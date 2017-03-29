# -*- coding: utf-8 -*-

"""
This plugin translate YANG module into YAML format
"""

from pyang import plugin

def pyang_plugin_init():
    plugin.register_plugin(YAMLPlugin())

class YAMLPlugin(plugin.PyangPlugin):

    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts["yaml"] = self

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        for (epos, etag, eargs) in ctx.errors:
            if error.is_error(error.err_level(etag)):
                raise error.EmitError("YAML plugin needs a valid module")

        for module in modules:
            self.process_children(module,fd)

    def process_children(self, node, fd, indent=0):
        """
        Process all children of `node`, except "rpc" and "notification".
        """
        indentStr = ' ' * indent
        fd.write(indentStr + "- %s:%s" % (node.arg, node.keyword)+"\n")
        indent = indent + 2
        for ch in node.i_children:
            if ch.keyword in ["rpc", "notification"]: continue
            if ch.keyword in ["container", "list", "choice"]:
                self.process_children(ch, fd, indent+2)
            elif ch.keyword in ["leaf", "leaf-list"]:
                fd.write(' ' * indent + "%s: %s" \
                        % (ch.arg, self.base_type(ch.search_one("type")))+"\n")

    def base_type(self, type):
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
            return [type.arg, [self.base_type(x) for x in type.i_type_spec.types]]
        else:
            return type.arg

