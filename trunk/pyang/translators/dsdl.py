# Copyright (c) 2008 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>
#                       Martin Bjorklund <mbj@tail-f.com>
#
# Translator of YANG to DSDL schemas with additional annotations
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
# 
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""This module implements translator from YANG to DSDL & annotations.

It is designed as a plugin for the pyang program and defines several
new command-line options:

--dsdl-no-annotations
    No output of DTD compatibility annotations

--dsdl-no-dublin-core
    No output of Dublin Core annotations

--dsdl-no-schematron
    No output of Schematron rules

-dsdl-no-dsrl
    No output of DSRL annotations (default-content)

-dsdl-no-netmod
    No output of NETMOD-specific attributes

Two classes are defined in this module:

* `DSDLPlugin`: pyang plugin interface class

* `DSDLTranslator`: its instance preforms the translation
"""

__docformat__ = "reStructuredText"

import sys
import optparse
try:
    import xml.etree.ElementTree as ET
except ImportError:
    pass

from pyang import plugin, statements

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
                                 help="No output of DTD compatibility"
                                 " annotations"),
            optparse.make_option("--dsdl-no-dublin-core",
                                 dest="dsdl_no_dublin_core",
                                 action="store_true",
                                 help="No output of Dublin Core"
                                 " annotations"),
            optparse.make_option("--dsdl-no-schematron",
                                 dest="dsdl_no_schematron",
                                 action="store_true",
                                 help="No output of Schematron rules"),
            optparse.make_option("--dsdl-no-dsrl",
                                 dest="dsdl_no_dsrl",
                                 action="store_true",
                                 help="No output of DSRL annotations"
                                 " (default-content)"),
            optparse.make_option("--dsdl-no-netmod",
                                 dest="dsdl_no_netmod",
                                 action="store_true",
                                 help="No output of NETMOD-specific"
                                 " attributes"),
            ]
        g = optparser.add_option_group("DSDL output specific options")
        g.add_options(optlist)
    def emit(self, ctx, module, fd):
        try:
            import xml.etree.ElementTree as ET
        except ImportError:
            print >> sys.stderr, ("DSDL translation needs the python module "
                                  "etree, available in python 2.5")
            sys.exit(1)

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

    """Instances of this class translate YANG to DSDL + annotations.

    The `translate` method walks recursively down the tree of YANG
    statements and builds one or more resulting ElementTree(s)
    containing the corresponding schemas. For each YANG statement, a
    callback method for the statement's keyword is dispatched.

    Instance variables:
    
    * `dc_elements`: dictionary with Dublin core elements (tag -> text)
    * `debug`: integer controlling level of debug messages
    * `emit`: list of prefixes (keys in `schema_languages` dictionary)
      controlling which annotations will be generated.
    * `first_anyxml`: boolean indicating first occurence of ``anyxml``
      statement (so that `anyxml_def` has to be inserted)
    * `imported_symbols`: list of used external symbols whose definition
      has already been imported 
    * `module`: YANG module that is being translated
    * `root_elem`: <grammar> ETree Element, which is the root of the
      resulting RELAX NG ETree
    * `stmt_handler`: dictionary dispatching callback methods for
      handling YANG statements (keyword -> method)
    * `type_handler`: dictionary dispatching callback methods for
      YANG built-in types (type -> method)

    Class variables are: `anyxml_def`, `datatree_nodes`, `datatype_map`,
    `grammar_attrs`, `schema_languages`.

    One static method is defined: `decode_ranges`.
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
    """Mapping of prefixes to schema language namespace URIs."""

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
    """Mapping of simple datatypes from YANG to W3C datatype library"""

    datatree_nodes = ["container", "leaf", "leaf-list", "list",
                      "choice", "anyxml", "uses"]
    """List of YANG statementes that form the data tree"""

    anyxml_def = '''<define name="__anyxml__"><zeroOrMore><choice>
        <attribute><anyName/></attribute>
        <element><anyName/><ref name="__anyxml__"/></element>
        <text/></choice></zeroOrMore></define>'''
    """RELAX NG pattern representing 'anyxml'"""

    def decode_ranges(range_expr):
        """Parse `range_expr` and return list of [lo,hi] pairs.

        Argument `range_expr` is either range-expr or length-expr.
        For range-part with a single component, hi is not present.
        If range-part is a single ``min`` or ``max``, it is omitted.
        """
        raw = range_expr.split("|")
        res = []
        for part in raw:
            strp = [x.strip() for x in part.split("..")]
            if len(strp) > 1 or strp[0] not in ("min", "max"):
                res.append(strp)
        return res
    decode_ranges = staticmethod(decode_ranges)

    def __init__(self):
        """Initialize the statement and type dispatchers.

        The same instance may be used for translating multiple YANG
        modules since all instance variables are initialized by the
        `translate` method.

        To change the behaviour of the translator, make a subclass and
        replace appropriate callback methods in the `stmt_handler`
        and/or `type_handler` dictionaries.
        """
        self.stmt_handler = {
            "anyxml": self.anyxml_stmt,
            "belongs-to": self.belongs_to_stmt,
            "case": self.case_stmt,
            "choice": self.choice_stmt,
            "config": self.attach_nm_att,
            "contact": self.contact_stmt,
            "container": self.container_stmt,
            "default": self.default_stmt,
            "description": self.description_stmt,
            "enum" : self.enum_stmt,
            "import" : self.noop,
            "include" : self.include_stmt,
            "grouping" : self.handle_reusable,
            "key": self.attach_nm_att,
            "leaf": self.leaf_stmt,
            "leaf-list": self.handle_list,
            "list": self.handle_list,
            "mandatory": self.noop,
            "must": self.must_stmt,
            "namespace": self.noop,
            "organization": self.organization_stmt,
            "prefix": self.noop,
            "reference": self.reference_stmt,
            "revision": self.revision_stmt,
            "status" : self.attach_nm_att,
            "type": self.type_stmt,
            "typedef" : self.handle_reusable,
            "unique" : self.unique_stmt,
            "units" : self.attach_nm_att,
            "uses" : self.uses_stmt,
        }
        self.type_handler = {
            "boolean": self.mapped_type,
            "binary": self.mapped_type,
            "bits": self.bits_type,
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
            "union": self.choice_type,
        }

    def translate(self, module, emit=schema_languages.keys(), debug=0):
        """Translate `module` to RELAX NG schema with annotations.

        The `emit` argument controls output of individual annotations
        (by default, all are present). The `debug` argument controls
        level of debug messages - 0 (default) supresses them.  
        """
        self.module = module
        self.emit = emit
        self.debug = debug
        self.imported_symbols = []
        self.namespace = module.search(keyword="namespace")[0].arg
        self.prefix = module.search(keyword="prefix")[0].arg
        self.first_anyxml = True
        self.dc_elements = {
            "source": ("YANG module '%s' (automatic translation)" %
                       self.module.arg)
        }
        self.root_elem = ET.Element("grammar", self.grammar_attrs)
        for prefix in self.emit: # used namespaces
            self.root_elem.attrib["xmlns:" + prefix] = \
                self.schema_languages[prefix]
        self.root_elem.attrib["xmlns:" + self.prefix] = self.namespace
        self.root_elem.attrib["ns"] = self.namespace
        # Write <start> if there are data tree nodes
        dt_nodes = 0
        for dtn in self.datatree_nodes:
            dt_nodes += len(module.search(keyword=dtn))
        if dt_nodes > 0:
            topel = ET.SubElement(self.root_elem, "start")
            if dt_nodes > 1: # Non-unique root element
                topel = ET.SubElement(topel, "group")
        else:
            topel = self.root_elem
        for sub in module.substmts: self.handle_stmt(sub, topel)
        self.dublin_core()
        return ET.ElementTree(element=self.root_elem)
        
    def dublin_core(self):
        """
        Attach Dublin Core elements from `dc_elements` to `root_elem`.
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
        
    def add_prefix(self, nodeid):
        """Prepend `self.prefix` to all parts of `nodeid`.

        Argument `nodeid` is a descendant schema identifier.
        """
        parts = [ "%s:%s" % (self.prefix,p) for p in nodeid.split("/")]
        return "/".join(parts)

    def unique_def_name(self, stmt):
        """Answer mangled name of the receiver (typedef or grouping).

        Identifiers of all ancestor nodes are prepended, separated by
        ``__``. Moreover, symbols from foreign modules start with
        their module name (local names thus start with ``__``).
        """
        path = stmt.full_path()
        if stmt.i_module == self.module:
            return "__".join(path[1:])
        else:
            return "__".join(path)

    def resolve_ref(self, stmt, kw):
        """Resolve definition reference in `stmt`, return <ref> element.

        The method returns an ETree Element <ref name="mangled_name"/>. 
        As a side effect, all used foreign definitions are copied to
        the resulting schema.

        The `kw` argument must be either ``typedef`` or ``grouping``.
        """
        primary = (self.module == stmt.i_module) # ref in main module?
        ref = stmt.arg
        same = True
        if ":" in ref:          # prefixed?
            prefix, ref = ref.split(":")
            same = (prefix == stmt.i_module.i_prefix)
        if same:
            parent = stmt.parent
            while parent is not None:
                deflist = parent.search(keyword=kw, arg=ref)
                parent = parent.parent
                if len(deflist) > 0: break
            def_ = deflist[0]
            if not primary and parent is None: # top-level external def?
                def_name = stmt.i_module.arg + "__" + ref
                if def_name not in self.imported_symbols:
                    self.handle_stmt(def_, self.root_elem)
                    self.imported_symbols.append(def_name)
            return ET.Element("ref", name=self.unique_def_name(def_))
        mod_name = stmt.i_module.i_prefixes[prefix]
        def_name =  mod_name + "__" + ref
        if def_name not in self.imported_symbols:
            # pull the definition
            ext_mod = stmt.i_module.i_ctx.modules[mod_name]
            def_, = ext_mod.search(keyword=kw, arg=ref)
            self.handle_stmt(def_, self.root_elem)
            self.imported_symbols.append(def_name)
        return ET.Element("ref", name=def_name)

    def handle_stmt(self, stmt, p_elem):
        """
        Run handler method for `stmt` in the context of `p_elem`.

        All handler methods are defined below and have the same
        arguments. They should create the schema fragment
        corresponding to `stmt`, insert it under `p_elem` and perform
        all side effects as necessary.
        """
        try:
            handler = self.stmt_handler[stmt.keyword]
        except KeyError:
            if self.debug > 0:
                sys.stderr.write("%s not handled\n" %
                                 util.keyword_to_str(stmt.raw_keyword))
        else:
            if self.debug > 0:
                sys.stderr.write("Handling '%s %s'\n" %
                                 (util.keyword_to_str(stmt.raw_keyword),
                                  stmt.arg))
            handler(stmt, p_elem)

    # Handlers for YANG statements

    def anyxml_stmt(self, stmt, p_elem):
        if self.first_anyxml:
            # install definition
            def_ = ET.fromstring(self.anyxml_def)
            self.root_elem.append(def_)
            self.first_anyxml = False
        elem = ET.SubElement(p_elem, "element", name=stmt.arg)
        for sub in stmt.substmts: self.handle_stmt(sub, elem)
        ET.SubElement(elem, "ref", name="__anyxml__")

    def attach_nm_att(self, stmt, p_elem):
        """Handle ``config``, ``key``, ``status``, ``units``."""
        self.nm_attribute(p_elem, stmt.keyword, stmt.arg)

    def belongs_to_stmt(self, stmt, p_elem):
        self.dc_elements["isPartOf"] = stmt.arg
        
    def case_stmt(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "group")
        for sub in stmt.substmts: self.handle_stmt(sub, elem)

    def choice_stmt(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "choice")
        for sub in stmt.substmts: self.handle_stmt(sub, elem)

    def contact_stmt(self, stmt, p_elem):
        self.dc_elements["contributor"] = stmt.arg

    def container_stmt(self, stmt, p_elem):
        if stmt.is_optional():
            p_elem = ET.SubElement(p_elem, "optional")
        elem = ET.SubElement(p_elem, "element", name=stmt.arg)
        substmts = stmt.substmts
        if len(substmts) == 0:
            ET.SubElement(elem, "empty")
        else:
            for sub in substmts: self.handle_stmt(sub, elem)

    def default_stmt(self, stmt, p_elem):
        if "dsrl" in self.emit:
            delem = ET.SubElement(p_elem, "dsrl:default-content")
            delem.text = stmt.arg

    def description_stmt(self, stmt, p_elem):
        if stmt.i_module != self.module: # ignore imported descriptions
            return
        if stmt.parent == self.module: # top-level description
            self.dc_elements["description"] = stmt.arg
        elif "a" in self.emit and stmt.parent.keyword != "enum":
            elem = ET.Element("a:documentation")
            p_elem.insert(0, elem)
            elem.text = stmt.arg

    def enum_stmt(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "value")
        elem.text = stmt.arg
        for sub in stmt.search(keyword="status"):
            self.handle_stmt(sub, elem)

    def handle_list(self, stmt, p_elem):
        """Handle ``leaf-list`` or ``list``."""
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

    def handle_reusable(self, stmt, p_elem):
        """Handle ``typedef`` or ``grouping``."""
        elem = ET.SubElement(self.root_elem, "define",
                             name=self.unique_def_name(stmt))
        for sub in stmt.substmts: self.handle_stmt(sub, elem)
        
    def include_stmt(self, stmt, p_elem):
        delem = ET.SubElement(p_elem, "include", href = stmt.arg + ".rng")

    def leaf_stmt(self, stmt, p_elem):
        if (len(stmt.search(keyword="mandatory", arg="true")) == 0 and
            (stmt.parent.keyword != "list" or
            stmt.arg not in stmt.parent.search(keyword="key")[0].arg)):
            p_elem = ET.SubElement(p_elem, "optional")
        elem = ET.SubElement(p_elem, "element", name=stmt.arg)
        for sub in stmt.substmts: self.handle_stmt(sub, elem)

    def must_stmt(self, stmt, p_elem):
        estmt = stmt.search(keyword="error-message")
        if len(estmt) > 0:
            err_msg = estmt[0].arg
        else:
            err_msg = None
        self.schematron_assert(p_elem, stmt.arg.replace("$this", "current()"),
                               err_msg)

    def noop(self, stmt, p_elem):
        pass

    def organization_stmt(self, stmt, p_elem):
        self.dc_elements["creator"] = stmt.arg

    def reference_stmt(self, stmt, p_elem):
        if stmt.i_module != self.module: # ignore imported descriptions
            return
        if stmt.parent == self.module: # top-level description
            self.dc_elements["BibliographicResource"] = stmt.arg
        if "a" in self.emit and stmt.parent.keyword != "enum":
            elem = ET.Element("a:documentation")
            elem.text = "See: " + stmt.arg
            i = 0
            # insert after description
            for ch in p_elem:
                if ch.tag == "a:documentation":
                    i += 1
                else:
                    break
            p_elem.insert(i, elem)

    def revision_stmt(self, stmt, p_elem):
        self.dc_elements["issued"] = stmt.arg
        
    def type_stmt(self, stmt, p_elem):
        """Handle ``type`` statement.

        All types except ``empty`` are handled by a specific type
        callback method defined below. Derived types are recognized by
        raising the KeyError.
        """
        if stmt.arg == "empty":
            ET.SubElement(p_elem, "empty")
            return
        try:
            thandler = self.type_handler[stmt.arg]
        except KeyError:
            p_elem.append(self.resolve_ref(stmt, "typedef"))
        else:
            thandler(stmt, p_elem)

    def unique_stmt(self, stmt, p_elem):
        leafs = stmt.arg.split()
        clist = [ "%s != current()/%s" % ((self.add_prefix(l),) * 2)
                  for l in leafs ]
        cond = ("preceding-sibling::%s:%s[%s]" %
                (self.prefix, p_elem.attrib["name"], " or ".join(clist)))
        err_msg = 'Not unique: "%s"' % stmt.arg
        self.schematron_assert(p_elem, cond, err_msg)

    def uses_stmt(self, stmt, p_elem):
        p_elem.append(self.resolve_ref(stmt, "grouping"))

    # Handlers for YANG types

    def bits_type(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "list")
        for bit in stmt.search(keyword="bit"):
            optel = ET.SubElement(elem, "optional")
            velem = ET.SubElement(optel, "value")
            velem.text = bit.arg

    def choice_type(self, stmt, p_elem):
        """Handle ``enumeration`` and ``union`` types."""
        elem = ET.SubElement(p_elem, "choice")
        for sub in stmt.substmts: self.handle_stmt(sub, elem)

    def keyref_type(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "data", type="string")
        pel, = stmt.search(keyword="path")
        err_msg = """Missing key '<value-of select="."/>'"""
        self.schematron_assert(p_elem, pel.arg +"[current()=.]", err_msg)

    def mapped_type(self, stmt, p_elem):
        """Handle types that are simply mapped to RELAX NG.
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
        if len(ranges) == 0: # isolated "max" or "min"
            ET.SubElement(p_elem, "data", type=rngtype)
            return
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

    def string_type(self, stmt, p_elem):
        pstmt = stmt.search(keyword="pattern")
        pels = []
        for pat in pstmt:
            pe = ET.Element("param", name="pattern")
            pe.text = pat.arg
            pels.append(pe)
            for sub in pat.substmts: self.handle_stmt(sub, pe)
        rstmt = stmt.search(keyword="length")
        if len(rstmt) == 0:
            elem = ET.SubElement(p_elem, "data", type="string")
            for pe in pels: elem.append(pe) 
            return
        ranges = self.decode_ranges(rstmt[0].arg)
        if len(ranges) == 0: # isolated "max" or "min"
            elem = ET.SubElement(p_elem, "data", type="string")
            for pe in pels: elem.append(pe) 
            return
        if len(ranges) > 1:
            p_elem = ET.SubElement(p_elem, "choice")
            for sub in rstmt[0].substmts: self.handle_stmt(sub, p_elem)
        for rc in ranges:
            elem = ET.SubElement(p_elem, "data", type="string")
            for pe in pels: elem.append(pe)
            if len(ranges) == 1:
                for sub in rstmt[0].substmts: self.handle_stmt(sub, elem)
            if len(rc) == 1:
                lelem = ET.SubElement(elem, "param", name="length")
                lelem.text = rc[0]
                continue
            if rc[0] != "min":
                lelem = ET.SubElement(elem, "param", name="minLength")
                lelem.text = rc[0]
            if rc[1] != "max":
                helem = ET.SubElement(elem, "param", name="maxLength")
                helem.text = rc[1]
