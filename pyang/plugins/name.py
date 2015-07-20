"""Name output plugin

"""

from pyang import plugin

def pyang_plugin_init():
    plugin.register_plugin(NamePlugin())

class NamePlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['name'] = self

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        emit_name(ctx, modules, fd)

def emit_name(ctx, modules, fd):
    for module in modules:
        bstr = ""
        b = module.search_one('belongs-to')
        if b is not None:
            bstr = " (belongs-to %s)" % b.arg
        fd.write("%s%s\n" % (module.arg, bstr))
