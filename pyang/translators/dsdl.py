# Copyright (c) 2009 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>
#                       Martin Bjorklund <mbj@tail-f.com>
#
# Translator of YANG to hybrid DSDL schema
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

"""Translator from YANG to hybrid DSDL schema.

It is designed as a plugin for the pyang program and defines several
new command-line options:

--dsdl-no-documentation
    No output of DTD compatibility documentation annotations

--dsdl-no-dublin-core
    No output of Dublin Core annotations

--dsdl-record-defs
    Record all top-level defs, even if they are not used

Three classes are defined in this module:

* `DSDLPlugin`: pyang plugin interface class

* `DSDLTranslator`: provides instance that preforms the mapping

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
    plugin.register_plugin(DSDLPlugin())

class DSDLPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['dsdl'] = self
    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--dsdl-no-documentation",
                                 dest="dsdl_no_documentation",
                                 action="store_true",
                                 default=False,
                                 help="No output of DTD compatibility"
                                 " documentation annotations"),
            optparse.make_option("--dsdl-no-dublin-core",
                                 dest="dsdl_no_dublin_core",
                                 action="store_true",
                                 default=False,
                                 help="No output of Dublin Core"
                                 " annotations"),
            optparse.make_option("--dsdl-record-defs",
                                 dest="dsdl_record_defs",
                                 action="store_true",
                                 default=False,
                                 help="Record all top-level defs"
                                 " (even if not used)"),
            ]
        g = optparser.add_option_group("Hybrid DSDL schema "
                                       "output specific options")
        g.add_options(optlist)

    def emit(self, ctx, modules, fd):
        if 'submodule' in [ m.keyword for m in modules ]:
            raise error.EmitError("Cannot translate submodules")
        emit_dsdl(ctx, modules, fd)

def emit_dsdl(ctx, modules, fd):
    # No errors are allowed
    for module in modules:
        for (epos, etag, eargs) in ctx.errors:
            if (epos.top_name == module.arg and
                error.is_error(error.err_level(etag))):
                raise error.EmitError("DSDL translation needs a valid module")
    schema = HybridDSDLSchema().from_modules(modules,
                                  ctx.opts.dsdl_no_dublin_core,
                                  ctx.opts.dsdl_no_documentation,
                                  ctx.opts.dsdl_record_defs, debug=0)
    fd.write(schema.serialize())

class Patch(object):

    """Instances of this class represent a patch to the YANG tree.

    A Patch is filled with statements from 'refine' and/or 'augment'
    that must be applied to a single node.

    Instance variables:

    * `path`: list specifying the relative path to the node where the
      patch is to be applied

    * `plist`: list of statements to apply
    """

    def __init__(self, path, refaug):
        """Initialize the instance."""
        self.path = path
        self.plist = [refaug]

    def pop(self):
        """Pop and return the first element of `self.path`."""
        return self.path.pop(0)

    def combine(self, patch):
        """Add `patch.plist` to `self.plist`."""
        exclusive = set(["config", "default", "mandatory", "presence",
                     "min-elements", "max-elements"])
        kws = set([s.keyword for s in self.plist]) & exclusive
        add = [n for n in patch.plist if n.keyword not in kws]
        self.plist.extend(add)

class HybridDSDLSchema(object):

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
        self.top_grammar.attr["xmlns"] = \
            "http://relaxng.org/ns/structure/1.0"
        self.top_grammar.attr["datatypeLibrary"] = \
            "http://www.w3.org/2001/XMLSchema-datatypes"
        for ns in self.namespaces:
            self.top_grammar.attr["xmlns:" + self.namespaces[ns]] = ns
        res += self.top_grammar.start_tag()
        for ch in self.top_grammar.children:
            res += ch.serialize()
        res += "<start>" + self.tree.serialize() + "</start>"
        for d in self.global_defs:
            res += self.global_defs[d].serialize()
        if self.has_anyxml:
            res += self.anyxml_def
        return res + self.top_grammar.end_tag()

    def from_modules(self, modules, no_dc=False, no_a=False, record_defs=False,
                  debug=0):
        self.namespaces = {
            "urn:ietf:params:xml:ns:netmod:hybrid-tree:1" : "nmt",
            "urn:ietf:params:xml:ns:netmod:dsdl-annotations:1" : "nma",
        }
        if not no_dc: self.namespaces[self.dc_uri] = "dc"
        if not no_a: self.namespaces[self.a_uri] = "a"
        self.global_defs = {}
        self.has_anyxml = False
        self.in_rpc = False
        self.debug = debug
        self.module_prefixes = {}
        gpset = {}
        self.gg_level = 0
        for module in modules:
            ns = module.search_one("namespace").arg
            pref = module.search_one("prefix").arg
            self.add_namespace(ns, pref)
            self.module_prefixes[module.arg] = pref
        for module in modules:
            self.module = module
            for aug in module.search("augment"):
                self.add_patch(gpset, aug)
            for sub in [ module.i_ctx.get_module(inc.arg)
                         for inc in module.search("include") ]:
                for aug in sub.search("augment"):
                    self.add_patch(gpset, aug)
        self.setup_top()
        for module in modules:
            self.module = module
            self.local_defs = {}
            self.lists = []
            if record_defs: self.preload_defs()
            self.prefix_stack = [self.module_prefixes[module.arg]]
            self.create_roots(module)
            self.handle_substmts(module, self.data, gpset)
            for d in self.local_defs.values():
                self.local_grammar.subnode(d)
            self.handle_empty()
            for l in self.lists: self.collect_keys(l)
        self.dc_element(self.top_grammar, "creator",
                        "Pyang %s, DSDL plugin" % pyang.__version__)
        return self

    def setup_top(self):
        """Create top-level elements of CTS."""
        self.top_grammar = SchemaNode("grammar")
        self.tree = SchemaNode.element("nmt:netmod-tree",
                                       interleave=True, occur=2)

    def create_roots(self, yam):
        """Create root elements for conf. data, RPCs and notifications."""
        self.local_grammar = SchemaNode("grammar")
        self.local_grammar.attr["ns"] = yam.search_one("namespace").arg
        self.local_grammar.attr["nma:module"] = self.module.arg
        src_text = "YANG module '%s'" % yam.arg
        revs = yam.search("revision")
        if len(revs) > 0:
            src_text += " revision %s" % self.current_revision(revs)
        self.dc_element(self.local_grammar, "source", src_text)
        start = SchemaNode("start", self.local_grammar)
        self.data = SchemaNode.element("nmt:data", start,
                                       interleave=True, occur=2)
        self.rpcs = SchemaNode.element("nmt:rpcs", start,
                                       interleave=False, occur=2)
        self.notifications = SchemaNode.element("nmt:notifications", start,
                                                interleave=True, occur=2)

    def yang_to_xpath(self, xpath):
        """Transform `xpath` by adding local NS prefixes.

        Prefixes are only added to unqualified node names.
        """
        def prefix():
            if self.gg_level: return "$pref:"
            return self.prefix_stack[-1] + ":"
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
                if c.isalnum() or c in "_-.":
                    name += c
                elif c == ":":
                    state = 4
                    name += c
                elif c == "(":  # function
                    state = 0
                    result += name + c
                else:
                    state = 0
                    if ":" not in name: result += prefix()
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
            elif state == 4:    # axis
                if c == ":":
                    state = 0
                    result += name + c
                else:
                    state = 1
                    name += c
        if state == 1:
            if ":" not in name: result += prefix()
            result += name
        return result

    def add_namespace(self, uri, prefix):
        """Add new item `uri`:`prefix` to `self.namespaces`.

        The prefix to be actually used for `uri` is returned.  If the
        namespace is already known, the old prefix is used.
        Prefix clashes are resolved by disambiguating `prefix`.
        """
        if uri in self.namespaces: return self.namespaces[uri]
        end = 1
        new = prefix
        while new in self.namespaces.values():
            new = "%s%x" % (prefix,end)
            end += 1
        self.namespaces[uri] = new
        return new

    def prefix_to_ns(self, prefix):
        """Return NS URI for `prefix` in the current context."""
        defin = self.module.i_ctx.get_module(
            self.module.i_prefixes[prefix][0])
        return defin.search_one("namespace").arg

    def preload_defs(self):
        """Preload all top-level definitions."""
        for d in (self.module.search("grouping") +
                  self.module.search("typedef")):
            uname, dic = self.unique_def_name(d)
            self.install_def(uname, d, dic)

    def add_prefix(self, name, stmt):
        """Return `name` prepended with correct prefix."""
        if self.gg_level: return name
        pref, colon, local = name.partition(":")
        if colon:
            return (self.module_prefixes[stmt.i_module.i_prefixes[pref][0]]
                    + ":" + local)
        else:
            return self.prefix_stack[-1] + ":" + pref

    def qname(self, stmt):
        """Return (prefixed) node name of `stmt`.

        The result is prefixed unless inside a global grouping.
        """
        if self.gg_level: return stmt.arg
        return self.prefix_stack[-1] + ":" + stmt.arg

    def canonic_nodeid(self, nodeid, stmt):
        """Return list containing `nodeid` components with prefixes."""
        return [ self.add_prefix(c, stmt) for c in nodeid.split("/") if c ]

    def handle_empty(self):
        """Handle empty subtree(s) of the hybrid tree.

        If any of the subtrees of the hybrid tree is empty, put
        <empty/> as its content.
        """
        empty = [ s for s in (self.data, self.rpcs, self.notifications)
                  if len(s.children) == 0 ] 
        if len(empty) < 3:
            self.tree.subnode(self.local_grammar)
            for subtree in empty:
                SchemaNode("empty", subtree)

    def dc_element(self, parent, name, text):
        """Add DC element `name` containing `text` to `parent`."""
        if self.dc_uri in self.namespaces:
            dcel = SchemaNode(self.namespaces[self.dc_uri] + ":" + name,
                              text=text)
            parent.children.insert(0,dcel)

    def get_default(self, stmt, refd):
        """Return default value for `stmt` node."""
        if refd["default"]:
                return refd["default"]
        defst = stmt.search_one("default")
        if defst:
            return defst.arg
        return None

    def unique_def_name(self, stmt):
        """Mangle the name of `stmt` (typedef or grouping).

        Return the mangled name and dictionary where the definition is
        to be installed.
        """
        mod = stmt.i_module
        if mod.keyword == "submodule":
            pref = mod.search_one("belongs-to").arg
        else:
            pref = mod.arg
        if stmt.parent.keyword in ("module", "submodule"):
            name = stmt.arg
            defs = self.global_defs
        else:
            name = "__".join(stmt.full_path())
            defs = self.local_defs
        return (pref + "__" + name, defs)

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

    def add_patch(self, pset, augref):
        """Add patch corresponding to `augref` to `pset`."""
        try:
            path = self.canonic_nodeid(augref.arg, augref)
        except KeyError:
            return
        car = path[0]
        patch = Patch(path[1:], augref)
        if car in pset:
            sel = [ x for x in pset[car] if patch.path == x.path ]
            if sel:
                sel[0].combine(patch)
            else:
                pset[car].append(patch)
        else:
            pset[car] = [patch]

    def apply_augments(self, auglist, p_elem, pset):
        """Apply statements from `auglist` as patch."""
        for a in auglist:
            par = a.parent
            if par.keyword == "uses":
                handle_substmts(a, p_elem, pset)
                continue
            if par.keyword == "submodule":
                mnam = par.search_one("belongs-to").arg
            else:
                mnam = par.arg
            if self.prefix_stack[-1] == self.module_prefixes[mnam]:
                handle_substmts(a, p_elem, pset)
            else:
                self.prefix_stack.append(self.module_prefixes[mnam])
                self.handle_substmts(a, p_elem, pset)
                self.prefix_stack.pop()

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

    def install_def(self, name, dstmt, def_map):
        """Install definition `name` representing `dstmt`."""
        delem = SchemaNode.define(name)
        delem.attr["name"] = name
        def_map[name] = delem
        if def_map is self.global_defs: self.gg_level += 1
        self.handle_substmts(dstmt, delem)
        if def_map is self.global_defs: self.gg_level -= 1

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

    def process_patches(self, pset, name, elem):
        """Process patches for node `name` from `pset`.

        Return tuple consisting of the selected patch statement list
        and transformed `pset` in which `name` is removed from the
        paths of all patches.
        """
        new_pset = {}
        augments = []
        refine_dict = dict.fromkeys(("presence", "default", "mandatory",
                                     "min-elements", "max-elements"))
        for p in pset.pop(self.prefix_stack[-1] + ":" + name, []):
            if p.path:
                new_pset[p.pop()] = [p]
            else:
                for refaug in p.plist:
                    if refaug.keyword == "augment":
                        augments.append(refaug)
                    else:
                        for s in refaug.substmts:
                            if s.keyword == "description":
                                self.description_stmt(s, elem, None)
                            elif s.keyword == "reference":
                                self.reference_stmt(s, elem, None)
                            elif s.keyword == "config":
                                self.nma_attribute(s, elem)
                            elif refine_dict.get(s.keyword, False) is None:
                                refine_dict[s.keyword] = s.arg
        return (refine_dict, augments, new_pset)

    def get_minmax(self, stmt, refine_dict):
        """Return pair of (min,max)-elements values for `stmt`."""
        minel = refine_dict["min-elements"]
        maxel = refine_dict["max-elements"]
        if minel is None:
            minst = stmt.search_one("min-elements")
            if minst:
                minel = minst.arg
            else:
                minel = "0"
        if maxel is None:
            maxst = stmt.search_one("max-elements")
            if maxst:
                maxel = maxst.arg
        return (minel, maxel)

    def collect_keys(self, list_):
        """Collect all keys of `list_`."""
        keys = list_.keys[:]
        todo = [list_]
        while 1:
            node = todo.pop()
            refs = []
            for ch in node.children:
                if ch.name == "ref": refs.append(ch)
                elif ch.name == "element" and ch.attr["name"] in keys:
                    k = ch.attr["name"]
                    list_.keymap[k] = ch
                    keys.remove(k)
            if not keys: break
            for r in refs:
                self.local_defs.update(self.global_defs)
                d = self.local_defs[r.attr["name"]]
                d.ref = r
                todo.append(d)
        for k in list_.keymap:
            out = list_.keymap[k]
            in_ = []
            while out.parent != list_:
                chs = out.parent.children[:]
                pos = chs.index(out)
                chs[pos:pos+1] = in_
                in_ = chs
                out = out.parent.ref
            pos = list_.children.index(out)
            list_.children[pos:pos+1] = in_

    def contains_any(self, gstmt, names):
        """Does `gstmt` contain any node with a name from `names`?

        The search is recursive, `gstmt` should be a grouping.
        """
        for sub in gstmt.substmts:
            if sub.keyword in self.schema_nodes and sub.arg in names:
                return True
            elif sub.keyword == "uses":
                if self.contains_any(sub.i_grouping, names):
                    return True
        return False

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
                raise error.EmitError(
                    "Unknown keyword %s (this should not happen)\n"
                    % stmt.keyword)

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
        elem = SchemaNode.element(self.qname(stmt), p_elem)
        SchemaNode("ref", elem).set_attr("name", "__anyxml__")
        refd = self.process_patches(pset, stmt.arg, elem)[0]
        if p_elem.name == "choice":
            elem.occur = 3
        elif refd["mandatory"] or stmt.search_one("mandatory", "true"):
            elem.occur = 2
            self.propagate_occur(p_elem, 2)
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
        refd, augs, new_pset = self.process_patches(pset, stmt.arg, celem)
        self.handle_substmts(stmt, celem, new_pset)
        self.apply_augments(augs, celem, new_pset)

    def choice_stmt(self, stmt, p_elem, pset):
        chelem = SchemaNode.choice(p_elem)
        refd, augs, new_pset = self.process_patches(pset, stmt.arg, chelem)
        if refd["mandatory"] or stmt.search_one("mandatory", "true"):
            chelem.attr["nma:mandatory"] = stmt.arg
            self.propagate_occur(chelem, 2)
        else:
            defv = self.get_default(stmt, refd)
            if defv:
                chelem.default_case = defv
            else:
                chelem.occur = 3
        self.handle_substmts(stmt, chelem, new_pset)
        self.apply_augments(augs, chelem, new_pset)
        
    def container_stmt(self, stmt, p_elem, pset):
        celem = SchemaNode.element(self.qname(stmt), p_elem)
        refd, augs, new_pset = self.process_patches(pset, stmt.arg, celem)
        if (p_elem.name == "choice" and p_elem.default_case != stmt.arg
            or refd["presence"] or stmt.search_one("presence")):
            celem.occur = 3
        self.handle_substmts(stmt, celem, new_pset)
        self.apply_augments(augs, celem, new_pset)

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
        elem = SchemaNode.element(self.qname(stmt), p_elem)
        refd = self.process_patches(pset, stmt.arg, elem)[0]
        if p_elem.name == "choice":
            if p_elem.default_case != stmt.arg:
                elem.occur = 3
        elif refd["mandatory"] or stmt.search_one("mandatory", "true"):
            self.propagate_occur(elem, 2)
        if elem.occur == 0:
            defv = self.get_default(stmt, refd)
            if defv:
                elem.default = defv
                self.propagate_occur(elem, 1)
        self.handle_substmts(stmt, elem)

    def leaf_list_stmt(self, stmt, p_elem, pset):
        lelem = SchemaNode.leaf_list(self.qname(stmt), p_elem)
        lelem.attr["nma:leaf-list"] = "true"
        refd = self.process_patches(pset, stmt.arg, lelem)[0]
        lelem.minEl, lelem.maxEl = self.get_minmax(stmt, refd)
        if int(lelem.minEl) > 0: self.propagate_occur(p_elem, 2)
        self.handle_substmts(stmt, lelem)

    def list_stmt(self, stmt, p_elem, pset):
        lelem = SchemaNode.list(self.qname(stmt), p_elem)
        refd, augs, new_pset = self.process_patches(pset, stmt.arg, lelem)
        lelem.minEl, lelem.maxEl = self.get_minmax(stmt, refd)
        if int(lelem.minEl) > 0: self.propagate_occur(p_elem, 2)
        keyst = stmt.search_one("key")
        if keyst:
            self.lists.append(lelem)
            lelem.keys = [self.add_prefix(k, stmt) for k in keyst.arg.split()]
        self.handle_substmts(stmt, lelem, new_pset)
        self.apply_augments(augs, lelem, new_pset)

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
        elem = SchemaNode.element(self.qname(stmt), notel, occur=2)
        augs, new_pset = self.process_patches(pset, stmt.arg, elem)[1:]
        self.handle_substmts(stmt, elem, new_pset)
        self.apply_augments(augs, elem, new_pset)

    def output_stmt(self, stmt, p_elem, pset):
        elem = SchemaNode.element("nmt:output", p_elem, occur=2)
        augs, new_pset = self.process_patches(pset, "output", elem)[1:]
        self.handle_substmts(stmt, elem, new_pset)
        self.apply_augments(augs, elem, new_pset)

    def reference_stmt(self, stmt, p_elem, pset):
        # ignore imported and top-level descriptions + desc. of enum
        if (self.a_uri in self.namespaces and
            stmt.i_module == self.module != stmt.parent and
            stmt.parent.keyword != "enum"):
            self.insert_doc(p_elem, "See: " + stmt.arg)

    def rpc_stmt(self, stmt, p_elem, pset):
        rpcel = SchemaNode.element("nmt:rpc", self.rpcs, occur=2)
        r_pset = self.process_patches(pset, stmt.arg, rpcel)[2]
        inpel = SchemaNode.element("nmt:input", rpcel, occur=2)
        elem = SchemaNode.element(self.qname(stmt), inpel, occur=2)
        inst = stmt.search_one("input")
        if inst:
            augs, i_pset = self.process_patches(r_pset, "input", elem)[1:]
            self.handle_substmts(inst, elem, i_pset)
            self.apply_augments(augs, elem, i_pset)
        self.handle_substmts(stmt, rpcel, r_pset)

    def type_stmt(self, stmt, p_elem, pset):
        """Handle ``type`` statement.

        Built-in types are handled by a specific type callback method
        defined below.
        """
        typedef = stmt.i_typedef
        if typedef and not stmt.i_is_derived: # just ref
            uname, dic = self.unique_def_name(typedef)
            if uname not in dic:
                self.install_def(uname, typedef, dic)
            SchemaNode("ref", p_elem).set_attr("name", uname)
            defst = typedef.search_one("default")
            if defst:
                dic[uname].default = defst.arg
                occur = 1
            else:
                occur = dic[uname].occur
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
        def addpref(nid):
            return "/".join([self.add_prefix(c, stmt)
                             for c in nid.split("/")])
        p_elem.attr["nma:unique"] = " ".join(
            [addpref(nid) for nid in stmt.arg.split()])

    def uses_stmt(self, stmt, p_elem, pset):
        noexpand = True
        for sub in stmt.substmts:
            if sub.keyword in ("refine", "augment"):
                noexpand = False
                self.add_patch(pset, sub)
        if noexpand and len(self.prefix_stack) > 1:
            noexpand = False
        if noexpand and pset:
            # any patch applies to the grouping?
            noexpand = not self.contains_any(stmt.i_grouping, pset.keys())
        if noexpand:
            uname, dic = self.unique_def_name(stmt.i_grouping)
            gname = "_" + uname
            if uname not in dic:
                self.install_def(gname, stmt.i_grouping, dic)
            elem = SchemaNode("ref", p_elem).set_attr("name", gname)
            occur = dic[gname].occur
            if occur > 0: self.propagate_occur(p_elem, occur)
            self.handle_substmts(stmt, elem)
        else:
            self.handle_substmts(stmt.i_grouping, p_elem, pset)

    def when_stmt(self, stmt, p_elem, pset=None):
        p_elem.attr["nma:when"] = self.yang_to_xpath(stmt.arg)

    def yang_version_stmt(self, stmt, p_elem, pset):
        if float(stmt.arg) != self.YANG_version:
            raise error.EmitError("Unsupported YANG version: %s" % stmt.arg)

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
