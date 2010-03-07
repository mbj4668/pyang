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

import pyang
from pyang import plugin, statements, error

from schemanode import SchemaNode

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
    schema = ConceptualTreeSchema().from_modules((module,),
                                  ctx.opts.cts_no_dublin_core,
                                  ctx.opts.cts_no_documentation,
                                  ctx.opts.cts_record_defs, debug=0)
    fd.write(schema.serialize())

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

    def combine(self, patch):
        """Add `patch.slist` to `self.slist`; avoid duplication."""
        exclusive = set(["config", "default", "mandatory", "presence",
                     "min-elements", "max-elements"])
        kws = set([s.keyword for s in self.slist]) & exclusive
        add = [n for n in patch.slist if n.keyword not in kws]
        self.slist.extend(add)

class ConceptualTreeSchema(object):

    YANG_version = 1
    """Checked against the yang-version statement, if present."""

    dc_uri = "http://purl.org/dc/terms"
    """Dublin Core URI"""
    a_uri =  "http://relaxng.org/ns/compatibility/annotations/1.0"
    """DTD compatibility annotattions URI"""

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
        "decimal64": "decimal",
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

    schema_nodes = data_nodes + ("choice", "case")

    def __init__(self):
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
            "default": self.noop,
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
            "when" : self.when_stmt,
            "yang-version": self.yang_version_stmt,
        }
        self.type_handler = {
            "boolean": self.mapped_type,
            "binary": self.binary_type,
            "bits": self.bits_type,
            "decimal64": self.numeric_type,
            "enumeration": self.choice_type,
            "empty": self.empty_type,
            "identityref": self.identityref_type,
            "instance-identifier": self.mapped_type,
            "int8": self.numeric_type,
            "int16": self.numeric_type,
            "int32": self.numeric_type,
            "int64": self.numeric_type,
            "leafref": self.leafref_type,
            "string" : self.string_type,
            "uint8": self.numeric_type,
            "uint16": self.numeric_type,
            "uint32": self.numeric_type,
            "uint64": self.numeric_type,
            "union": self.choice_type,
        }

    def serialize(self):
        """Return the string representation of the receiver."""
        res = '<?xml version="1.0" encoding="UTF-8"?>'
        self.grammar_elem.attr["xmlns"] = \
            "http://relaxng.org/ns/structure/1.0"
        self.grammar_elem.attr["datatypeLibrary"] = \
            "http://www.w3.org/2001/XMLSchema-datatypes"
        for ns in self.namespaces:
            self.grammar_elem.attr["xmlns:" + self.namespaces[ns]] = ns
        res += self.grammar_elem.start_tag()
        for ch in self.grammar_elem.children:
            res += ch.serialize()
        if not self.no_data:
            res += "<start>" + self.root.serialize() + "</start>"
        for d in self.defs:
            res += self.defs[d].serialize()
        if self.has_anyxml:
            res += self.anyxml_def
        return res + self.grammar_elem.end_tag()

    def from_modules(self, modules, no_dc=False, no_a=False, record_defs=False,
                  debug=0):
        self.namespaces = {
            "urn:ietf:params:xml:ns:netmod:conceptual-tree:1" : "nmt",
            "urn:ietf:params:xml:ns:netmod:dsdl-annotations:1" : "nma",
        }
        if not no_dc: self.namespaces[self.dc_uri] = "dc"
        if not no_a: self.namespaces[self.a_uri] = "a"
        self.defs = {}
        self.has_anyxml = False
        self.in_rpc = False
        self.no_data = True
        self.debug = debug
        self.module_prefixes = {}
        for module in modules:
            ns = module.search_one("namespace").arg
            pref = module.search_one("prefix").arg
            self.add_namespace(ns, pref)
            self.module_prefixes[module.arg] = pref
        self.grammar_elem = SchemaNode("grammar")
        for module in modules:
            self.module = module
            src_text = "YANG module '%s'" % module.arg
            revs = module.search("revision")
            if len(revs) > 0:
                src_text += " revision %s" % self.current_revision(revs)
            self.dc_element("source", src_text)
            if record_defs: self.preload_defs()
            if self.has_data_node(module):
                if self.no_data:
                    self.no_data = False
                    self.create_roots()
                ns = self.module.search_one("namespace").arg
                self.prefix = self.module_prefixes[module.arg]
                self.handle_substmts(module, self.confdata)
        self.handle_empty()
        self.dc_element("creator",
                        "Pyang %s, CTS plugin" % pyang.__version__)
        return self

    def create_roots(self):
        """Create root elements for conf. data, RPCs and notifications."""
        self.root = SchemaNode.element("nmt:netmod-tree",
                                       interleave=False, occur=2)
        self.confdata = SchemaNode.element("nmt:top", self.root,
                                           interleave=True, occur=2)
        self.rpcs = SchemaNode.element("nmt:rpc-methods", self.root,
                                       interleave=False, occur=2)
        self.notifications = SchemaNode.element("nmt:notifications", self.root,
                                                interleave=True, occur=2)

    def yang_to_xpath(self, xpath):
        """Transform `xpath` by adding local NS prefixes.

        Prefixes are only added to unqualified node names.
        """
        state = 0
        result = ""
        for c in xpath:
            if state == 0:      # everything except below
                if c.isalpha() or c == "_":
                    state = 1
                    name = c
                elif c == "'":
                    state = 2
                    result += c
                elif c == '"':
                    state = 3
                    result += c
                else:
                    result += c
            elif state == 1:    # inside name
                if c.isalnum() or c in "_-.:":
                    name += c
                elif c == "(":  # function
                    state = 0
                    result += name + c
                else:
                    state = 0
                    if ":" not in name: result += self.prefix + ":"
                    result += name + c
            elif state == 2:    # single-quoted string
                if c == "'":
                    state = 0
                    result += c
                else:
                    result += c
            elif state == 3:    # double-quoted string
                if c == '"':
                    state = 0
                    result += c
                else:
                    result += c
        if state == 1:
            if ":" not in name: result += self.prefix + ":"
            result += name
        return result

    def add_namespace(self, uri, prefix):
        """Add new item `uri`:`prefix` to `self.namespaces`.

        The prefix to be actually used for `uri` is returned.  If the
        namespace is already known, the old prefix is used.
        Prefix clashes are resolved by disambiguating `prefix`.
        """
        if uri not in self.namespaces:
            end = 1
            new = prefix
            while new in self.namespaces.values():
                new = "%s%x" % (prefix,end)
                end += 1
            self.namespaces[uri] = new
            return new
        return self.namespaces[uri]

    def prefix_to_ns(self, prefix):
        """Return NS URI for `prefix` in the current context."""
        defin = self.module.i_ctx.get_module(
            self.module.i_prefixes[prefix][0])
        return defin.search_one("namespace").arg

    def preload_defs(self):
        """Preload all top-level definitions."""
        for d in (self.module.search("grouping") +
                  self.module.search("typedef")):
            self.install_def(self.unique_def_name(d))

    def prefix_id(self, name):
        """Add local prefix to `name`, it it doesn't have any prefix."""
        if ":" in name: return name
        return self.prefix + ":" + name

    def prefix_desc_nodeid(self, nodeid):
        """Add local prefix to all components of `nodeid`."""
        return "/".join([self.prefix_id(c) for c in nodeid.split("/")])

    def handle_empty(self):
        """Handle empty subtree(s) of conceptual tree.

        If any of the subtrees of the conceptual tree is empty, put
        <empty/> as its content.
        """
        if self.no_data: return
        for subtree in (self.confdata, self.rpcs, self.notifications):
            if len(subtree.children) == 0:
                SchemaNode("empty", subtree)

    def dc_element(self, name, text):
        """Add DC element `name` containing `text` to <grammar>."""
        if self.dc_uri in self.namespaces:
            dcel = SchemaNode(self.namespaces[self.dc_uri] + ":" + name,
                              text=text)
            self.grammar_elem.children.insert(0,dcel)

    def unique_def_name(self, stmt, pref=""):
        """Answer mangled name of `stmt` (typedef or grouping)."""
        mod = stmt.i_module
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
            elif stmt.keyword == "module" and st.keyword == "include":
                maybe.append(st.i_module.i_ctx.get_module(st.arg))
        for m in maybe:
            if self.has_data_node(m): return True
        return False

    def add_patch(self, pset, patch):
        """Add `patch` to `pset`."""
        car = patch.pop()
        if car in pset:
            sel = [ x for x in pset[car] if patch.path == x.path ]
            if sel:
                sel[0].combine(patch)
            else:
                pset[car].append(patch)
        else:
            pset[car] = [patch]

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

    def insert_doc(self, p_elem, docstring):
        """Add <a:documentation> with `docstring` to `p_elem`."""
        dtag = self.namespaces[self.a_uri] + ":documentation"
        elem = SchemaNode(dtag, text=docstring)
        pos = 0
        for ch in p_elem.children:
            if ch.name == dtag: pos += 1
        p_elem.children.insert(pos, elem)

    def strip_local_prefix(self, stmt, qname):
        """Strip local prefix of `stmt` from `qname` and return the result."""
        pref, colon, name = qname.partition(":")
        if colon and pref == stmt.i_module.i_prefix:
            return name
        else:
            return qname

    def install_def(self, name, dstmt):
        """Install definition `name` representing `dstmt`."""
        delem = SchemaNode.define(name).set_attr("name", name)
        self.defs[name] = delem
        self.handle_substmts(dstmt, delem)

    def handle_extension(self, stmt, p_elem):
        """Append YIN representation of `stmt`."""
        ext = stmt.i_extension
        prf, extkw = stmt.raw_keyword
        prefix = self.add_namespace(self.prefix_to_ns(prf), prf)
        eel = SchemaNode(prefix + ":" + extkw, p_elem)
        argst = ext.search_one("argument")
        if argst:
            if argst.search_one("yin-element", "true"):
                SchemaNode(prefix + ":" + argst.arg, eel, stmt.arg)
            else:
                eel.attr[argst.arg] = stmt.arg
        self.handle_substmts(stmt, eel)

    def propagate_occur(self, node, value):
        """Propagate occurence `value` to `node` and its ancestors."""
        while node.occur < value:
            node.occur = value
            if node.name == "define":
                break
            node = node.parent

    def select_patch(self, pset, name):
        """Select patch for `name` from `pset`.

        Return tuple consisting of the selected patch statement list
        and transformed `pset` in which `name` is removed from the
        paths of all patches.
        """
        new_pset = {}
        local = []
        for p in pset.pop(name, []):
            if p.path:
                new_pset[p.pop()] = [p]
            else:
                local = p.slist
        return (local, new_pset)

    def is_mandatory(self, stmt, slist):
        """Decide whether `stmt` is mandatory."""
        for st in slist:
            if st.keyword == "mandatory":
                return st.arg == "true"
        if stmt.search_one("mandatory", "true"): return True
        return False

    def get_default(self, stmt, slist):
        """Return default value for `stmt`."""
        for s in slist:
            if s.keyword == "default": return s.arg
        dst = stmt.search_one("default")
        if dst: return dst.arg
        return None

    def get_minmax(self, stmt, slist):
        """Return pair (min,max)-elements for `stmt`."""
        minel = maxel = None
        for s in slist:
            if s.keyword == "min-elements":
                minel = s.arg
            elif s.keyword == "max-elements":
                maxel = s.arg
        if minel is None:
            minst = stmt.search_one("min_elements")
            if minst:
                minel = minst.arg
            else:
                minel = "0"
        if maxel is None:
            maxst = stmt.search_one("max_elements")
            if maxst:
                maxel = maxst.arg
        return (minel, maxel)

    def find_leaf(self, stmt, key):
        """Find leaf `key` as a child of `stmt`.

        The search must traverse any uses/grouping and
        leave breadcrumbs at such indirections.
        """
        for sub in stmt.substmts:
            if sub.keyword == "leaf" and sub.arg == key:
                return sub
            elif sub.keyword == "uses":
                grp = sub.i_grouping
                grp.d_uses = sub
                res = self.find_leaf(grp, key)
                if res: return res
        return None

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
                return
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
        self.has_anyxml = True
        elem = SchemaNode.element(self.prefix_id(stmt.arg), p_elem)
        SchemaNode("ref", elem).set_attr("name", "__anyxml__")
        plist = self.select_patch(pset, stmt.arg)[0]
        if p_elem.name == "choice":
            elem.occur = 3
        elif self.is_mandatory(stmt, plist):
                elem.occur = 2
                self.propagate_occur(p_elem, 2)
        for s in plist: self.handle_stmt(s, elem)
        self.handle_substmts(stmt, elem)

    def nma_attribute(self, stmt, p_elem, pset=None):
        """Map `stmt` to NETMOD-specific attribute."""
        att = "nma:" + stmt.keyword
        if att not in p_elem.attr:
            p_elem.attr[att] = stmt.arg

    def case_stmt(self, stmt, p_elem, pset):
        celem = SchemaNode.case(p_elem)
        if p_elem.default_case != stmt.arg:
            celem.occur = 3
        plist, new_pset = self.select_patch(pset, stmt.arg)
        for s in plist: self.handle_stmt(s, celem, new_pset)
        self.handle_substmts(stmt, celem, new_pset)

    def choice_stmt(self, stmt, p_elem, pset):
        chelem = SchemaNode.choice(p_elem)
        plist, new_pset = self.select_patch(pset, stmt.arg)
        if self.is_mandatory(stmt, plist):
            chelem.occur = 2
            self.propagate_occur(chelem.parent, 2)
        else:
            defv = self.get_default(stmt, plist)
            if defv:
                chelem.default_case = defv
            else:
                chelem.occur = 3
        for s in plist: self.handle_stmt(s, chelem, new_pset)
        self.handle_substmts(stmt, chelem, new_pset)
        
    def container_stmt(self, stmt, p_elem, pset):
        celem = SchemaNode.element(self.prefix_id(stmt.arg),p_elem)
        plist, new_pset = self.select_patch(pset, stmt.arg)
        if p_elem.name == "choice":
            if p_elem.default_case != stmt.arg:
                celem.occur = 3
        elif ([ s for s in plist if s.keyword == "presence"] or
            stmt.search_one("presence")):
            celem.occur = 3
        for s in plist: self.handle_stmt(s, celem, new_pset)
        self.handle_substmts(stmt, celem, new_pset)

    def description_stmt(self, stmt, p_elem, pset):
        # ignore imported and top-level descriptions + desc. of enum
        if (self.a_uri in self.namespaces and
            stmt.i_module == self.module != stmt.parent and
            stmt.parent.keyword != "enum"):
            self.insert_doc(p_elem, stmt.arg)

    def enum_stmt(self, stmt, p_elem, pset):
        elem = SchemaNode("value", p_elem, stmt.arg)
        for sub in stmt.search("status"):
            self.handle_stmt(sub, elem)

    def include_stmt(self, stmt, p_elem, pset):
        if stmt.parent.keyword == "module":
            subm = self.module.i_ctx.get_module(stmt.arg)
            self.handle_substmts(subm, p_elem)

    def leaf_stmt(self, stmt, p_elem, pset):
        def handle_default():
            defv = self.get_default(stmt, plist)
            if defv and elem.occur == 0:
                elem.occur = 1
                elem.default = defv
                self.propagate_occur(elem.parent, 1)
        qname = self.prefix_id(stmt.arg)
        elem = SchemaNode.element(qname)
        plist = self.select_patch(pset, stmt.arg)[0]
        p_elem.subnode(elem)
        if p_elem.name == "choice":
            if p_elem.default_case == stmt.arg:
                handle_default()
            else:
                elem.occur = 3
        elif self.is_mandatory(stmt, plist):
            self.propagate_occur(elem, 2)
        else:
            handle_default()
        for s in plist: self.handle_stmt(s, elem)
        self.handle_substmts(stmt, elem)

    def leaf_list_stmt(self, stmt, p_elem, pset):
        lelem = SchemaNode.leaf_list(self.prefix_id(stmt.arg), p_elem)
        plist = self.select_patch(pset, stmt.arg)[0]
        lelem.minEl, lelem.maxEl = self.get_minmax(stmt, plist)
        for s in plist: self.handle_stmt(s, lelem)
        self.handle_substmts(stmt, lelem)

    def list_stmt(self, stmt, p_elem, pset):
        lelem = SchemaNode.list(self.prefix_id(stmt.arg), p_elem)
        plist, new_pset = self.select_patch(pset, stmt.arg)
        lelem.minEl, lelem.maxEl = self.get_minmax(stmt, plist)
        keyst = stmt.search_one("key")
        if keyst:
            lelem.keys = [self.prefix_id(k) for k in keyst.arg.split()]
        for s in plist: self.handle_stmt(s, lelem, new_pset)
        self.handle_substmts(stmt, lelem, new_pset)

    def must_stmt(self, stmt, p_elem, pset):
        mel = SchemaNode("nma:must", p_elem)
        mel.attr["assert"] = self.yang_to_xpath(stmt.arg)
        em = stmt.search_one("error-message")
        if em:
            SchemaNode("nma:error-message", mel, em.arg)
        eat = stmt.search_one("error-app-tag")
        if eat:
            SchemaNode("nma:error-app-tag", mel, eat.arg)

    def notification_stmt(self, stmt, p_elem, pset):
        notel = SchemaNode.element("nmt:notification", self.notifications,
                                   occur=2)
        elem = SchemaNode.element(self.prefix_id(stmt.arg), notel, occur=2)
        plist, new_pset = self.select_patch(pset, stmt.arg)
        for s in plist: self.handle_stmt(s, elem, new_pset)
        self.handle_substmts(stmt, elem, new_pset)

    def output_stmt(self, stmt, p_elem, pset):
        elem = SchemaNode.element("nmt:output", p_elem, occur=2)
        plist, new_pset = self.select_patch(pset, "output")
        for s in plist: self.handle_stmt(s, elem, new_pset)
        self.handle_substmts(stmt, elem, new_pset)

    def reference_stmt(self, stmt, p_elem, pset):
        # ignore imported and top-level descriptions + desc. of enum
        if (self.a_uri in self.namespaces and
            stmt.i_module == self.module != stmt.parent and
            stmt.parent.keyword != "enum"):
            self.insert_doc(p_elem, "See: " + stmt.arg)

    def rpc_stmt(self, stmt, p_elem, pset):
        rpcel = SchemaNode.element("nmt:rpc-method", self.rpcs, occur=2)
        rlist, r_pset = self.select_patch(pset, stmt.arg)
        inpel = SchemaNode.element("nmt:input", rpcel, occur=2)
        elem = SchemaNode.element(self.prefix_id(stmt.arg), inpel, occur=2)
        inst = stmt.search_one("input")
        if inst:
            ilist, i_pset = self.select_patch(r_pset, "input")
            for s in ilist: self.handle_stmt(s, elem, i_pset)
            self.handle_substmts(inst, elem, i_pset)
        for s in rlist: self.handle_stmt(s, elem, r_pset)
        self.handle_substmts(stmt, rpcel, r_pset)

    def type_stmt(self, stmt, p_elem, pset):
        """Handle ``type`` statement.

        Built-in types are handled by a specific type callback method
        defined below.
        """
        typedef = stmt.i_typedef
        if typedef and not stmt.i_is_derived: # just ref
            uname = self.unique_def_name(typedef)
            if uname not in self.defs:
                self.install_def(uname, typedef)
            SchemaNode("ref", p_elem).set_attr("name", uname)
            defst = typedef.search_one("default")
            if defst:
                self.defs[uname].default = defst.arg
                occur = 1
            else:
                occur = self.defs[uname].occur
            if occur > 0: self.propagate_occur(p_elem, occur)
            return
        chain = [stmt]
        tdefault = None
        while typedef:
            type_ = typedef.search_one("type")
            chain.insert(0, type_)
            if tdefault is None:
                tdef = typedef.search_one("default")
                if tdef:
                    tdefault = tdef.arg
            typedef = type_.i_typedef
        if tdefault and p_elem.occur == 0:
            p_elem.default = tdefault
            p_elem.occur = 1
            self.propagate_occur(p_elem.parent, 1)
        self.type_handler[chain[0].arg](chain, p_elem)

    def unique_stmt(self, stmt, p_elem, pset):
        p_elem.attr["nma:unique"] = " ".join(
            [self.prefix_desc_nodeid(nid) for nid in stmt.arg.split()])

    def uses_stmt(self, stmt, p_elem, pset):
        noexpand = True
        for sub in stmt.substmts:
            if sub.keyword in ("refine", "augment"):
                noexpand = False
                self.add_patch(pset, Patch(sub, prefix=self.prefix))
        if noexpand and pset: 
            for nid in pset: # any patch applies to the grouping?
                if [ s for s in stmt.i_grouping.substmts if s.arg == nid
                     and s.keyword in self.data_nodes + ("choice",) ]:
                    noexpand = False
                    break
        if noexpand:
            uname = self.unique_def_name(stmt.i_grouping, pref="_")
            if uname not in self.defs:
                self.install_def(uname, stmt.i_grouping)
            elem = SchemaNode("ref", p_elem).set_attr("name", uname)
            occur = self.defs[uname].occur
            if occur > 0: self.propagate_occur(p_elem, occur)
            self.handle_substmts(stmt, elem)
        else:
            self.handle_substmts(stmt.i_grouping, p_elem, pset)

    def when_stmt(self, stmt, p_elem, pset=None):
        p_elem.attr["nma:when"] = self.yang_to_xpath(stmt.arg)

    def yang_version_stmt(self, stmt, p_elem, pset):
        if float(stmt.arg) != self.YANG_version:
            print >> sys.stderr, "Unsupported YANG version: %s" % stmt.arg
            sys.exit(1)

    # Handlers for YANG types

    def binary_type(self, tchain, p_elem):
        def gen_data():
            return SchemaNode("data").set_attr("type", "base64Binary")
        self.type_with_ranges(tchain, p_elem, "length", gen_data)

    def bits_type(self, tchain, p_elem):
        elem = SchemaNode("list", p_elem)
        for bit in tchain[0].search("bit"):
            optel = SchemaNode("optional", elem)
            SchemaNode("value", optel, bit.arg)

    def choice_type(self, tchain, p_elem):
        """Handle ``enumeration`` and ``union`` types."""
        elem = SchemaNode.choice(p_elem, occur=2)
        self.handle_substmts(tchain[0], elem)

    def empty_type(self, tchain, p_elem):
        SchemaNode("empty", p_elem)

    def identityref_type(self, tchain, p_elem):
        SchemaNode("data", p_elem).set_attr("type", "QName")

    def leafref_type(self, tchain, p_elem):
        stmt = tchain[0]
        self.handle_stmt(stmt.i_type_spec.i_target_node.search_one("type"),
                         p_elem)
        p_elem.attr["nma:leafref"] = self.yang_to_xpath(
            stmt.search_one("path").arg)

    def mapped_type(self, tchain, p_elem):
        """Handle types that are simply mapped to RELAX NG."""
        SchemaNode("data", p_elem).set_attr("type",
                                            self.datatype_map[tchain[0].arg])

    def numeric_type(self, tchain, p_elem):
        """Handle numeric types."""
        typ = tchain[0].arg
        def gen_data():
            elem = SchemaNode("data").set_attr("type", self.datatype_map[typ])
            if typ == "decimal64":
                fd = tchain[0].search_one("fraction-digits").arg
                SchemaNode("param",elem,"19").set_attr("name","totalDigits")
                SchemaNode("param",elem,fd).set_attr("name","fractionDigits")
            return elem
        self.type_with_ranges(tchain, p_elem, "range", gen_data)

    def type_with_ranges(self, tchain, p_elem, rangekw, gen_data):
        """Handle types with 'range' or 'length' restrictions."""
        ranges = self.get_ranges(tchain, rangekw)
        if not ranges: return p_elem.subnode(gen_data())
        if len(ranges) > 1:
            p_elem = SchemaNode.choice(p_elem)
            p_elem.occur = 2
        for r in ranges:
            d_elem = gen_data()
            for p in self.range_params(r, rangekw):
                d_elem.subnode(p)
            p_elem.subnode(d_elem)

    def get_ranges(self, tchain, kw):
        """Return list of `kw` ranges defined in `tchain`."""
        (lo, hi) = ("min", "max")
        ran = None
        for t in tchain:
            rstmt = t.search_one(kw)
            if rstmt is None: continue
            ran = [ i.split("..") for i in rstmt.arg.split("|") ]
            if ran[0][0] != 'min': lo = ran[0][0]
            if ran[-1][-1] != 'max': hi = ran[-1][-1]
        if ran is None: return None
        if len(ran) == 1:
            return [(lo, hi)]
        else:
            return [(lo, ran[0][-1])] + ran[1:-1] + [(ran[-1][0], hi)]

    def range_params(self, ran, kw):
        """Return list of <param>s corresponding to `kw` range `ran`.
        """
        specs = {"range": (SchemaNode("value"),
                           SchemaNode("param").set_attr("name","minInclusive"),
                           SchemaNode("param").set_attr("name","maxInclusive")),
                 "length": (SchemaNode("param").set_attr("name","length"),
                            SchemaNode("param").set_attr("name","minLength"),
                            SchemaNode("param").set_attr("name","maxLength"))}
        (exact, min_, max_) = specs[kw]
        if (len(ran) == 1 or ran[0] == ran[1]) and ran[0][0] != "m":
            elem = exact
            elem.text = ran[0]
            return [elem]
        res = []
        if ran[0][0] != "m":
            elem = min_
            elem.text = ran[0]
            res.append(elem)
        if ran[1][0] != "m":
            elem = max_
            elem.text = ran[1]
            res.append(elem)
        return res

    def string_type(self, tchain, p_elem):
        pels = []
        for t in tchain:
            for pst in t.search("pattern"):
                pels.append(SchemaNode("param",
                                       text=pst.arg).set_attr("name","pattern"))
        def get_data():
            elem = SchemaNode("data").set_attr("type", "string")
            for p in pels: elem.subnode(p)
            return elem
        self.type_with_ranges(tchain, p_elem, "length", get_data)
