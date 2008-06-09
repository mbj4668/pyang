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
    }
    """mapping of simple datatypes from YANG to W3C datatype library"""

    def __init__(self):
        """Initialize the instance.

        Subclasses should first call __init__ method from heir
        superclass and then redefine some of the items in the
        `self.handler` dictionary if necessary.
        """
        self.handler = {
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

    def translate(self, module, emit = ["a","dc","sch"]):
        """Translate `module` to DSDL schema(s).

        """
        self.module = module
        self.emit = emit
        self.imported_modules = {}
        self.imported_symbols = []
        self.dc_elements = {
            "source": ("YANG module '%s' (automatic translation)" %
                       self.module.name)
            }
        self.root_elem = ET.Element("grammar", self.grammar_attrs)
        for prefix in self.schema_languages: # define namespaces
            self.root_elem.attrib["xmlns:" + prefix] = \
                self.schema_languages[prefix]
        start = ET.SubElement(self.root_elem, "start")
        for sub in module.substmts: self.handle(sub, start)
        self.dublin_core()
        return ET.ElementTree(element=self.root_elem)
        
    def dublin_core(self):
        """
        Attach Dublin Core elements from dc_elements to <grammar>.
        """
        for dc in self.dc_elements:
            dcel = ET.Element("dc:" + dc)
            dcel.text = self.dc_elements[dc]
            self.root_elem.insert(0, dcel)

    def pull_def(self, prefix, stmt, ident):
        """
        Pull the definitions of `ident` from external module carrying
        `prefix` and install it as pattern definition.  Argument
        `stmt` should be either `typedef` or `grouping`.
        """
        ext_mod = self.module.ctx.modules[self.module.i_prefixes[prefix]]
        def_stmt = ext_mod.get_by_kw_and_arg(stmt, ident)
        self.handle(def_stmt, self.root_elem)

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
            handler(stmt, p_elem)

    # Handlers for YANG statements

    def noop(self, stmt, p_elem):
        pass

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
        if min_el == [] or int(min_el[1].arg) == 0:
            rng_card = "zeroOrMore"
        else:
            rng_card = "oneOrMore"
        cont = ET.SubElement(p_elem, rng_card)
        elem = ET.SubElement(cont, "element", name=stmt.arg)
        for sub in stmt.substmts: self.handle(sub, elem)

    def handle_description(self, stmt, p_elem):
        if stmt.i_module != self.module: return # ignore imported descriptions
        if stmt.parent == self.module: # top-level description
            self.dc_elements["description"] = stmt.arg
        else:
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
        elif ":" in stmt.arg:        # foreign type
            pr_t = stmt.arg.split(":")
            if stmt.arg not in self.imported_symbols:
                self.pull_def(pr_t[0], "typedef", pr_t[1])
            ET.SubElement(p_elem, "ref", name="__".join(pr_t))
        else:
            elem = ET.SubElement(p_elem, "data",
                                 type=self.datatype_map[stmt.arg])
        for sub in stmt.substmts: self.handle(sub, elem)

    def handle_reusable(self, stmt, p_elem):
        """Handle ``typedef`` or ``grouping``."""
        elem = ET.SubElement(self.root_elem, "define",
                             name=stmt.full_path("__"))
        for sub in stmt.substmts: self.handle(sub, elem)
        
    def handle_uses(self, stmt, p_elem):
        parent = stmt.parent
        while parent is not None:
            grp = parent.get_by_kw_and_arg("grouping", stmt.arg)
            if grp is not None:
                break
            parent = parent.parent
        ET.SubElement(p_elem, "ref",
                      name=grp.full_path("__"))

    def handle_enum(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "value")
        elem.text = stmt.arg
        for sub in stmt.substmts: self.handle(sub, elem)

    def handle_must(self, stmt, p_elem):
        pattern = ET.SubElement(p_elem, "sch:pattern")
        rule = ET.SubElement(pattern, "sch:rule",
                             context=p_elem.attrib["name"])
        assert_ = ET.SubElement(rule, "sch:assert",
                                test=stmt.arg.replace("$this", "."))
        err_msg = stmt.get_by_kw("error-message")
        if err_msg != []:
            assert_.text = err_msg[0].arg
