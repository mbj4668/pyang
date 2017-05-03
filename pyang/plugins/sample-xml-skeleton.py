# Copyright (c) 2014 by Ladislav Lhotka, CZ.NIC <lhotka@nic.cz>
#
# Pyang plugin generating a sample XML instance document..
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

"""sample-xml-skeleton output plugin

This plugin takes a YANG data model and generates an XML instance
document containing sample elements for all data nodes.

* An element is present for every leaf, container or anyxml.

* At least one element is present for every leaf-list or list. The
  number of entries in the sample is min(1, min-elements).

* For a choice node, sample element(s) are present for each case.

* Leaf, leaf-list and anyxml elements are empty (exception:
  --sample-xml-skeleton-defaults option).
"""

import os
import sys
import optparse
import xml.etree.ElementTree as ET
import copy

from pyang import plugin, statements, error
from pyang.util import unique_prefixes

def pyang_plugin_init():
    plugin.register_plugin(SampleXMLSkeletonPlugin())

class SampleXMLSkeletonPlugin(plugin.PyangPlugin):

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--sample-xml-skeleton-doctype",
                                 dest="doctype",
                                 default="data",
                                 help="Type of sample XML document " +
                                 "(data or config)."),
            optparse.make_option("--sample-xml-skeleton-defaults",
                                 action="store_true",
                                 dest="sample_defaults",
                                 default=False,
                                 help="Insert leafs with defaults values."),
            optparse.make_option("--sample-xml-skeleton-annotations",
                                 action="store_true",
                                 dest="sample_annots",
                                 default=False,
                                 help="Add annotations as XML comments."),
            optparse.make_option("--sample-xml-skeleton-path",
                                 dest="sample_path",
                                 help="Subtree to print"),
            ]
        g = optparser.add_option_group(
            "Sample-xml-skeleton output specific options")
        g.add_options(optlist)
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['sample-xml-skeleton'] = self

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        """Main control function.

        Set up the top-level parts of the sample document, then process
        recursively all nodes in all data trees, and finally emit the
        sample XML document.
        """
        if ctx.opts.sample_path is not None:
            path = ctx.opts.sample_path.split('/')
            if path[0] == '':
                path = path[1:]
        else:
            path = []

        for (epos, etag, eargs) in ctx.errors:
            if error.is_error(error.err_level(etag)):
                raise error.EmitError(
                    "sample-xml-skeleton plugin needs a valid module")
        self.doctype = ctx.opts.doctype
        if self.doctype not in ("config", "data"):
            raise error.EmitError("Unsupported document type: %s" %
                                  self.doctype)
        self.annots = ctx.opts.sample_annots
        self.defaults = ctx.opts.sample_defaults
        self.node_handler = {
            "container": self.container,
            "leaf": self.leaf,
            "anyxml": self.anyxml,
            "choice": self.process_children,
            "case": self.process_children,
            "list": self.list,
            "leaf-list": self.leaf_list,
            "rpc": self.ignore,
            "action": self.ignore,
            "notification": self.ignore
            }
        self.ns_uri = {}
        for yam in modules:
            self.ns_uri[yam] = yam.search_one("namespace").arg
        self.top = ET.Element(self.doctype,
                         {"xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0"})
        tree = ET.ElementTree(self.top)
        for yam in modules:
            self.process_children(yam, self.top, None, path)
        if sys.version > "3":
            tree.write(fd, encoding="unicode", xml_declaration=True)
        elif sys.version > "2.7":
            tree.write(fd, encoding="UTF-8", xml_declaration=True)
        else:
            tree.write(fd, encoding="UTF-8")

    def ignore(self, node, elem, module, path):
        """Do nothing for `node`."""
        pass

    def process_children(self, node, elem, module, path):
        """Proceed with all children of `node`."""
        for ch in node.i_children:
            if ch.i_config or self.doctype == "data":
                self.node_handler[ch.keyword](ch, elem, module, path)

    def container(self, node, elem, module, path):
        """Create a sample container element and proceed with its children."""
        nel, newm, path = self.sample_element(node, elem, module, path)
        if path is None:
            return
        if self.annots:
            pres = node.search_one("presence")
            if pres is not None:
                nel.append(ET.Comment(" presence: %s " % pres.arg))
        self.process_children(node, nel, newm, path)

    def leaf(self, node, elem, module, path):
        """Create a sample leaf element."""
        if node.i_default is None:
            nel, newm, path = self.sample_element(node, elem, module, path)
            if path is None:
                return
            if self.annots:
                nel.append(ET.Comment(" type: %s " % node.search_one("type").arg))
        elif self.defaults:
            nel, newm, path = self.sample_element(node, elem, module, path)
            if path is None:
                return
            nel.text = str(node.i_default)

    def anyxml(self, node, elem, module, path):
        """Create a sample anyxml element."""
        nel, newm, path = self.sample_element(node, elem, module, path)
        if path is None:
            return
        if self.annots:
            nel.append(ET.Comment(" anyxml "))

    def list(self, node, elem, module, path):
        """Create sample entries of a list."""
        nel, newm, path = self.sample_element(node, elem, module, path)
        if path is None:
            return
        self.process_children(node, nel, newm, path)
        minel = node.search_one("min-elements")
        self.add_copies(node, elem, nel, minel)
        self.list_comment(node, nel, minel)

    def leaf_list(self, node, elem, module, path):
        """Create sample entries of a leaf-list."""
        nel, newm, path = self.sample_element(node, elem, module, path)
        if path is None:
            return
        minel = node.search_one("min-elements")
        self.add_copies(node, elem, nel, minel)
        self.list_comment(node, nel, minel)

    def sample_element(self, node, parent, module, path):
        """Create element under `parent`.

        Declare new namespace if necessary.
        """
        if path is None:
            return parent, module, None
        elif path == []:
            # GO ON
            pass
        else:
            if node.arg == path[0]:
                path = path[1:]
            else:
                return parent, module, None

        res = ET.SubElement(parent, node.arg)
        mm = node.main_module()
        if mm != module:
            res.attrib["xmlns"] = self.ns_uri[mm]
            module = mm
        return res, module, path

    def add_copies(self, node, parent, elem, minel):
        """Add appropriate number of `elem` copies to `parent`."""
        rep = 0 if minel is None else int(minel.arg) - 1
        for i in range(rep):
            parent.append(copy.deepcopy(elem))

    def list_comment(self, node, elem, minel):
        """Add list annotation to `elem`."""
        if not self.annots: return
        lo = "0" if minel is None else minel.arg
        maxel = node.search_one("max-elements")
        hi = "" if maxel is None else maxel.arg
        elem.insert(0, ET.Comment(" # entries: %s..%s " % (lo,hi)))

