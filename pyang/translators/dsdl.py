"""This module implements translator from YANG to DSDL.

"""

__docformat__ = "reStructuredText"

import sys
import optparse
import xml.etree.ElementTree as ET

from pyang import plugin
from pyang import statements

def pyang_plugin_init():
    plugin.register_plugin(DSDLPlugin())

class DSDLPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        fmts['dsdl'] = self
    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--dsdl-no-annotations",
                                 dest="dsdl_no_annotations",
                                 action="store_true",
                                 help="Do not print documentation annotations"),
            optparse.make_option("--dsdl-no-dublin-core",
                                 dest="dsdl_no_dublin_core",
                                 action="store_true",
                                 help="Do not print Dublin Core elements"),
            optparse.make_option("--dsdl-no-schematron",
                                 dest="dsdl_no_schematron",
                                 action="store_true",
                                 help="Do not print Schematron rules"),
            optparse.make_option("--dsdl-no-dsrl",
                                 dest="dsdl_no_dsrl",
                                 action="store_true",
                                 help="Do not print DSRL elements"),
            optparse.make_option("--dsdl-no-netmod",
                                 dest="dsdl_no_netmod",
                                 action="store_true",
                                 help="Do not print NETMOD attributes"),
            ]
        g = optparser.add_option_group("DSDL output specific options")
        g.add_options(optlist)
    def emit(self, ctx, module, fd):
        emit_dsdl(ctx, module, fd)

def emit_dsdl(ctx, module, fd):
    emit = []
    if ctx.opts.dsdl_no_schematron != True:
        emit.append("sch")
    if ctx.opts.dsdl_no_dublin_core != True:
        emit.append("dc")
    if ctx.opts.dsdl_no_annotations != True:
        emit.append("a")
    if ctx.opts.dsdl_no_dsrl != True:
        emit.append("dsrl")
    if ctx.opts.dsdl_no_netmod != True:
        emit.append("nm")
    etree = DSDLTranslator().translate(module, emit, debug=0)
    etree.write(fd, "UTF-8")


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
        "dsrl": "http://purl.oclc.org/dsdl/dsrl",
        "nm": "urn:ietf:params:xml:ns:netmod:dsdl-attrib:1",
        "sch": "http://purl.oclc.org/dsdl/schematron",
    }
    """Mapping of prefixes to schema language namespace URIs.

    The prefixes also used for controlling which schema languages are
    produced as output of the `translate` method.
    """

    datatype_map = {
        "instance-identifier": "string",
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

    datatree_nodes = ["container", "leaf", "leaf-list", "list",
                      "choice", "anyxml"]
    """list of YANG statementes that form the data tree"""

    anyxml_def = '''<define name="anyxml"><zeroOrMore><choice>
        <attribute><anyName/></attribute>
        <element><anyName/><ref name="anyxml"/></element>
        <text/></choice></zeroOrMore></define>'''
    """RELAX NG pattern representing 'anyxml'"""

    def decode_ranges(range_expr):
        """Parse `range_expr` and return list of (lo,hi) tuples.

        For range-part with a single component, hi is not present.
        """
        return [ tuple(r.split("..")) for r in range_expr.split("|") ]
    decode_ranges = staticmethod(decode_ranges)

    def __init__(self):
        """Initialize the instance.

        Subclasses should first call __init__ method from heir
        superclass and then redefine some of the items in the
        `self.stmt_handler` dictionary if necessary.
        """
        self.stmt_handler = {
            "anyxml": self.anyxml_stmt,
            "belongs-to": self.belongs_to_stmt,
            "case": self.case_stmt,
            "choice": self.choice_stmt,
            "config": self.config_stmt,
            "contact": self.contact_stmt,
            "container": self.container_stmt,
            "default": self.default_stmt,
            "description": self.description_stmt,
            "enum" : self.enum_stmt,
            "import" : self.noop,
            "include" : self.include_stmt,
            "grouping" : self.handle_reusable,
            "key": self.key_stmt,
            "leaf": self.leaf_stmt,
            "leaf-list": self.handle_list,
            "list": self.handle_list,
            "mandatory": self.noop,
            "must": self.must_stmt,
            "namespace": self.namespace_stmt,
            "organization": self.organization_stmt,
            "pattern": self.pattern_stmt,
            "prefix": self.noop,
            "reference": self.reference_stmt,
            "revision": self.revision_stmt,
            "type": self.type_stmt,
            "typedef" : self.handle_reusable,
            "unique" : self.unique_stmt,
            "uses" : self.uses_stmt,
        }
        self.type_handler = {
            "boolean": self.mapped_type,
            "binary": self.mapped_type,
            "bits": self.bits_type,
            "empty": self.mapped_type,
            "enumeration": self.choice_type,
            "float32": self.numeric_type,
            "float64": self.numeric_type,
            "instance-identifier": self.mapped_type,
            "int8": self.numeric_type,
            "int16": self.numeric_type,
            "int32": self.numeric_type,
            "int64": self.numeric_type,
            "keyref": self.keyref_type,
            "string" : self.string_type,
            "uint8": self.numeric_type,
            "uint16": self.numeric_type,
            "uint32": self.numeric_type,
            "uint64": self.numeric_type,
            "uint64": self.choice_type,
            "union": self.choice_type,
        }

    def translate(self, module, emit=schema_languages.keys(), debug=0):
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
        for sub in module.substmts: self.handle_stmt(sub, start)
        self.dublin_core()
        return ET.ElementTree(element=self.root_elem)
        
    def dublin_core(self):
        """
        Attach Dublin Core elements from dc_elements to <grammar>.
        """
        if "dc" in self.emit:
            for dc in self.dc_elements:
                dcel = ET.Element("dc:" + dc)
                dcel.text = self.dc_elements[dc]
                self.root_elem.insert(0, dcel)

    def schematron_assert(self, elem, cond, err_msg=None):
        """Install <sch:assert> under `elem`.
        """
        if "sch" in self.emit:
            assert_ = ET.SubElement(elem, "sch:assert", test=cond)
            if err_msg is not None:
                assert_.text = err_msg

    def nm_attribute(self, elem, attr, value):
        """Attach NETMOD attribute `attr` with `value` to `elem`.
        """
        if "nm" in self.emit:
            elem.attrib["nm:" + attr] = value
        
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
                    def_, = ext_mod.search(keyword=kw, arg=ident)
                    self.handle_stmt(def_, self.root_elem)
                    self.imported_symbols.append(def_name)
                return ET.Element("ref", name=def_name)
        parent = stmt.parent
        while parent is not None:
            deflist = parent.search(keyword=kw, arg=ref)
            if len(deflist) > 0:
                break
            parent = parent.parent
        return ET.Element("ref", name=self.unique_def_name(deflist[0]))

    def handle_stmt(self, stmt, p_elem):
        """
        Run handler method for `stmt` in the context of `p_elem`.

        All handler methods have the same arguments.
        """
        try:
            handler = self.stmt_handler[stmt.keyword]
        except KeyError:
            if self.debug > 0:
                sys.stderr.write("%s not handled\n" % \
                                     statements.keyword_to_str(stmt.keyword))
        else:
            if self.debug > 0:
                sys.stderr.write("Handling '%s %s'\n" %
                                 (statements.keyword_to_str(stmt.keyword),
                                  stmt.arg))
            handler(stmt, p_elem)

    # Handlers for YANG statements

    def noop(self, stmt, p_elem):
        pass

    def anyxml_stmt(self, stmt, p_elem):
        if self.first_anyxml:   # install definition
            def_ = ET.fromstring(self.anyxml_def)
            self.root_elem.append(def_)
            self.first_anyxml = False
        elem = ET.SubElement(p_elem, "element", name=stmt.arg)
        for sub in stmt.substmts: self.handle_stmt(sub, elem)
        ET.SubElement(elem, "ref", name="anyxml")

    def config_stmt(self, stmt, p_elem):
        self.nm_attribute(p_elem, "config", stmt.arg)

    def contact_stmt(self, stmt, p_elem):
        self.dc_elements["contributor"] = stmt.arg

    def container_stmt(self, stmt, p_elem):
        if stmt.is_optional():
            p_elem = ET.SubElement(p_elem, "optional")
        elem = ET.SubElement(p_elem, "element", name=stmt.arg)
        for sub in stmt.substmts: self.handle_stmt(sub, elem)

    def default_stmt(self, stmt, p_elem):
        if "dsrl" in self.emit:
            delem = ET.SubElement(p_elem, "dsrl:default-content")
            delem.text = stmt.arg

    def include_stmt(self, stmt, p_elem):
        delem = ET.SubElement(p_elem, "include", href = stmt.arg + ".rng")

    def key_stmt(self, stmt, p_elem):
        self.nm_attribute(p_elem, "key", stmt.arg)

    def leaf_stmt(self, stmt, p_elem):
        if len(stmt.search(keyword="mandatory", arg="true")) == 0:
            p_elem = ET.SubElement(p_elem, "optional")
        elem = ET.SubElement(p_elem, "element", name=stmt.arg)
        for sub in stmt.substmts: self.handle_stmt(sub, elem)

    def organization_stmt(self, stmt, p_elem):
        self.dc_elements["creator"] = stmt.arg

    def revision_stmt(self, stmt, p_elem):
        self.dc_elements["issued"] = stmt.arg
        
    def belongs_to_stmt(self, stmt, p_elem):
        self.dc_elements["isPartOf"] = stmt.arg
        
    def handle_list(self, stmt, p_elem):
        """Handle leaf-list or list."""
        min_el = stmt.search(keyword="min-elements")
        if len(min_el) == 0 or int(min_el[0].arg) == 0:
            rng_card = "zeroOrMore"
        else:
            rng_card = "oneOrMore"
        cont = ET.SubElement(p_elem, rng_card)
        if rng_card == "oneOrMore":
            self.nm_attribute(cont, "min-elements", min_el[0].arg)
        max_el = stmt.search(keyword="max-elements")
        if len(max_el) > 0:
            self.nm_attribute(cont, "max-elements", max_el[0].arg)
        ordby = stmt.search("ordered-by")
        if len(ordby) > 0:
            self.nm_attribute(cont, "ordered-by", ordby[0].arg)
        elem = ET.SubElement(cont, "element", name=stmt.arg)
        for sub in stmt.substmts: self.handle_stmt(sub, elem)

    def description_stmt(self, stmt, p_elem):
        if stmt.i_module != self.module: # ignore imported descriptions
            return
        if stmt.parent == self.module: # top-level description
            self.dc_elements["description"] = stmt.arg
        elif "a" in self.emit and stmt.parent.keyword != "enum":
            elem = ET.Element("a:documentation")
            p_elem.insert(0, elem)
            elem.text = stmt.arg

    def namespace_stmt(self, stmt, p_elem):
        self.root_elem.attrib["ns"] = stmt.arg

    def pattern_stmt(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "param", name="pattern")
        elem.text = stmt.arg
        for sub in stmt.substmts: self.handle_stmt(sub, elem)

    def reference_stmt(self, stmt, p_elem):
        if "a" not in self.emit: return
        elem = ET.Element("a:documentation")
        elem.text = "See: " + stmt.arg
        i = 0
        # insert after description
        for ch in p_elem:
            if ch.tag == "a:documentation":
                i += 1
                continue
        p_elem.insert(i, elem)

    def type_stmt(self, stmt, p_elem):
        if stmt.arg == "empty":
            ET.SubElement(p_elem, "empty")
            return
        try:
            thandler = self.type_handler[stmt.arg]
        except KeyError:                   # derived type
            p_elem.append(self.resolve_ref(stmt, "typedef"))
        else:
            thandler(stmt, p_elem)

    def handle_reusable(self, stmt, p_elem):
        """Handle ``typedef`` or ``grouping``."""
        elem = ET.SubElement(self.root_elem, "define",
                             name=self.unique_def_name(stmt))
        for sub in stmt.substmts: self.handle_stmt(sub, elem)
        
    def uses_stmt(self, stmt, p_elem):
        p_elem.append(self.resolve_ref(stmt, "grouping"))

    def enum_stmt(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "value")
        elem.text = stmt.arg
        if "a" in self.emit:    # special handling of description
            desc = stmt.search(keyword="description")
            if len(desc) > 0:
                docel = ET.SubElement(p_elem, "a:documentation")
                docel.text = desc[0].arg

    def must_stmt(self, stmt, p_elem):
        estmt = stmt.search(keyword="error-message")
        if len(estmt) > 0:
            err_msg = estmt[0].arg
        else:
            err_msg = None
        self.schematron_assert(p_elem, stmt.arg.replace("$this", "."),
                               err_msg)

    def choice_stmt(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "choice")
        for sub in stmt.substmts: self.handle_stmt(sub, elem)

    def case_stmt(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "group")
        for sub in stmt.substmts: self.handle_stmt(sub, elem)

    def unique_stmt(self, stmt, p_elem):
        leafs = stmt.arg.split()
        clist = [ "%s != current()/%s" % (l,l) for l in leafs ]
        cond = "preceding-sibling::%s[%s]" % (p_elem.attrib["name"],
                                              " or ".join(clist))
        err_msg = 'Not unique: "%s"' % stmt.arg
        self.schematron_assert(p_elem, cond, err_msg)

    # Handlers for YANG types

    def choice_type(self, stmt, p_elem):
        """Handle enumeration and union types."""
        elem = ET.SubElement(p_elem, "choice")
        for sub in stmt.substmts: self.handle_stmt(sub, elem)

    def mapped_type(self, stmt, p_elem):
        """Handle types that are simply mapped to RELAX NG.
        
        `DSDLTranslator.datatype_map` maps the type names.
        """
        ET.SubElement(p_elem, "data", type=self.datatype_map[stmt.arg])

    def numeric_type(self, stmt, p_elem):
        """Handle numeric types."""
        rngtype = self.datatype_map[stmt.arg]
        rstmt = stmt.search(keyword="range")
        if len(rstmt) == 0:
            ET.SubElement(p_elem, "data", type=rngtype)
            return
        ranges = self.decode_ranges(rstmt[0].arg)
        if len(ranges) > 1:
            p_elem = ET.SubElement(p_elem, "choice")
            for sub in rstmt[0].substmts: self.handle_stmt(sub, p_elem)
        for rc in ranges:
            elem = ET.SubElement(p_elem, "data", type=rngtype)
            if len(ranges) == 1:
                for sub in rstmt[0].substmts: self.handle_stmt(sub, elem)
            if rc[0] not in ("min", "-INF"):
                lelem = ET.SubElement(elem, "param", name="minInclusive")
                lelem.text = rc[0]
            if len(rc) == 1 or rc[1] not in ("max","INF"):
                helem = ET.SubElement(elem, "param", name="maxInclusive")
                if len(rc) == 1:
                    helem.text = rc[0]
                else:
                    helem.text = rc[1]

    def bits_type(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "list")
        for bit in stmt.search(keyword="bit"):
            optel = ET.SubElement(p_elem, "optional")
            velem = ET.SubElement(optel, "value")
            velem.text = bit.arg

    def keyref_type(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "data", type="string")
        pel, = stmt.search(keyword="path")
        err_msg = """Missing key '<value-of select="."/>'"""
        self.schematron_assert(p_elem, pel.arg +"[current()=.]", err_msg)

    def string_type(self, stmt, p_elem):
        pstmt = stmt.search(keyword="pattern")
        if len(pstmt) > 0:
            pe = ET.Element("param", name="pattern")
            pe.text = pstmt[0].arg
            for sub in pstmt[0].substmts: self.handle_stmt(sub, pe)
        else:
            pe = None
        rstmt = stmt.search(keyword="length")
        if len(rstmt) == 0:
            elem = ET.SubElement(p_elem, "data", type="string")
            if pe is not None: elem.append(pe) 
            return
        ranges = self.decode_ranges(rstmt[0].arg)
        if len(ranges) > 1:
            p_elem = ET.SubElement(p_elem, "choice")
            for sub in rstmt[0].substmts: self.handle_stmt(sub, p_elem)
        for rc in ranges:
            elem = ET.SubElement(p_elem, "data", type="string")
            if pe is not None: elem.append(pe)
            if len(ranges) == 1:
                for sub in rstmt[0].substmts: self.handle_stmt(sub, elem)
            if len(rc) == 1:
                lelem = ET.SubElement(p_elem, "param", name="length")
                lelem.text = rc[0]
                return
            if rc[0] != "min":
                lelem = ET.SubElement(elem, "param", name="minLength")
                lelem.text = rc[0]
            if rc[1] != "max":
                helem = ET.SubElement(elem, "param", name="maxLength")
                helem.text = rc[1]
