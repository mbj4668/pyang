# Copyright (c) 2014 by Ladislav Lhotka, CZ.NIC <lhotka@nic.cz>
#
# Pyang plugin generating a driver file for JSON->XML translation.
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

"""JTOX output plugin

This plugin takes a YANG data model and produces a JSON driver file that can
be used by the *json2xml* script for translating a valid JSON configuration, or config into
XML.
"""

import os
import json

from pyang import plugin, statements, error

mods = {}
"""Dictionary containing module prefixes and URIs.

   Keys are module names, values are pairs [prefix, uri].
"""

def pyang_plugin_init():
    plugin.register_plugin(JtoXPlugin())

class JtoXPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['jtox'] = self

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        emit_jtox(modules, ctx, fd)

def emit_jtox(modules, ctx, fd):
    """Main control function.
    """
    for (epos, etag, eargs) in ctx.errors:
        if error.is_error(error.err_level(etag)):
            raise error.EmitError("JTOX plugin needs a valid module")
    tree = {}
    prefixes = []
    def unique_prefix(p):
        """Disambiguate the module prefix."""
        suffix = 0
        while p == "nc" or p in prefixes:
            p += "%d" % suffix
            suffix += 1
        return p
    for module in modules:
        uri = module.search_one("namespace").arg
        prf = unique_prefix(module.i_prefix)
        prefixes.append(prf)
        mods[module.i_modulename] = [prf, uri]
    for module in modules:
        process_children(module, tree)
    json.dump({"modules": mods, "tree": tree}, fd)

def process_children(node, parent):
    """Process all children of `node`, except "rpc" and "notification".
    """
    for ch in node.i_children:
        if ch.keyword in ["rpc", "notification"]: continue
        if ch.keyword in ["choice", "case"]:
            process_children(ch, parent)
            continue
        ndata = [ch.keyword]
        if ch.keyword == "container":
            ndata.append({})
            process_children(ch, ndata[1])
        elif ch.keyword == "list":
            ndata.append({})
            process_children(ch, ndata[1])
            ndata.append([(k.i_module.i_modulename, k.arg)
                          for k in ch.i_key])
        elif ch.keyword in ["leaf", "leaf-list"]:
            ndata.append(base_type(ch.search_one("type")))
        modname = ch.i_module.i_modulename
        if ch.arg in parent:
            parent[ch.arg][modname] = ndata
        else:
            parent[ch.arg] = {modname: ndata}

def base_type(type):
    """Return the base type of `type`."""
    while 1:
        if type.arg == "leafref":
            node = type.i_type_spec.i_target_node
        elif type.i_typedef is None:
            break
        else:
            node = type.i_typedef
        type = node.search_one("type")
    if type.arg == "decimal64":
        return [type.arg, int(type.search_one("fraction-digits").arg)]
    elif type.arg == "union":
        return [type.arg, [base_type(x) for x in type.i_type_spec.types]]
    else:
        return type.arg

