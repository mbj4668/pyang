# -*- coding: utf-8 -*-

"""
This plugin translate YANG module into YAML format http://yaml.org/
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
        fd.write("---" + "\n")
        parent = None
        for module in modules:
            self.process_children(module, parent, fd)

    def process_children(self, node, parent, fd, indent=0):
        """
        Process all children of `node`, except "rpc" and "notification".
        """
        is_indent = False
        if parent == None:
            fd.write(' ' * indent + "%s: " % (node.arg)+"\n")
            indent = indent + 2

        if parent is not None and parent.keyword == "case":
            indent = indent + 2

        for ch in node.i_children:
            if ch.keyword in ["rpc", "notification"]: continue
            if ch.keyword in ["container", "list", "choice", "case"]:
                parent = ch
                fd.write(' ' * indent + "%s: " % (ch.arg)+"\n")
                self.process_children(ch, parent, fd, indent+2)
            elif ch.keyword in ["leaf", "leaf-list"]:
                if hasattr(ch, 'i_is_key'):
                    is_indent = True
                    fd.write(' ' * indent + "- %s:" % ch.arg + "\n")
                    if not is_indent:
                        indent = indent + 2
                elif ch.keyword == "leaf-list":
                    fd.write(' ' * indent + "%s:" % ch.arg + "\n")
                else:
                    if is_indent:
                        indent = indent + 2
                        is_indent = False
                    fd.write(' ' * indent + "%s:" % ch.arg + "\n")

