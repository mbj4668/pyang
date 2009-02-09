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

--rng-no-documentation
    No output of DTD compatibility documentation annotations

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

import pyang
from pyang import plugin, statements, error

def pyang_plugin_init():
    plugin.register_plugin(RNGPlugin())

class RNGPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        fmts['rng'] = self
    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--rng-no-documentation",
                                 dest="rng_no_documentation",
                                 action="store_true",
                                 help="No output of DTD compatibility"
                                 " documentation annotations"),
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
            print >> sys.stderr, ("RELAX NG translation needs etree module "
                                  "available since python 2.5")
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
    if ctx.opts.rng_no_documentation != True:
        emit.append("a")
    if ctx.opts.rng_no_netmod != True:
        emit.append("nma")
    etree = RNGTranslator().translate((module,), emit, debug=0)
    etree.write(fd, "UTF-8")

class Patch(object):

    """Instances of this class represent a patch to the YANG tree.

    Instance variables:

    * `path`: list specifying the node where to apply the patch
    * `slist`: list of statements to apply
    """

    def __init__(self, refaug, prefix=None):
        """Initialize the instance from `refaug` statement.

        `refaug` must be refinement or augment statement.
        Also remove `prefix` from all path components.
        """
        self.path = []
        for comp in refaug.arg.split("/"):
            pref, colon, ident = comp.partition(":")
            if not colon:
                self.path.append(pref)
            elif pref == prefix:
                self.path.append(ident)
            else:
                self.path.append(comp)
        self.slist = refaug.substmts

    def pop(self):
        """Pop and return the first element of `self.path`."""
        return self.path.pop(0)

    def colocated(self, patch):
        """Do patch and receiver have the same path?"""
        return self.path == patch.path

    def combine(self, patch):
        """Add `patch.slist` to `self.slist`; avoid duplication."""
        exclusive = set(["config", "default", "mandatory", "presence",
                     "min-elements", "max-elements"])
        kws = set([s.keyword for s in self.slist]) & exclusive
        add = [n for n in patch.slist if n.keyword not in kws]
        self.slist.extend(add)

    def search(self, keyword, arg=None):
        """Does `self.slist` contain stmt with `keyword` (and `arg`)?"""
        for st in self.slist:
            if st.keyword == keyword:
                return arg == None or st.arg == arg

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
        "nma": "urn:ietf:params:xml:ns:netmod:dsdl-annotations:1",
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

    anyxml_def = ('<define name="__anyxml__"><zeroOrMore><choice>' +
                  '<attribute><anyName/></attribute>' +
                  '<element><anyName/><ref name="__anyxml__"/></element>' +
                  '<text/></choice></zeroOrMore></define>')

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
            "config": self.nma_attribute,
            "contact": self.noop,
            "container": self.container_stmt,
            "default": self.default_stmt,
            "deviation": self.noop,
            "description": self.description_stmt,
            "enum" : self.enum_stmt,
            "feature": self.noop,
            "identity": self.noop,
            "if-feature": self.nma_attribute,
            "extension": self.noop,
            "import" : self.noop,
            "include" : self.include_stmt,
            "input": self.input_stmt,
            "grouping" : self.noop,
            "key": self.noop,
            "leaf": self.leaf_stmt,
            "leaf-list": self.leaf_list_stmt,
            "list": self.list_stmt,
            "mandatory": self.noop,
            "min-elements": self.noop,
            "max-elements": self.noop,
            "must": self.must_stmt,
            "namespace": self.noop,
            "notification": self.notification_stmt,
            "ordered-by": self.nma_attribute,
            "organization": self.noop,
            "output": self.output_stmt,
            "prefix": self.noop,
            "presence": self.noop,
            "reference": self.reference_stmt,
            "refine": self.noop,
            "revision": self.noop,
            "rpc": self.rpc_stmt,
            "min-elements": self.noop,
            "status" : self.nma_attribute,
            "type": self.type_stmt,
            "typedef" : self.noop,
            "unique" : self.nma_attribute,
            "units" : self.nma_attribute,
            "uses" : self.uses_stmt,
            "when" : self.nma_attribute,
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
            "keyref": self.noop,   # FIXME: remove when pyang handles leafrefs
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
            revs = module.search(keyword="revision")
            if len(revs) > 0:
                src_text += " revision %s" % self._current_revision(revs)
            self.dc_element("source", src_text) 
            self.handle_substmts(module, self.data)
        self.handle_empty()
        self.dc_element("creator",
                        "Pyang %s, RELAX NG plugin" % pyang.__version__)
        return ET.ElementTree(element=self.grammar_elem)
        
    def new_element(self, parent, name, prefix=None):
        """
        Declare new element `name` under `parent`.

        Current namespace prefix (`self.prefix`) is prepended. Returns
        the corresponding RNG element.
        """
        if prefix is None: prefix = self.prefix
        return ET.SubElement(parent, "element", name=prefix+":"+name)

    def setup_conceptual_tree(self):
        """Create the conceptual tree structure.
        """
        start = ET.SubElement(self.grammar_elem, "start")
        self.prefix = "nmt"
        tree = self.new_element(start, "netmod-tree")
        top = self.new_element(tree, "top")
        self.data = ET.SubElement(top, "interleave")
        self.rpcs = self.new_element(tree, "rpc-methods")
        self.notifications = self.new_element(tree, "notifications")

    def handle_empty(self):
        """Handle empty subtree(s) of conceptual tree.

        If any of the subtrees of the conceptual tree is empty, put
        <empty/> as its content.
        """
        for subtree in (self.data, self.rpcs, self.notifications):
            if len(subtree) == 0:
                ET.SubElement(subtree, "empty")

    def dc_element(self, name, text):
        """Add DC element `name` containing `text` to <grammar>."""
        if "dc" in self.emit:
            dcel = ET.Element("dc:" + name)
            dcel.text = text
            self.grammar_elem.insert(0,dcel)

    def unique_def_name(self, stmt):
        """Answer mangled name of the receiver (typedef or grouping)."""
        mod = stmt.i_module
        if mod.keyword == "submodule":
            pref = mod.search_one("belongs-to").arg
        else:
            pref = mod.arg
        return pref + "__" + "__".join(stmt.full_path())

    def _add_patch(self, pset, patch):
        """Add `patch` to `pset`."""
        car = patch.pop()
        if car in pset:
            sel = [ x for x in pset[car] if patch.colocated(x) ]
            if sel:
                sel[0].combine(patch)
            else:
                pset[car].append(patch)
        else:
            pset[car] = [patch]

    def _sift_pset(self, pset, patch):
        """Prepare patch for the next level."""
        car = patch.pop()
        if car in pset:
            pset[car].append(patch)
        else:
            pset[car] = [patch]
        return car

    def _current_revision(self, r_stmts):
        """Pick the most recent revision date from `r_stmts`."""
        cur = max([[int(p) for p in r.arg.split("-")] for r in r_stmts])
        return "%4d-%02d-%02d" % tuple(cur)

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

    def _is_mandatory(self, stmt):
        """Return boolean saying whether `stmt` is mandatory."""
        if stmt.keyword == "leaf":
            return stmt.search_one("mandatory", "true") is not None
        elif stmt.keyword in ("list", "leaf-list"):
            mi = stmt.search_one("min-elements")
            return mi is not None and int(mi.arg) > 0
        elif stmt.keyword == "container":
            if stmt.search_one("presence"):
                return False
        elif stmt.keyword == "uses":
            stmt = stmt.i_grouping
        else:
            return False
        for sub in stmt.substmts:
            if self._is_mandatory(sub): return True
        return False

    def _min_max(self, slist):
        """Return value pair (min-elements, max-elements)."""
        min_el = max_el = -1
        for st in slist:
            if min_el == -1 and st.keyword == "min-elements":
                min_el = int(st.arg)
            if max_el == -1 and st.keyword == "max-elements":
                max_el = int(st.arg)
            if min_el != -1 and max_el != -1: break
        return (min_el, max_el)

    def handle_stmt(self, stmt, p_elem, pset={}):
        """
        Run handler method for `stmt` in the context of `p_elem`.

        All handler methods are defined below and have the same
        arguments. They should create the schema fragment
        corresponding to `stmt`, insert it under `p_elem` and perform
        all side effects as necessary.
        """
        if self.debug > 0:
            sys.stderr.write("Handling '%s %s'\n" %
                             (util.keyword_to_str(stmt.raw_keyword), stmt.arg))
        self.stmt_handler[stmt.keyword](stmt, p_elem, pset)

    def handle_substmts(self, stmt, p_elem, pset={}):
        """Handle all substatements of `stmt`."""
        for sub in stmt.substmts:
            self.handle_stmt(sub, p_elem, pset)

    # Handlers for YANG statements

    def anyxml_stmt(self, stmt, p_elem, pset):
        if not self.has_anyxml:
            # install definition
            def_ = ET.fromstring(self.anyxml_def)
            self.grammar_elem.append(def_)
            self.has_anyxml = True
        elem = ET.Element("element", name=self.prefix+":"+stmt.arg)
        is_opt = stmt.search_one("mandatory", "true") is None
        for p in pset.pop(stmt.arg, []):
            if p.search("mandatory", "true"): is_opt = False
            for st in p.slist: self.handle_stmt(st, elem)
        if is_opt: p_elem = ET.SubElement(p_elem, "optional")
        p_elem.append(elem)
        ET.SubElement(elem, "ref", name="__anyxml__")
        self.handle_substmts(stmt, elem)

    def nma_attribute(self, stmt, p_elem, pset=None):
        """Map `stmt` to NETMOD-specific attribute."""
        if "nma" in self.emit:
            p_elem.attrib["nma:" + stmt.keyword] = stmt.arg

    def case_stmt(self, stmt, p_elem, pset):
        elem = ET.SubElement(p_elem, "group")
        new_pset = {}
        todo = []
        for p in pset.pop(stmt.arg, []):
            if p.path:
                self._sift_pset(new_pset, p)
            else:
                todo = p.slist
        for st in todo: self.handle_stmt(st, elem, new_pset)
        self.handle_substmts(stmt, elem, new_pset)

    def choice_stmt(self, stmt, p_elem, pset):
        elem = ET.Element("choice")
        is_opt = stmt.search_one("mandatory", "true") is None
        new_pset = {}
        todo = []
        for p in pset.pop(stmt.arg, []):
            if p.path:
                cid = self._sift_pset(new_pset, p)
                if not stmt.search(keyword="case", arg=cid):
                    for p in new_pset[cid]: p.pop()
            else:
                todo = p.slist
                if p.search("mandatory", "true"): is_opt = False
        if is_opt: p_elem = ET.SubElement(p_elem, "optional")
        p_elem.append(elem)
        for st in todo: self.handle_stmt(st, elem, new_pset)
        self.handle_substmts(stmt, elem, new_pset)
        
    def container_stmt(self, stmt, p_elem, pset):
        elem = ET.Element("element", name=self.prefix+":"+stmt.arg)
        is_opt = not self._is_mandatory(stmt)
        new_pset = {}
        todo = []
        for p in pset.pop(stmt.arg, []):
            if p.path:
                self._sift_pset(new_pset, p)
            else:
                todo = p.slist
                if p.search("presence"): is_opt = True
        if is_opt: p_elem = ET.SubElement(p_elem, "optional")
        p_elem.append(elem)
        for st in todo: self.handle_stmt(st, elem, new_pset)
        self.handle_substmts(stmt, elem, new_pset)

    def default_stmt(self, stmt, p_elem, pset):
        if "nma:default" not in p_elem.attrib:
            self.nma_attribute(stmt, p_elem)

    def description_stmt(self, stmt, p_elem, pset):
        # ignore imported and top-level descriptions + desc. of enum
        if ("a" in self.emit and
            stmt.i_module == self.module != stmt.parent and
            stmt.parent.keyword != "enum"):
            elem = ET.Element("a:documentation")
            p_elem.insert(0, elem)
            elem.text = stmt.arg

    def enum_stmt(self, stmt, p_elem, pset):
        elem = ET.SubElement(p_elem, "value")
        elem.text = stmt.arg
        for sub in stmt.search(keyword="status"):
            self.handle_stmt(sub, elem)

    def include_stmt(self, stmt, p_elem, pset):
        subm = self.module.i_ctx.modules[stmt.arg]
        self.handle_substmts(subm, p_elem)

    def input_stmt(self, stmt, p_elem, pset):
        elem = self.new_element(p_elem, "input", prefix="nmt")
        self.handle_substmts(stmt, elem)

    def leaf_stmt(self, stmt, p_elem, pset):
        elem = ET.Element("element", name=self.prefix+":"+stmt.arg)
        is_opt = (stmt.search_one("mandatory", "true") is None and
                  stmt.arg not in p_elem.attrib.get("nma:key",[]))
        for p in pset.pop(stmt.arg, []):
            if p.search("mandatory", "true"): is_opt = False
            for st in p.slist: self.handle_stmt(st, elem)
        if is_opt: p_elem = ET.SubElement(p_elem, "optional")
        p_elem.append(elem)
        self.handle_substmts(stmt, elem)

    def leaf_list_stmt(self, stmt, p_elem, pset):
        elem = ET.Element("element", name=self.prefix+":"+stmt.arg)
        min_el, max_el = self._min_max(stmt.substmts)
        new_pset = {}
        for p in pset.pop(stmt.arg, []):
            mi, ma = self._min_max(p.slist)
            if mi >= 0: min_el = mi
            if ma >= 0: max_el = ma
            for st in p.slist: self.handle_stmt(st, elem)
        if min_el <= 0:
            rng_card = "zeroOrMore"
        else:
            rng_card = "oneOrMore"
        cont = ET.SubElement(p_elem, rng_card)
        if min_el > 1:
            cont.attrib["nma:min-elements"] = str(min_el)
        if max_el > -1:
            cont.attrib["nma:max-elements"] = str(max_el)
        cont.append(elem)
        self.handle_substmts(stmt, elem, new_pset)

    def list_stmt(self, stmt, p_elem, pset):
        elem = ET.Element("element", name=self.prefix+":"+stmt.arg)
        self.nma_attribute(stmt.search_one("key"), elem)
        min_el, max_el = self._min_max(stmt.substmts)
        new_pset = {}
        todo = []
        for p in pset.pop(stmt.arg, []):
            if p.path:
                self._sift_pset(new_pset, p)
            else:
                todo = p.slist
                mi, ma = self._min_max(p.slist)
                if mi >= 0: min_el = mi
                if ma >= 0: max_el = ma
        if min_el <= 0:
            rng_card = "zeroOrMore"
        else:
            rng_card = "oneOrMore"
        cont = ET.SubElement(p_elem, rng_card)
        if min_el > 1:
            cont.attrib["nma:min-elements"] = str(min_el)
        if max_el > -1:
            cont.attrib["nma:max-elements"] = str(max_el)
        cont.append(elem)
        for st in todo: self.handle_stmt(st, elem, new_pset)
        self.handle_substmts(stmt, elem, new_pset)

    def must_stmt(self, stmt, p_elem, pset):
        if "nma" not in self.emit: return
        mel = ET.SubElement(p_elem, "nma:must")
        mel.attrib["assert"] = stmt.arg
        em = stmt.search_one("error-message")
        if em:
            ET.SubElement(mel, "nma:error-message").text = em.arg
        eat = stmt.search_one("error-app-tag")
        if eat:
            ET.SubElement(mel, "nma:error-app-tag").text = eat.arg

    def noop(self, stmt, p_elem, pset):
        pass

    def notification_stmt(self, stmt, p_elem, pset):
        elem = self.new_element(self.notifications, "notification",
                                prefix="nmt")
        attr = ET.SubElement(elem, "attribute", name="name")
        ET.SubElement(attr, "value").text = stmt.arg
        self.handle_substmts(stmt, elem)

    def output_stmt(self, stmt, p_elem, pset):
        elem = self.new_element(p_elem, "output", prefix="nmt")
        self.handle_substmts(stmt, elem)

    def reference_stmt(self, stmt, p_elem, pset):
        # ignore imported and top-level descriptions + desc. of enum
        if ("a" in self.emit and
            stmt.i_module == self.module != stmt.parent and
            stmt.parent.keyword != "enum"):
            elem = ET.Element("a:documentation")
            p_elem.append(elem)
            elem.text = "See: " + stmt.arg

    def rpc_stmt(self, stmt, p_elem, pset):
        elem = self.new_element(self.rpcs, "rpc-method", prefix="nmt")
        attr = ET.SubElement(elem, "attribute", name="name")
        ET.SubElement(attr, "value").text = stmt.arg
        self.handle_substmts(stmt, elem)

    def type_stmt(self, stmt, p_elem, pset):
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
        uname = self.unique_def_name(dstmt)
        if uname not in self.used_defs: # add definition
            self.used_defs.append(uname)
            elem = ET.SubElement(self.grammar_elem, "define", name=uname)
            self.handle_substmts(dstmt, elem)
        ET.SubElement(p_elem, "ref", name=uname)

    def uses_stmt(self, stmt, p_elem, pset):
        noexpand = True
        for sub in stmt.substmts:
            if sub.keyword in ("refine", "augment"):
                noexpand = False
                self._add_patch(pset, Patch(sub, prefix=self.prefix))
        if noexpand and pset:
            for nid in pset:
                if stmt.i_grouping.search(arg=nid):
                    noexpand = False
                    break
        if noexpand:
            self._handle_ref(stmt.arg, stmt.i_grouping, p_elem)
        else:
            self.handle_substmts(stmt.i_grouping, p_elem, pset)

    def yang_version_stmt(self, stmt, p_elem, pset):
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
