"""This module implements translator from YANG to DSDL.

"""

__docformat__ = "reStructuredText"

import sys
import xml.etree.ElementTree as ET

class DSDLTranslator(object):

    """Instances of this class translate YANG to DSDL.

    The `translate` method walks recursively down the tree of YANG
    statements and builds one or more resulting ElementTree(s)
    containing the corresponding schemas. For each YANG statement, a
    handler method for the statement's keyword is dispatched.

    Instance variables:
    
    * dc_elements: dictionary with Dublin core elements (tag -> text)
    * emit: list of prefixes that controls which schema languages
      will be generated.
    * handler: dictionary dispatching YANG statements to handler methods
    * imported_symbols: list of used external symbols
    * module: YANG module that is being translated
    * root_elem: root element in the main etree (with annotated RELAX NG)
    """

    grammar_attrs = {
        "xmlns" : "http://relaxng.org/ns/structure/1.0",
        "datatypeLibrary" : "http://www.w3.org/2001/XMLSchema-datatypes",
    }
    """Common attributes of the <grammar> element."""

    schema_languages = {
        "a": "http://relaxng.org/ns/compatibility/annotations/1.0",
        "dc": "http://purl.org/dc/terms",
        "sch": "http://purl.oclc.org/dsdl/schematron",
    }
    """Mapping of prefixes to schema language namespace URIs.

    The prefixes also used for controlling which schema languages are
    produced as output of the `translate` method.
    """

    datatype_map = {
        "string" : "string",
        "int8": "byte",
        "int16": "short",
        "int32": "int",
        "int64": "long",
        "uint8": "unsignedByte",
        "uint16": "unsignedShort",
        "uint32": "unsignedInt",
        "uint64": "unsignedLong",
        "float32": "float",
        "float64": "double",
        "boolean": "boolean",
        "binary": "base64Binary",
    }
    """mapping of simple datatypes from YANG to W3C datatype library"""

    datatree_nodes = ["container", "leaf", "leaf-list", "list", "choice"]
    """list of YANG statementes that form the data tree"""

    anyxml_def = '''<define name="anyxml"><zeroOrMore><choice>
        <attribute><anyName/></attribute>
        <element><anyName/><ref name="anyxml"/></element>
        <text/></choice></zeroOrMore></define>'''
    """RELAX NG pattern representing 'anyxml'"""

    def __init__(self):
        """Initialize the instance.

        Subclasses should first call __init__ method from heir
        superclass and then redefine some of the items in the
        `self.handler` dictionary if necessary.
        """
        self.handler = {
            "anyxml": self.handle_anyxml,
            "case": self.handle_case,
            "choice": self.handle_choice,
            "contact": self.handle_contact,
            "container": self.new_element,
            "description": self.handle_description,
            "enum" : self.handle_enum,
            "import" : self.noop,
            "grouping" : self.handle_reusable,
            "leaf": self.new_element,
            "leaf-list": self.new_list,
            "list": self.new_list,
            "must": self.handle_must,
            "namespace": self.handle_namespace,
            "organization": self.handle_organization,
            "pattern": self.handle_pattern,
            "prefix": self.noop,
            "revision": self.handle_revision,
            "type": self.handle_type,
            "typedef" : self.handle_reusable,
            "uses" : self.handle_uses,
        }

    def translate(self, module, emit = ["a","dc","sch"], debug=0):
        """Translate `module` to DSDL schema(s).
        """
        self.module = module
        self.emit = emit
        self.debug = debug
        self.prefix_map = {}
        self.imported_symbols = []
        self.first_anyxml = True
        self.dc_elements = {
            "source": ("YANG module '%s' (automatic translation)" %
                       self.module.name)
        }
        self.root_elem = ET.Element("grammar", self.grammar_attrs)
        for prefix in self.emit: # used namespaces
            self.root_elem.attrib["xmlns:" + prefix] = \
                self.schema_languages[prefix]
        # Library modules have no <start>
        if len(module.substmt_keywords().intersection(self.datatree_nodes)):
            start = ET.SubElement(self.root_elem, "start")
        else:
            start = self.root_elem
        for sub in module.substmts: self.handle(sub, start)
        self.dublin_core()
        return ET.ElementTree(element=self.root_elem)
        
    def dublin_core(self):
        """
        Attach Dublin Core elements from dc_elements to <grammar>.
        """
        if "dc" not in self.emit: return
        for dc in self.dc_elements:
            dcel = ET.Element("dc:" + dc)
            dcel.text = self.dc_elements[dc]
            self.root_elem.insert(0, dcel)

    def unique_def_name(self, stmt):
        """Answer disambiguated name of the receiver (typedef or grouping).
        """
        path = stmt.full_path()
        if stmt.i_module == self.module:
            return "__" + "__".join(path[1:])
        else:
            return "__".join(path)

    def resolve_ref(self, stmt, kw):
        """Resolve definition reference in `stmt`, return <ref> element.

        The `kw` argument is either ``typedef`` or ``grouping``.
        """
        ref = stmt.arg
        if ":" in ref:          # prefixed?
            prefix, ident = ref.split(":")
            if prefix == stmt.i_module.prefix.arg: # local prefix?
                ref = ident
            else:
                mod_name = stmt.i_module.i_prefixes[prefix]
                def_name =  mod_name + "__" + ident
                if def_name not in self.imported_symbols:
                    # pull the definition
                    ext_mod = stmt.i_module.ctx.modules[mod_name]
                    def_ = ext_mod.get_by_kw_and_arg(kw, ident)
                    self.handle(def_, self.root_elem)
                    self.imported_symbols.append(def_name)
                return ET.Element("ref", name=def_name)
        parent = stmt.parent
        while parent is not None:
            def_ = parent.get_by_kw_and_arg(kw, ref)
            if def_ is not None:
                break
            parent = parent.parent
        return ET.Element("ref", name=self.unique_def_name(def_))

    def handle(self, stmt, p_elem):
        """
        Run handler method for `stmt` in the context of `p_elem`.

        All handler methods have the same arguments.
        """
        try:
            handler = self.handler[stmt.keyword]
        except KeyError:
            sys.stderr.write("%s not handled\n" % stmt.keyword)
        else:
            if self.debug > 0:
                sys.stderr.write("Handling '%s %s'\n" %
                                 (stmt.keyword, stmt.arg))
            handler(stmt, p_elem)

    # Handlers for YANG statements

    def noop(self, stmt, p_elem):
        pass

    def handle_anyxml(self, stmt, p_elem):
        if self.first_anyxml:   # install definition
            def_ = ET.fromstring(self.anyxml_def)
            self.root_elem.append(def_)
            self.first_anyxml = False
        elem = ET.SubElement(p_elem, "element", name=stmt.arg)
        for sub in stmt.substmts: self.handle(sub, elem)
        ET.SubElement(elem, "ref", name="anyxml")

    def handle_contact(self, stmt, p_elem):
        self.dc_elements["contributor"] = stmt.arg

    def handle_organization(self, stmt, p_elem):
        self.dc_elements["creator"] = stmt.arg

    def handle_revision(self, stmt, p_elem):
        self.dc_elements["issued"] = stmt.arg
        
    def new_element(self, stmt, p_elem):
        """Handle ``leaf`` or ``container."""
        elem = ET.SubElement(p_elem, "element", name=stmt.arg)
        for sub in stmt.substmts: self.handle(sub, elem)

    def new_list(self, stmt, p_elem):
        """Handle ``leaf-list`` or ``list."""
        min_el = stmt.get_by_kw("min-elements")
        if min_el == [] or int(min_el[0].arg) == 0:
            rng_card = "zeroOrMore"
        else:
            rng_card = "oneOrMore"
        cont = ET.SubElement(p_elem, rng_card)
        elem = ET.SubElement(cont, "element", name=stmt.arg)
        for sub in stmt.substmts: self.handle(sub, elem)

    def handle_description(self, stmt, p_elem):
        if stmt.i_module != self.module: # ignore imported descriptions
            return
        if stmt.parent == self.module: # top-level description
            self.dc_elements["description"] = stmt.arg
        elif "a" in self.emit and stmt.parent.keyword != "enum":
            elem = ET.Element("a:documentation")
            p_elem.insert(0, elem)
            elem.text = stmt.arg

    def handle_namespace(self, stmt, p_elem):
        self.root_elem.attrib["ns"] = stmt.arg

    def handle_pattern(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "param", name="pattern")
        elem.text = stmt.arg
        for sub in stmt.substmts: self.handle(sub, elem)

    def handle_type(self, stmt, p_elem):
        if stmt.arg in ("enumeration", "union"):
            elem = ET.SubElement(p_elem, "choice")
        elif stmt.arg == "empty":
            ET.SubElement(p_elem, "empty")
        elif stmt.arg in self.datatype_map:
            elem = ET.SubElement(p_elem, "data",
                                 type=self.datatype_map[stmt.arg])
        else:                   # derived type
            p_elem.append(self.resolve_ref(stmt, "typedef"))
        for sub in stmt.substmts: self.handle(sub, elem)

    def handle_reusable(self, stmt, p_elem):
        """Handle ``typedef`` or ``grouping``."""
        elem = ET.SubElement(self.root_elem, "define",
                             name=self.unique_def_name(stmt))
        for sub in stmt.substmts: self.handle(sub, elem)
        
    def handle_uses(self, stmt, p_elem):
        p_elem.append(self.resolve_ref(stmt, "grouping"))
        for sub in stmt.substmts: self.handle(sub, elem)

    def handle_enum(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "value")
        elem.text = stmt.arg
        if "a" in self.emit:    # special handling of description
            desc = stmt.get_by_kw("description")
            if len(desc) > 0:
                docel = ET.SubElement(p_elem, "a:documentation")
                docel.text = desc[0].arg

    def handle_must(self, stmt, p_elem):
        pattern = ET.SubElement(p_elem, "sch:pattern")
        rule = ET.SubElement(pattern, "sch:rule",
                             context=p_elem.attrib["name"])
        assert_ = ET.SubElement(rule, "sch:assert",
                                test=stmt.arg.replace("$this", "."))
        err_msg = stmt.get_by_kw("error-message")
        if err_msg != []:
            assert_.text = err_msg[0].arg

    def handle_choice(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "choice")
        for sub in stmt.substmts: self.handle(sub, elem)

    def handle_case(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "group")
        for sub in stmt.substmts: self.handle(sub, elem)
