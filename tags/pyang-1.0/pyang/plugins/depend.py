"""Makefile dependency rule output plugin

"""

import optparse
import sys

from pyang import plugin

def pyang_plugin_init():
    plugin.register_plugin(DependPlugin())

class DependPlugin(plugin.PyangPlugin):
    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--depend-target",
                                 dest="depend_target",
                                 help="Makefile rule target"),
            optparse.make_option("--depend-no-submodules",
                                 dest="depend_no_submodules",
                                 action="store_true",
                                 help="Do not generate dependencies for " \
                                 "included submodules"),
            optparse.make_option("--depend-extension",
                                 dest="depend_extension",
                                 default="",
                                 help="YANG module file name extension"),
            ]
        g = optparser.add_option_group("Depend output specific options")
        g.add_options(optlist)
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['depend'] = self
    def emit(self, ctx, modules, fd):
        emit_depend(ctx, modules, fd)
        
def emit_depend(ctx, modules, fd):
    for module in modules:
        if ctx.opts.depend_target is None:
            fd.write('%s :' % module.pos.ref)
        else:
            fd.write('%s :' % ctx.opts.depend_target)
        for i in module.search("import"):
            fd.write(' %s%s' % (i.arg, ctx.opts.depend_extension))
        if not ctx.opts.depend_no_submodules:
            for i in module.search("include"):
                fd.write(' %s%s' % (i.arg, ctx.opts.depend_extension))
        fd.write('\n')
