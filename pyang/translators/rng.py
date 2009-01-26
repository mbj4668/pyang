# Copyright (c) 2009 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>
#                       Martin Bjorklund <mbj@tail-f.com>
#
# Translator of YANG to RELAX NG with additional annotations
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

"""Translator from YANG to RELAX NG with annotations.

It is designed as a plugin for the pyang program and defines several
new command-line options:

--rng-no-annotations
    No output of DTD compatibility annotations

--rng-no-dublin-core
    No output of Dublin Core annotations

-rng-no-netmod
    No output of NETMOD-specific attributes

Two classes are defined in this module:

* `RNGPlugin`: pyang plugin interface class

* `RNGTranslator`: its instance preforms the translation
"""

__docformat__ = "reStructuredText"

import sys
import optparse
try:
    import xml.etree.ElementTree as ET
except ImportError:
    pass

from pyang import plugin, statements, error

def pyang_plugin_init():
    plugin.register_plugin(RNGPlugin())

class RNGPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        fmts['rng'] = self
    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--rng-no-annotations",
                                 dest="rng_no_annotations",
                                 action="store_true",
                                 help="No output of DTD compatibility"
                                 " annotations"),
            optparse.make_option("--rng-no-dublin-core",
                                 dest="rng_no_dublin_core",
                                 action="store_true",
                                 help="No output of Dublin Core"
                                 " annotations"),
            optparse.make_option("--rng-no-netmod",
                                 dest="rng_no_netmod",
                                 action="store_true",
                                 help="No output of NETMOD-specific"
                                 " attributes"),
            ]
        g = optparser.add_option_group("RELAX NG output specific options")
        g.add_options(optlist)
    def emit(self, ctx, module, fd):
        try:
            import xml.etree.ElementTree as ET
        except ImportError:
            print >> sys.stderr, ("RELAX NG translation needs the python module "
                                  "etree, available in python 2.5")
            sys.exit(1)

        emit_rng(ctx, module, fd)

def emit_rng(ctx, module, fd):
    # No errors are allowed
    for (epos, etag, eargs) in ctx.errors:
        if (epos.top_name == module.arg and
            error.is_error(error.err_level(etag))):
            print >> sys.stderr, "RELAX NG translation needs a valid module"
            sys.exit(1)
    emit = []
    if ctx.opts.rng_no_dublin_core != True:
        emit.append("dc")
    if ctx.opts.rng_no_annotations != True:
        emit.append("a")
    if ctx.opts.rng_no_netmod != True:
        emit.append("nm")
    etree = RNGTranslator().translate((module,), emit, debug=0)
    etree.write(fd, "UTF-8")


class RNGTranslator(object):

    """Instances of this class translate YANG to RELAX NG + annotations.

    The `translate` method walks recursively down the tree of YANG
    statements and builds one or more resulting ElementTree(s)
    containing the corresponding schemas. For each YANG statement, a
    callback method for the statement's keyword is dispatched.

    Instance variables:
    
    * `debug`: integer controlling level of debug messages
    * `emit`: list of prefixes (keys in `schema_languages` dictionary)
      controlling which annotations will be generated.
    * `has_anyxml`: boolean indicating occurence of ``anyxml``
      statement (so that `anyxml_def` has to be inserted)
    * `used_defs`: list of used typedefs and groupings whose
      definition has already been imported
    * `module`: YANG module that is being translated
    * `root_elem`: <grammar> ETree Element, which is the root of the
      resulting RELAX NG ETree
    * `stmt_handler`: dictionary dispatching callback methods for
      handling YANG statements (keyword -> method)
    * `type_handler`: dictionary dispatching callback methods for
      YANG built-in types (type -> method)

    Class variables are: `anyxml_def`, `datatree_nodes`, `datatype_map`,
    `grammar_attrs`, `schema_languages`.

    One static method is defined: `summarize_ranges`.
    """

    YANG_version = 1
    """This is checked against the yang-version statement, if present."""

    grammar_attrs = {
        "xmlns" : "http://relaxng.org/ns/structure/1.0",
        "xmlns:nmt" : "urn:ietf:params:xml:ns:netmod:tree:1",
        "datatypeLibrary" : "http://www.w3.org/2001/XMLSchema-datatypes",
    }
    """Common attributes of the <grammar> element."""

    schema_languages = {
        "a": "http://relaxng.org/ns/compatibility/annotations/1.0",
        "dc": "http://purl.org/dc/terms",
        "nm": "urn:ietf:params:xml:ns:netmod:rng-annot:1",
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
        "string": "string",
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
            "argument": self.noop,
            "augment": self.noop,
            "base": self.noop,
            "belongs-to": self.noop,
            "case": self.case_stmt,
            "choice": self.choice_stmt,
            "config": self.nm_attribute,
            "contact": self.noop,
            "container": self.container_stmt,
            "default": self.default_stmt,
            "deviation": self.noop,
            "description": self.description_stmt,
            "enum" : self.enum_stmt,
            "feature": self.noop,
            "identity": self.noop,
            "if-feature": self.noop,
            "extension": self.noop,
            "import" : self.noop,
            "include" : self.include_stmt,
            "input": self.noop,
            "grouping" : self.noop,
            "key": self.nm_attribute,
            "leaf": self.leaf_stmt,
            "leaf-list": self.handle_list,
            "list": self.handle_list,
            "mandatory": self.noop,
            "min-elements": self.noop,
            "max-elements": self.noop,
            "must": self.must_stmt,
            "namespace": self.noop,
            "notification": self.noop,
            "ordered-by": self.noop,
            "organization": self.noop,
            "output": self.noop,
            "prefix": self.noop,
            "presence": self.noop,
            "reference": self.reference_stmt,
            "refine": self.noop,
            "rpc": self.noop,
            "min-elements": self.noop,
            "status" : self.nm_attribute,
            "type": self.type_stmt,
            "typedef" : self.noop,
            "unique" : self.nm_attribute,
            "units" : self.nm_attribute,
            "uses" : self.uses_stmt,
            "when" : self.nm_attribute,
            "yang-version": self.yang_version_stmt,
        }
        self.type_handler = {
            "boolean": self.mapped_type,
            "binary": self.mapped_type,
            "bits": self.bits_type,
            "enumeration": self.choice_type,
            "empty": self.empty_type,
            "float32": self.numeric_type,
            "float64": self.numeric_type,
            "instance-identifier": self.mapped_type,
            "int8": self.numeric_type,
            "int16": self.numeric_type,
            "int32": self.numeric_type,
            "int64": self.numeric_type,
            "leafref": self.noop,
            "string" : self.string_type,
            "uint8": self.numeric_type,
            "uint16": self.numeric_type,
            "uint32": self.numeric_type,
            "uint64": self.numeric_type,
            "union": self.choice_type,
        }

    def translate(self, modules, emit=schema_languages.keys(), debug=0):
        """Translate `modules` to RELAX NG schema with annotations.

        The `emit` argument controls output of individual annotations
        (by default, all are present). The `debug` argument controls
        level of debug messages - 0 (default) supresses them.  
        """
        self.emit = emit
        self.debug = debug
        self.grammar_elem = ET.Element("grammar", self.grammar_attrs)
        for prefix in self.emit: # used namespaces
            self.grammar_elem.attrib["xmlns:" + prefix] = \
                self.schema_languages[prefix]
        self.setup_conceptual_tree()
        self.has_anyxml = False
        self.used_defs = []
        for module in modules:
            self.module = module
            ns = module.search_one("namespace").arg
            self.prefix = module.search_one("prefix").arg
            self.grammar_elem.attrib["xmlns:"+self.prefix] = ns
            src_text = "YANG module '%s'" % module.arg
            rev = module.search_one("revision")
            if rev:
                src_text += "revision %s" % rev.arg
            self.dc_element("source", src_text) 
            self.handle_substmts(module, self.top)
        self.handle_empty()
        self.dc_element("creator", "Pyang, RELAX NG plugin")
        return ET.ElementTree(element=self.grammar_elem)
        
    def new_element(self, parent, name):
        """
        Declare new element `name` under `parent`.

        Current namespace prefix (`self.prefix`) is prepended. Returns
        the corresponding RNG element.
        """
        return ET.SubElement(parent, "element", name=self.prefix+":"+name)

    def setup_conceptual_tree(self):
        """Create the conceptual tree structure.
        """
        start = ET.SubElement(self.grammar_elem, "start")
        self.prefix = "nmt"
        tree = self.new_element(start, "netmod-tree")
        self.top = self.new_element(tree, "top")
        self.rpcs = self.new_element(tree, "rpc-methods")
        self.notifications = self.new_element(tree, "notifications")

    def handle_empty(self):
        """Handle empty subtree(s) of conceptual tree.

        If any of the subtrees of the conceptual tree is empty, put
        <empty/> as its content.
        """
        for subtree in (self.top, self.rpcs, self.notifications):
            if len(subtree) == 0:
                ET.SubElement(subtree, "empty")

    def dc_element(self, name, text):
        """Add DC element `name` containing `text` to <grammar>."""
        if "dc" in self.emit:
            dcel = ET.Element("dc:" + name)
            dcel.text = text
            self.grammar_elem.insert(0,dcel)

    def unique_def_name(self, stmt):
        """Answer mangled name of the receiver (typedef or grouping).

        Identifiers of all ancestor nodes are prepended, separated by
        ``__``. Moreover, symbols from foreign modules start with
        their module name (local names thus start with ``__``).
        """
        path = stmt.full_path()
        if stmt.i_module == self.module:
            local = "__".join(path[1:])
            if len(path) == 2:
                return local
            else:
                return "__" + local
        else:
            return "__".join(path)

    def _summarize_ranges(self, ranges):
        """Resolve 'min' and 'max' in a cascade of ranges."""
        if len(ranges) == 0: return []
        min = 'min'
        max = 'max'
        for r in ranges:
            if r[0][0] == "min":
                r[0][0] = min
            else:
                min = r[0][0]
            if r[-1][1] == "max":
                r[-1][1] = max
            else:
                max = r[-1][1]
        return ranges[-1]

    def _numeric_type(self, y_type, ranges, p_elem):
        """Create <data> element with numeric type under `p_elem`."""
        r_type = self.datatype_map[y_type]
        if len(ranges) == 0:
            ET.SubElement(p_elem, "data", type=r_type)
            return
        if len(ranges) > 1:
            p_elem = ET.SubElement(p_elem, "choice")
        for r in ranges:
            d_elem = ET.SubElement(p_elem, "data", type=r_type)
            self._numeric_restriction(r, d_elem)

    def _string_type(self, lengths, patterns, p_elem):
        """Create <data> element with string type under `p_elem`."""
        pat_els = []
        for rexp in patterns:
            pel = ET.Element("param", name="pattern")
            pel.text = rexp
            pat_els.append(pel)
        if len(lengths) == 0:
            d_elem = ET.SubElement(p_elem, "data", type="string")
            for p in pat_els: d_elem.append(p) 
            return
        if len(lengths) > 1:
            p_elem = ET.SubElement(p_elem, "choice")
        for l in lengths:
            d_elem = ET.SubElement(p_elem, "data", type="string")
            self._string_restriction(l, pat_els, d_elem)

    def _numeric_restriction(self, range_, p_elem):
        """Create numeric restriction(s) for `p_elem`."""
        if range_[0] != "min":
            elem = ET.SubElement(p_elem, "param", name="minInclusive")
            elem.text = str(range_[0])
        if range_[1] != "max":
            elem = ET.SubElement(p_elem, "param", name="maxInclusive")
            if range_[1] is None:
                elem.text = str(range_[0])
            else:
                elem.text = str(range_[1])

    def _string_restriction(self, len_, pat_els, p_elem):
        """Create string restriction(s) for `p_elem`."""
        if len_[1] is None:
            elem = ET.SubElement(p_elem, "param", name="length")
            elem.text = str(len_[0])
        else:
            if len_[0] != "min":
                elem = ET.SubElement(p_elem, "param", name="minLength")
                elem.text = str(len_[0])
            if len_[1] != "max":
                elem = ET.SubElement(p_elem, "param", name="maxLength")
                elem.text = str(len_[1])
        for p in pat_els: p_elem.append(p)

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
                if def_name not in self.used_defs:
                    self.handle_stmt(def_, self.grammar_elem)
                    self.used_defs.append(def_name)
            return ET.Element("ref", name=self.unique_def_name(def_))
        mod_name = stmt.i_module.i_prefixes[prefix]
        def_name =  mod_name + "__" + ref
        if def_name not in self.used_defs:
            # pull the definition
            ext_mod = stmt.i_module.i_ctx.modules[mod_name]
            def_, = ext_mod.search(keyword=kw, arg=ref)
            self.handle_stmt(def_, self.grammar_elem)
            self.used_defs.append(def_name)
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

    def handle_substmts(self, stmt, p_elem):
        """Handle all substatements of `stmt`."""
        for sub in stmt.substmts: self.handle_stmt(sub, p_elem)

    # Handlers for YANG statements

    def anyxml_stmt(self, stmt, p_elem):
        if not self.has_anyxml:
            # install definition
            def_ = ET.fromstring(self.anyxml_def)
            self.grammar_elem.append(def_)
            self.has_anyxml = True
        elem = self.new_element(p_elem, stmt.arg)
        self.handle_substmts(stmt, elem)
        ET.SubElement(elem, "ref", name="__anyxml__")

    def nm_attribute(self, stmt, p_elem):
        """Map `stmt` to NETMOD-specific attribute."""
        if "nm" in self.emit:
            p_elem.attrib["nm:" + stmt.keyword] = stmt.arg

    def case_stmt(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "group")
        self.handle_substmts(stmt, elem)

    def choice_stmt(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "choice")
        self.handle_substmts(stmt, elem)

    def container_stmt(self, stmt, p_elem):
        if stmt.is_optional():
            p_elem = ET.SubElement(p_elem, "optional")
        elem = self.new_element(p_elem, stmt.arg)
        if len(stmt.substmts) == 0:
            ET.SubElement(elem, "empty")
        else:
            self.handle_substmts(stmt, elem)

    def default_stmt(self, stmt, p_elem):
        if "dsrl" in self.emit:
            delem = ET.SubElement(p_elem, "dsrl:default-content")
            delem.text = stmt.arg

    def description_stmt(self, stmt, p_elem):
        # ignore imported and top-level descriptions + desc. of enum
        if ("a" in self.emit and stmt.i_module == self.module != stmt.parent
            and stmt.parent.keyword != "enum"):
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
        min_el = stmt.search_one("min-elements")
        if min_el is None or int(min_el.arg) == 0:
            rng_card = "zeroOrMore"
        else:
            rng_card = "oneOrMore"
        cont = ET.SubElement(p_elem, rng_card)
        if min_el and int(min_el.arg) > 1:
            cont.attrib["nm:min-elements"] = min_el.arg
        max_el = stmt.search_one("max-elements")
        if max_el:
            cont.attrib["nm:max-elements"] = max_el.arg
        ordby = stmt.search_one("ordered-by")
        if ordby:
            cont.attrib["nm:ordered-by"] = ordby.arg
        elem = self.new_element(cont, stmt.arg)
        self.handle_substmts(stmt, elem)

    def _add_def(self, stmt):
        """Add ``typedef`` or ``grouping``."""
        elem = ET.SubElement(self.grammar_elem, "define",
                             name=self.unique_def_name(stmt))
        self.handle_substmts(stmt, elem)
        
    def include_stmt(self, stmt, p_elem):
        delem = ET.SubElement(p_elem, "include", href = stmt.arg + ".rng")

    def leaf_stmt(self, stmt, p_elem):
        if (len(stmt.search(keyword="mandatory", arg="true")) == 0 and
            (stmt.parent.keyword != "list" or
            stmt.arg not in stmt.parent.search(keyword="key")[0].arg)):
            p_elem = ET.SubElement(p_elem, "optional")
        elem = self.new_element(p_elem, stmt.arg)
        self.handle_substmts(stmt, elem)

    def must_stmt(self, stmt, p_elem):
        if "nm" not in self.emit: return
        mel = ET.SubElement(p_elem, "nm:must")
        ET.SubElement(mel, "nm:assert").text = stmt.arg
        em = stmt.search_one("error-message")
        if em:
            ET.SubElement(mel, "nm:error-message").text = em.arg
        eat = stmt.search_one("error-app-tag")
        if eat:
            ET.SubElement(mel, "nm:error-app-tag").text = eat.arg

    def noop(self, stmt, p_elem):
        pass

    def reference_stmt(self, stmt, p_elem):
        if stmt.i_module != self.module: # ignore imported descriptions
            return
        if stmt.parent == self.module: # top-level description
            self.dc_element("BibliographicResource", stmt.arg)
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

    def type_stmt(self, stmt, p_elem):
        """Handle ``type`` statement.

        Built-in types are handled by a specific type callback method
        defined below.
        """
        typedef = stmt.i_typedef
        if typedef is None: # built-in type
            self.type_handler[stmt.arg](stmt, p_elem)
        elif stmt.i_is_derived: # derived with restrictions
            self._unwind_type(stmt, p_elem)
        else:                   # just refer to type def.
            self._handle_ref(stmt.arg, typedef, p_elem)

    def _handle_ref(self, dname, dstmt, p_elem):
        """Insert <ref> and add definition if necessary."""
        if dname not in self.used_defs:
            self.used_defs.append(dname)
            self._add_def(dstmt)
        ET.SubElement(p_elem, "ref", name=self.unique_def_name(dstmt))

    def uses_stmt(self, stmt, p_elem):
        refines = stmt.search(keyword="refine")
        if len(refines) == 0:
            self._handle_ref(stmt.arg, stmt.i_grouping, p_elem)
        # else: make deep copy of the grouping and do modifications

    def yang_version_stmt(self, stmt, p_elem):
        if float(stmt.arg) != self.YANG_version:
            print >> sys.stderr, "Unsupported YANG version: %s" % stmt.arg
            sys.exit(1)

    # Handlers for YANG types

    def _unwind_type(self, stmt, p_elem):
        """Unwind type formed by multiple derivations."""
        patterns = []
        lengths = []
        ranges = []
        while 1:
            patterns.extend([p.arg for p in stmt.search(keyword="pattern")])
            if stmt.i_lengths:
                lengths[0:0] = [[list(lc) for lc in stmt.i_lengths]]
            if stmt.i_ranges:
                ranges[0:0] = [[list(rc) for rc in stmt.i_ranges]]
            if stmt.i_typedef is None: break
            stmt = stmt.i_typedef.search_one("type")
        if stmt.arg == "string":
            slen = self._summarize_ranges(lengths)
            self._string_type(slen, patterns, p_elem)
        else:
            srang = self._summarize_ranges(ranges)
            self._numeric_type(stmt.arg, srang, p_elem)

    def bits_type(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "list")
        for bit in stmt.search(keyword="bit"):
            optel = ET.SubElement(elem, "optional")
            velem = ET.SubElement(optel, "value")
            velem.text = bit.arg

    def choice_type(self, stmt, p_elem):
        """Handle ``enumeration`` and ``union`` types."""
        elem = ET.SubElement(p_elem, "choice")
        self.handle_substmts(stmt, elem)

    def empty_type(self, stmt, p_elem):
        ET.SubElement(p_elem, "empty")

    def mapped_type(self, stmt, p_elem):
        """Handle types that are simply mapped to RELAX NG."""
        ET.SubElement(p_elem, "data", type=self.datatype_map[stmt.arg])

    def numeric_type(self, stmt, p_elem):
        """Handle numeric types."""
        self._numeric_type(stmt.arg, stmt.i_ranges, p_elem)

    def string_type(self, stmt, p_elem):
        patterns = [p.arg for p in stmt.search(keyword="pattern")]
        self._string_type(stmt.i_lengths, patterns, p_elem)
