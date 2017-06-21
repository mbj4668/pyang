"""Name@revision output plugin
This has been adapted from the name.py plugin.
"""

from pyang import plugin


def pyang_plugin_init():
    plugin.register_plugin(NameRevisionPlugin())


class NameRevisionPlugin(plugin.PyangPlugin):

    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['name-revision'] = self

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        emit_name(ctx, modules, fd)


def emit_name(ctx, modules, fd):
    for module in modules:
        bstr = ""
        rstr = ""
        b = module.search_one('belongs-to')
        r = module.search_one('revision')
        if b is not None:
            bstr = " (belongs-to %s)" % b.arg
        if r is not None:
            rstr = '@%s' % r.arg
        fd.write("%s%s%s\n" % (module.arg, rstr, bstr))
