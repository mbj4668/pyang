"""JSON XSL output plugin

This plugin takes a YANG data model and produces an XSL stylesheet
that translates datastore contents from XML to JSON.
"""

import os
import json

from pyang import plugin
from pyang import statements

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
        emit_jtox(modules, fd)

def emit_jtox(modules, fd):
    """Main control function.
    """
    tree = {}
    prefixes = []
    def unique_prefix(p):
        """Disambiguate the module prefix."""
        suffix = 0
        while p in prefixes:
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
    """Process all children of `node`.
    """
    chs = node.i_children
    for ch in chs:
        if ch.keyword in ["choice", "case"]:
            process_children(ch, parent)
            continue
        ndata = [ch.keyword]
        if ch.keyword in ["container", "list"]:
            ndata.append({})
            process_children(ch, ndata[-1])
        elif ch.keyword in ["leaf", "leaf-list"]:
            ltyp = base_type(ch.search_one("type"))
            ndata.append(ltyp.arg)
            if ltyp.arg == "union":
                ndata.append([base_type(x).arg for x in ltyp.i_type_spec.types])
            elif ltyp.arg == "decimal64":
                ndata.append(int(ltyp.search_one("fraction-digits").arg))
        modname = ch.i_module.i_modulename
        if ch.arg in parent:
            parent[ch.arg][mods[modname][0]] = ndata
        else:
            parent[ch.arg] = {mods[modname][0]: ndata}

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
    return type

