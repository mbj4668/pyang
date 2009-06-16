# Copyright (c) 2009 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>
#                       Martin Bjorklund <mbj@tail-f.com>
#
# Translator of YANG to conceptual tree schema
# (RELAX NG with additional annotations)
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

"""Translator from YANG to conceptual tree schema.

It is designed as a plugin for the pyang program and defines several
new command-line options:

--cts-no-documentation
    No output of DTD compatibility documentation annotations

--cts-no-dublin-core
    No output of Dublin Core annotations

--cts-record-defs
    Record all top-level defs, even if they are not used

Three classes are defined in this module:

* `CTSPlugin`: pyang plugin interface class

* `CTSTranslator`: provides instance that preforms the mapping

* `Patch`: utility class representing a patch to the YANG tree
  where augment and refine statements are recorded
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
    plugin.register_plugin(CTSPlugin())

class CTSPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        fmts['cts'] = self
    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--cts-no-documentation",
                                 dest="cts_no_documentation",
                                 action="store_true",
                                 default=False,
                                 help="No output of DTD compatibility"
                                 " documentation annotations"),
            optparse.make_option("--cts-no-dublin-core",
                                 dest="cts_no_dublin_core",
                                 action="store_true",
                                 default=False,
                                 help="No output of Dublin Core"
                                 " annotations"),
            optparse.make_option("--cts-record-defs",
                                 dest="cts_record_defs",
                                 action="store_true",
                                 default=False,
                                 help="Record all top-level defs"
                                 " (even if not used)"),
            ]
        g = optparser.add_option_group("Conceptual tree schema "
                                       "output specific options")
        g.add_options(optlist)
    def emit(self, ctx, module, fd):
        try:
            import xml.etree.ElementTree as ET
        except ImportError:
            print >> sys.stderr, ("CTS translation needs etree module "
                                  "available since python 2.5")
            sys.exit(1)

        if module.keyword == 'submodule':
            print >> sys.stderr, "Cannot translate submodules"
            sys.exit(1)

        emit_cts(ctx, module, fd)

def emit_cts(ctx, module, fd):
    # No errors are allowed
    for (epos, etag, eargs) in ctx.errors:
        if (epos.top_name == module.arg and
            error.is_error(error.err_level(etag))):
            print >> sys.stderr, "CTS translation needs a valid module"
            sys.exit(1)
    etree = CTSTranslator().translate((module,),
                                      ctx.opts.cts_no_dublin_core,
                                      ctx.opts.cts_no_documentation,
                                      ctx.opts.cts_record_defs, debug=0)
    etree.write(fd, "UTF-8")

class Patch(object):

    """Instances of this class represent a patch to the YANG tree.

    A Patch is filled with statements from 'refine' and/or 'augment'
    that must be applied to a single node.

    Instance variables:

    * `path`: list specifying the relative path to the node where the
      patch is to be applied

    * `slist`: list of statements to apply
    """

    def __init__(self, refaug, prefix=None):
        """Initialize the instance from `refaug` statement.

        `refaug` must be 'refine' or 'augment' statement.
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

    def decide_mandatory(self, previous):
        """Return the net result for mandatory.

        Argument `previous` carries the status of mandatory property
        from main context.
        """
        for st in self.slist:
            if st.keyword == "mandatory":
                return st.arg == "true"
        return previous

    def has(self, keyword, arg=None):
        """Does `self.slist` contain stmt with `keyword` (and `arg`)?"""
        for st in self.slist:
            if st.keyword == keyword:
                return arg == None or st.arg == arg

class CTSTranslator(object):

    """
    Instances of this class translate YANG to conceptual tree schema.

    The `translate` method walks recursively down the tree of YANG
    statements and builds the resulting ElementTree containing the
    annotated RELAX NG schema for the conceptual tree.

    Instance variables:
    
    * `confdata`: root element of the main schema subtree for
      configuration data

    * `debug`: integer controlling level of debug messages

    * `grammar_elem`: <grammar> ETree Element, which is the root of
      the resulting RELAX NG ETree

    * `has_anyxml`: boolean indicating occurence of 'anyxml'
      statement (so that `anyxml_def` has to be inserted)

    * `module`: YANG module that is being translated

    * `namespaces`: mapping of used NS URIs to prefixes

    * `notifications`: root element of the schema subtree for
      notifications

    * `no_data`: boolean signalling that no data nodes have been
      encountered and conceptual tree skeleton is not in place yet

    * `prefix`: prefix of the current module

    * `prefix_map`: map module-local prefixes to schema prefixes

    * `rpcs`: root element of the schema subtree for RPCs

    * `stmt_handler`: dictionary dispatching callback methods for
      handling YANG statements (keyword -> method)

    * `type_handler`: dictionary dispatching callback methods for
      YANG built-in types (type -> method)

    * `used_defs`: list of used typedefs and groupings whose
      definition has already been imported
    """

    YANG_version = 1
    """Checked against the yang-version statement, if present."""

    dc_uri = "http://purl.org/dc/terms"
    """Dublin Core URI"""
    a_uri =  "http://relaxng.org/ns/compatibility/annotations/1.0"
    """DTD compatibility annotattions URI"""

    grammar_attrs = {
        "xmlns" : "http://relaxng.org/ns/structure/1.0",
        "datatypeLibrary" : "http://www.w3.org/2001/XMLSchema-datatypes",
    }
    """Common attributes of the <grammar> element."""

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

    anyxml_def = ('<define name="__anyxml__"><zeroOrMore><choice>' +
                  '<attribute><anyName/></attribute>' +
                  '<element><anyName/><ref name="__anyxml__"/></element>' +
                  '<text/></choice></zeroOrMore></define>')
    """This definition is inserted first time 'anyxml' is found ."""

    data_nodes = ("leaf", "container", "leaf-list", "list",
                  "anyxml", "rpc", "notification")
    """Keywords of YANG data nodes."""

    def __init__(self):
        """Initialize the statement and type dispatchers.

        The same instance may be used repeatedly since all specific
        instance variables are initialized by the `translate` method.

        To change the behaviour of the translator, make a subclass and
        replace appropriate callback methods and/or change the
        `stmt_handler` or `type_handler` dictionaries.
        """
        self.namespaces = {
            "urn:ietf:params:xml:ns:netmod:conceptual-tree:1" : "nmt",
            "urn:ietf:params:xml:ns:netmod:dsdl-annotations:1" : "nma",
        }
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
            "default": self.nma_attribute,
            "deviation": self.noop,
            "description": self.description_stmt,
            "enum" : self.enum_stmt,
            "feature": self.noop,
            "identity": self.noop,
            "if-feature": self.nma_attribute,
            "extension": self.noop,
            "import" : self.noop,
            "include" : self.include_stmt,
            "input": self.noop,
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
            "unique" : self.unique_stmt,
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
            "leafref": self.noop,
            "string" : self.string_type,
            "uint8": self.numeric_type,
            "uint16": self.numeric_type,
            "uint32": self.numeric_type,
            "uint64": self.numeric_type,
            "union": self.choice_type,
        }

    def translate(self, modules, no_dc=False, no_a=False,
                  record_defs=False, debug=0):
        """Translate `modules` to conceptual tree schema.

        Return value: ElementTree with the resulting schema. If
        `no_dc`/`no_a` is true, Dublin Core/documentation
        annotations are omitted. Argument `record_defs` controls
        whether unused groupings and typedefs from the top level of
        `modules` are mapped to the output schema.
        """
        if not no_dc: self.namespaces[self.dc_uri] = "dc"
        if not no_a: self.namespaces[self.a_uri] = "a"
        self.debug = debug
        self.grammar_elem = ET.Element("grammar", self.grammar_attrs)
        self.no_data = True
        self.has_anyxml = False
        self.used_defs = []
        for module in modules:
            self.module = module
            self.prefix_map = {}
            prefix = module.search_one("prefix").arg
            ns_uri = module.search_one("namespace").arg
            self.prefix = self.add_namespace(ns_uri, prefix)
            src_text = "YANG module '%s'" % module.arg
            revs = module.search("revision")
            if len(revs) > 0:
                src_text += " revision %s" % self.current_revision(revs)
            self.dc_element("source", src_text)
            if record_defs: self.preload_defs()
            if self.has_data_node(module):
                if self.no_data:
                    self.no_data = False
                    self.setup_conceptual_tree()
                self.handle_substmts(module, self.confdata)
        self.handle_empty()
        self.declare_namespaces()
        self.dc_element("creator",
                        "Pyang %s, CTS plugin" % pyang.__version__)
        return ET.ElementTree(element=self.grammar_elem)

    def add_namespace(self, uri, prefix):
        """Add new item `uri`:`prefix` to `self.namespaces`.

        The prefix to be actually used for `uri` is returned.  If the
        namespace is already known, the old prefix should be used.
        Prefix clashes are resolved by disambiguating `prefix`.
        """
        if uri in self.namespaces:
            new = self.namespaces[uri]
        else:
            end = 1
            new = prefix
            while new in self.namespaces.values():
                new = "%s%x" % (prefix,end)
                end += 1
            self.namespaces[uri] = new
        self.prefix_map[prefix] = new
        return new

    def preload_defs(self):
        """Preload all top-level definitions."""
        for d in (self.module.search("grouping") +
                  self.module.search("typedef")):
            self.handle_ref(d)
        
    def new_element(self, parent, name, prefix=None):
        """
        Create <rng:element name="`prefix`:`name`"> under `parent`.

        Return value: the new RNG element.
        """
        if prefix is None: prefix = self.prefix
        return ET.SubElement(parent, "element", name=prefix+":"+name)

    def prefix_desc_nodeid(self, nodeid):
        """Add local prefix to all components of `nodeid`."""
        def pref_comp(c):
            if ":" in c: return c
            return self.prefix + ":" + c
        return "/".join([pref_comp(c) for c in nodeid.split("/")])

    def setup_conceptual_tree(self):
        """Create the conceptual tree structure."""
        start = ET.SubElement(self.grammar_elem, "start")
        prefix = "nmt"
        tree = self.new_element(start, "netmod-tree", prefix)
        top = self.new_element(tree, "top", prefix)
        self.confdata = ET.SubElement(top, "interleave")
        self.rpcs = self.new_element(tree, "rpc-methods", prefix)
        self.notifications = self.new_element(tree, "notifications",prefix)

    def handle_empty(self):
        """Handle empty subtree(s) of conceptual tree.

        If any of the subtrees of the conceptual tree is empty, put
        <empty/> as its content.
        """
        if self.no_data: return
        for subtree in (self.confdata, self.rpcs, self.notifications):
            if len(subtree) == 0:
                ET.SubElement(subtree, "empty")

    def dc_element(self, name, text):
        """Add DC element `name` containing `text` to <grammar>."""
        if self.dc_uri in self.namespaces:
            dcel = ET.Element(self.namespaces[self.dc_uri] + ":" + name)
            dcel.text = text
            self.grammar_elem.insert(0,dcel)

    def unique_def_name(self, stmt):
        """Answer mangled name of the receiver (typedef or grouping)."""
        mod = stmt.i_module
        if stmt.keyword == "typedef":
            pref = ""
        else:
            pref = "_"
        if mod.keyword == "submodule":
            pref += mod.search_one("belongs-to").arg
        else:
            pref += mod.arg
        return pref + "__" + "__".join(stmt.full_path())

    def has_data_node(self, stmt):
        """Does `stmt` have any data nodes?"""
        maybe = []
        for st in stmt.substmts:
            if st.keyword in self.data_nodes: return True
            if st.keyword in ["choice", "case"]:
                maybe.append(st)
            elif st.keyword == "uses":
                maybe.append(st.i_grouping)
        for m in maybe:
            if self.has_data_node(m): return True
        return False

    def add_patch(self, pset, patch):
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

    def sift_pset(self, pset, patch):
        """Prepare patch for the next level."""
        car = patch.pop()
        if car in pset:
            pset[car].append(patch)
        else:
            pset[car] = [patch]
        return car

    def current_revision(self, r_stmts):
        """Pick the most recent revision date from `r_stmts`."""
        cur = max([[int(p) for p in r.arg.split("-")] for r in r_stmts])
        return "%4d-%02d-%02d" % tuple(cur)

    def summarize_ranges(self, ranges):
        """Resolve 'min' and 'max' in a cascade of ranges.

        Argument `ranges` is a list of lists of pairs.  Example: if we
        have two consecutive restrictions '1..12' and 'min..3|7..max',
        then the argument is [[[1, 12]], [['min', 3], [7, 'max']]]
        and [[1,3], [7,12]] will be returned.
        """
        if len(ranges) == 0: return []
        min_ = 'min'
        max_ = 'max'
        for r in ranges:
            if r[0][0] == "min":
                r[0][0] = min_
            else:
                min_ = r[0][0]
            if r[-1][1] == "max":
                r[-1][1] = max_
            else:
                max_ = r[-1][1]
        return ranges[-1]

    def numeric_data(self, y_type, ranges, p_elem):
        """Create <data> element with numeric type under `p_elem`.

        Argument `y_type` is a YANG numeric type identifier and
        `ranges` is a list of range restrictions. If `ranges` contains
        more than one interval, multiple <data> elements have to be
        combined in a <choice> where each <data> element specifies one
        interval.
        """
        r_type = self.datatype_map[y_type]
        if len(ranges) == 0:
            ET.SubElement(p_elem, "data", type=r_type)
            return
        if len(ranges) > 1:
            p_elem = ET.SubElement(p_elem, "choice")
        for r in ranges:
            d_elem = ET.SubElement(p_elem, "data", type=r_type)
            self.numeric_restriction(r, d_elem)

    def string_data(self, lengths, patterns, p_elem):
        """Create <data> element with string type under `p_elem`.

        Argument `lengths` is a list of range restrictions and
        `patterns` list of regex patterns. If `lengths` contains more
        than one interval, multiple <data> elements have to be
        combined in a <choice> where each <data> element specifies
        together one interval and all patterns.
        """
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
            self.string_restriction(l, pat_els, d_elem)

    def numeric_restriction(self, range_, p_elem):
        """Create numeric range restriction for `p_elem`.

        Argument `range_` is a single range interval (pair).
        """
        if range_[0] != "min":
            elem = ET.SubElement(p_elem, "param", name="minInclusive")
            elem.text = str(range_[0])
        if range_[1] != "max":
            elem = ET.SubElement(p_elem, "param", name="maxInclusive")
            if range_[1] is None:
                elem.text = str(range_[0])
            else:
                elem.text = str(range_[1])

    def string_restriction(self, len_, pat_els, p_elem):
        """Create string restriction(s) for `p_elem`.

        Argument `len_` is a single length interval and `pat_els` is a
        list of patterns that will be combined with the length facets.
        """
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

    def insert_doc(self, p_elem, docstring):
        """Add <a:documentation> with `docstring` to `p_elem`."""
        dtag = self.namespaces[self.a_uri] + ":documentation"
        elem = ET.Element(dtag)
        elem.text = docstring
        pos = 0
        for ch in p_elem:
            if ch.tag == dtag: pos += 1
        p_elem.insert(pos, elem)


    def is_mandatory(self, stmt):
        """Is `stmt` is mandatory?

        This test is done without the outer context, so additional
        checks may be necessary, e.g., whether a leaf is a list key.
        This recursive function is used only for containers.
        """
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
        elif stmt.keyword == "choice":
            return stmt.search_one("mandatory", "true") is not None
        else:
            return False
        for sub in stmt.substmts:
            if self.is_mandatory(sub): return True
        return False

    def complete_case(self, stmt):
        """Is `stmt` a complete case in a choice?"""
        return (stmt.parent.keyword == "choice" or
                stmt.parent.keyword == "case" and
                len([sub for sub in stmt.parent.substmts
                     if sub.keyword in self.data_nodes]) == 1)

    def min_max(self, slist):
        """Return value pair (min-elements, max-elements).

        Value -1 signals absence of the corresponding restriction and
        -2 for max-elements means 'unbounded'.
        """
        min_el = max_el = -1
        for st in slist:
            if min_el == -1 and st.keyword == "min-elements":
                min_el = int(st.arg)
            if max_el == -1 and st.keyword == "max-elements":
                if st.arg == "unbounded":
                    max_el = -2
                else:
                    max_el = int(st.arg)
            if min_el != -1 and max_el != -1: break
        return (min_el, max_el)

    def strip_local_prefix(self, stmt, qname):
        """Strip local prefix of `stmt` from `qname` and return the result."""
        pref, colon, name = qname.partition(":")
        if colon and pref == stmt.i_module.i_prefix:
            return name
        else:
            return qname

    def check_default_case(self, stmt, p_elem):
        """Check whether `stmt` is the default short case of a choice."""
        if ("nma:default" in p_elem.attrib and stmt.arg ==
            self.strip_local_prefix(stmt, p_elem.attrib["nma:default"])):
            grp = ET.SubElement(p_elem, "group")
            grp.attrib["nma:default-case"] = "true"
            del p_elem.attrib["nma:default"]
            return grp
        return p_elem

    def handle_ref(self, dstmt):
        """Install definition for `dstmt` if it's not there yet ."""
        uname = self.unique_def_name(dstmt)
        if uname not in self.used_defs:
            self.used_defs.append(uname)
            elem = ET.SubElement(self.grammar_elem, "define", name=uname)
            self.handle_substmts(dstmt, elem)
        return uname

    def handle_extension(self, stmt, p_elem):
        """Append YIN representation of `stmt`."""
        ext = stmt.i_extension
        prefix = stmt.raw_keyword[0]
        if prefix in self.prefix_map:
            prefix = self.prefix_map[prefix]
        else:
            if ext.i_module.keyword == 'module':
                ns = ext.i_module.search_one("namespace").arg
            else:
                parentname = ext.i_module.search_one('belongs-to').arg
                parentm = self.module.i_ctx.modules[parentname]
                ns = parentm.search_one('namespace').arg
            prefix = self.add_namespace(ns, prefix)
        eel = ET.SubElement(p_elem, prefix + ":" + stmt.raw_keyword[1])
        argst = ext.search_one("argument")
        if argst:
            if argst.search_one("yin-element", "true"):
                ET.SubElement(eel, prefix + ":" + argst.arg).text = stmt.arg
            else:
                eel.attrib[argst.arg] = stmt.arg
        self.handle_substmts(stmt, eel)

    def declare_namespaces(self):
        """Declare namespace contained in `self.namespaces`."""
        for uri in self.namespaces:
            self.grammar_elem.attrib["xmlns:" + self.namespaces[uri]] = uri

    def handle_stmt(self, stmt, p_elem, pset={}):
        """
        Run handler method for `stmt` in the context of `p_elem`.

        All handler methods are defined below and have the same
        arguments. They should create the schema fragment
        corresponding to `stmt`, apply all patches from `pset`
        belonging to `stmt`, insert the fragment under `p_elem` and
        perform all side effects as necessary.
        """
        if self.debug > 0:
            sys.stderr.write("Handling '%s %s'\n" %
                             (util.keyword_to_str(stmt.raw_keyword), stmt.arg))
        try:
            method = self.stmt_handler[stmt.keyword]
        except KeyError:
            if isinstance(stmt.keyword, tuple): # extension
                self.handle_extension(stmt, p_elem)
            else:
                sys.stderr.write("Unknown keyword %s (this should not happen)\n"
                                 % stmt.keyword)
                sys.exit(1)
        method(stmt, p_elem, pset)

    def handle_substmts(self, stmt, p_elem, pset={}):
        """Handle all substatements of `stmt`."""
        for sub in stmt.substmts:
            self.handle_stmt(sub, p_elem, pset)

    # Handlers for YANG statements

    def noop(self, stmt, p_elem, pset=''):
        """`stmt` is not handled in the regular way."""
        pass

    def anyxml_stmt(self, stmt, p_elem, pset):
        p_elem = self.check_default_case(stmt, p_elem)
        if not self.has_anyxml:
            # install definition
            def_ = ET.fromstring(self.anyxml_def)
            self.grammar_elem.append(def_)
            self.has_anyxml = True
        elem = ET.Element("element", name=self.prefix+":"+stmt.arg)
        is_mand = stmt.search_one("mandatory", "true")
        for p in pset.pop(stmt.arg, []):
            is_mand = p.decide_mandatory(is_mand)
            for st in p.slist: self.handle_stmt(st, elem)
        if not (is_mand or self.complete_case(stmt)):
            p_elem = ET.SubElement(p_elem, "optional")
        p_elem.append(elem)
        ET.SubElement(elem, "ref", name="__anyxml__")
        self.handle_substmts(stmt, elem)

    def nma_attribute(self, stmt, p_elem, pset=None):
        """Map `stmt` to NETMOD-specific attribute."""
        att = "nma:" + stmt.keyword
        if att not in p_elem.attrib:
            p_elem.attrib[att] = stmt.arg

    def case_stmt(self, stmt, p_elem, pset):
        elem = ET.SubElement(p_elem, "group")
        if ("nma:default" in p_elem.attrib and stmt.arg ==
            self.strip_local_prefix(stmt, p_elem.attrib["nma:default"])):
            elem.attrib["nma:default-case"] = "true"
            del p_elem.attrib["nma:default"]
        new_pset = {}
        todo = []
        for p in pset.pop(stmt.arg, []):
            if p.path:
                self.sift_pset(new_pset, p)
            else:
                todo = p.slist
        for st in todo: self.handle_stmt(st, elem, new_pset)
        self.handle_substmts(stmt, elem, new_pset)

    def choice_stmt(self, stmt, p_elem, pset):
        elem = ET.Element("choice")
        is_mand = stmt.search_one("mandatory", "true")
        new_pset = {}
        todo = []
        for p in pset.pop(stmt.arg, []):
            if p.path:
                cid = self.sift_pset(new_pset, p)
                if not stmt.search_one("case", arg=cid):
                    for p in new_pset[cid]: p.pop()
            else:
                todo = p.slist
                is_mand = p.decide_mandatory(is_mand)
        if not is_mand: p_elem = ET.SubElement(p_elem, "optional")
        p_elem.append(elem)
        for st in todo: self.handle_stmt(st, elem, new_pset)
        self.handle_substmts(stmt, elem, new_pset)
        
    def container_stmt(self, stmt, p_elem, pset):
        p_elem = self.check_default_case(stmt, p_elem)
        elem = ET.Element("element", name=self.prefix+":"+stmt.arg)
        is_opt = not self.is_mandatory(stmt)
        new_pset = {}
        todo = []
        for p in pset.pop(stmt.arg, []):
            if p.path:
                self.sift_pset(new_pset, p)
            else:
                todo = p.slist
                is_opt = is_opt or p.has("presence")
        if is_opt and not self.complete_case(stmt):
            p_elem = ET.SubElement(p_elem, "optional")
        p_elem.append(elem)
        for st in todo: self.handle_stmt(st, elem, new_pset)
        self.handle_substmts(stmt, elem, new_pset)

    def description_stmt(self, stmt, p_elem, pset):
        # ignore imported and top-level descriptions + desc. of enum
        if (self.a_uri in self.namespaces and
            stmt.i_module == self.module != stmt.parent and
            stmt.parent.keyword != "enum"):
            self.insert_doc(p_elem, stmt.arg)

    def enum_stmt(self, stmt, p_elem, pset):
        elem = ET.SubElement(p_elem, "value")
        elem.text = stmt.arg
        for sub in stmt.search("status"):
            self.handle_stmt(sub, elem)

    def include_stmt(self, stmt, p_elem, pset):
        subm = self.module.i_ctx.modules[stmt.arg]
        self.handle_substmts(subm, p_elem)

    def leaf_stmt(self, stmt, p_elem, pset):
        p_elem = self.check_default_case(stmt, p_elem)
        elem = ET.Element("element", name=self.prefix+":"+stmt.arg)
        is_mand = stmt.search_one("mandatory", "true")
        for p in pset.pop(stmt.arg, []):
            is_mand = p.decide_mandatory(is_mand)
            for st in p.slist: self.handle_stmt(st, elem)
        if not (is_mand or self.complete_case(stmt) or
                stmt.arg in p_elem.attrib.get("nma:key",[])):
            p_elem = ET.SubElement(p_elem, "optional")
        p_elem.append(elem)
        self.handle_substmts(stmt, elem)

    def leaf_list_stmt(self, stmt, p_elem, pset):
        p_elem = self.check_default_case(stmt, p_elem)
        elem = ET.Element("element", name=self.prefix+":"+stmt.arg)
        min_el, max_el = self.min_max(stmt.substmts)
        new_pset = {}
        for p in pset.pop(stmt.arg, []):
            mi, ma = self.min_max(p.slist)
            if mi >= 0: min_el = mi
            if ma >= 0: max_el = ma
            for st in p.slist: self.handle_stmt(st, elem)
        if min_el <= 0 and not self.complete_case(stmt):
            rng_card = "zeroOrMore"
        else:
            rng_card = "oneOrMore"
        cont = ET.SubElement(p_elem, rng_card)
        if min_el > 1:
            elem.attrib["nma:min-elements"] = str(min_el)
        if max_el > -1:
            elem.attrib["nma:max-elements"] = str(max_el)
        cont.append(elem)
        self.handle_substmts(stmt, elem, new_pset)

    def list_stmt(self, stmt, p_elem, pset):
        p_elem = self.check_default_case(stmt, p_elem)
        elem = ET.Element("element", name=self.prefix+":"+stmt.arg)
        keyst = stmt.search_one("key")
        if keyst:               # also add local prefix
            elem.attrib['nma:key'] = ' '.join(
                [self.prefix_desc_nodeid(k) for k in keyst.arg.split()])
        min_el, max_el = self.min_max(stmt.substmts)
        new_pset = {}
        todo = []
        for p in pset.pop(stmt.arg, []):
            if p.path:
                self.sift_pset(new_pset, p)
            else:
                todo = p.slist
                mi, ma = self.min_max(p.slist)
                if mi >= 0: min_el = mi
                if ma >= 0: max_el = ma
        if min_el <= 0 and not self.complete_case(stmt):
            rng_card = "zeroOrMore"
        else:
            rng_card = "oneOrMore"
        cont = ET.SubElement(p_elem, rng_card)
        if min_el > 1:
            elem.attrib["nma:min-elements"] = str(min_el)
        if max_el > -1:
            elem.attrib["nma:max-elements"] = str(max_el)
        cont.append(elem)
        for st in todo: self.handle_stmt(st, elem, new_pset)
        self.handle_substmts(stmt, elem, new_pset)

    def must_stmt(self, stmt, p_elem, pset):
        mel = ET.SubElement(p_elem, "nma:must")
        mel.attrib["assert"] = stmt.arg
        em = stmt.search_one("error-message")
        if em:
            ET.SubElement(mel, "nma:error-message").text = em.arg
        eat = stmt.search_one("error-app-tag")
        if eat:
            ET.SubElement(mel, "nma:error-app-tag").text = eat.arg

    def notification_stmt(self, stmt, p_elem, pset):
        notel = self.new_element(self.notifications, "notification",
                                prefix="nmt")
        elem = self.new_element(notel, stmt.arg)
        self.handle_substmts(stmt, elem)

    def output_stmt(self, stmt, p_elem, pset):
        elem = self.new_element(p_elem, "output", prefix="nmt")
        self.handle_substmts(stmt, elem)

    def reference_stmt(self, stmt, p_elem, pset):
        # ignore imported and top-level descriptions + desc. of enum
        if (self.a_uri in self.namespaces and
            stmt.i_module == self.module != stmt.parent and
            stmt.parent.keyword != "enum"):
            self.insert_doc(p_elem, "See: " + stmt.arg)

    def rpc_stmt(self, stmt, p_elem, pset):
        rpcel = self.new_element(self.rpcs, "rpc-method", prefix="nmt")
        inpel = self.new_element(rpcel, "input", prefix="nmt")
        elem = self.new_element(inpel, stmt.arg)
        ist = stmt.search_one("input")
        if ist: self.handle_substmts(ist, elem)
        self.handle_substmts(stmt, rpcel)

    def type_stmt(self, stmt, p_elem, pset):
        """Handle ``type`` statement.

        Built-in types are handled by a specific type callback method
        defined below.
        """
        typedef = stmt.i_typedef
        if typedef is None: # built-in type
            self.type_handler[stmt.arg](stmt, p_elem)
        elif stmt.i_is_derived: # derived with restrictions
            self.unwind_type(stmt, p_elem)
        else:                   # just refer to type def.
            uname = self.handle_ref(typedef)
            ET.SubElement(p_elem, "ref", name=uname)

    def unique_stmt(self, stmt, p_elem, pset):
        p_elem.attrib["nma:unique"] = ' '.join(
            [self.prefix_desc_nodeid(nid) for nid in stmt.arg.split()])

    def uses_stmt(self, stmt, p_elem, pset):
        noexpand = True
        for sub in stmt.substmts:
            if sub.keyword in ("refine", "augment"):
                noexpand = False
                self.add_patch(pset, Patch(sub, prefix=self.prefix))
        if noexpand and pset:
            for nid in pset:
                if [ s for s in stmt.i_grouping.substmts if s.arg == nid
                     and s.keyword in self.data_nodes + ("choice",) ]:
                    noexpand = False
                    break
        if noexpand:
            uname = self.handle_ref(stmt.i_grouping)
            ET.SubElement(p_elem, "ref", name=uname)
        else:
            self.handle_substmts(stmt.i_grouping, p_elem, pset)

    def yang_version_stmt(self, stmt, p_elem, pset):
        if float(stmt.arg) != self.YANG_version:
            print >> sys.stderr, "Unsupported YANG version: %s" % stmt.arg
            sys.exit(1)

    # Handlers for YANG types

    def unwind_type(self, stmt, p_elem):
        """Unwind type formed by multiple derivations."""
        patterns = []
        lengths = []
        ranges = []
        while 1:
            patterns.extend([p.arg for p in stmt.search("pattern")])
            if stmt.i_lengths:
                lengths[0:0] = [[list(lc) for lc in stmt.i_lengths]]
            if stmt.i_ranges:
                ranges[0:0] = [[list(rc) for rc in stmt.i_ranges]]
            if stmt.i_typedef is None: break
            stmt = stmt.i_typedef.search_one("type")
        if stmt.arg == "string":
            slen = self.summarize_ranges(lengths)
            self.string_data(slen, patterns, p_elem)
        else:
            srang = self.summarize_ranges(ranges)
            self.numeric_data(stmt.arg, srang, p_elem)

    def bits_type(self, stmt, p_elem):
        elem = ET.SubElement(p_elem, "list")
        for bit in stmt.search("bit"):
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
        self.numeric_data(stmt.arg, stmt.i_ranges, p_elem)

    def string_type(self, stmt, p_elem):
        patterns = [p.arg for p in stmt.search("pattern")]
        self.string_data(stmt.i_lengths, patterns, p_elem)
