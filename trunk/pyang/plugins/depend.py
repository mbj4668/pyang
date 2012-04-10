"""Makefile dependency rule output plugin

"""

import optparse
import sys
import os.path

from pyang import plugin
from pyang import error

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
                                 help="YANG module file name extension"),
            optparse.make_option("--depend-include-path",
                                 dest="depend_include_path",
                                 action="store_true",
                                 help="Include file path in the prerequisites"),
            optparse.make_option("--depend-ignore-module",
                                 dest="depend_ignore",
                                 default=[],
                                 action="append",
                                 help="(sub)module to ignore in the" \
                                     " prerequisites.  This option can be" \
                                     " given multiple times."),
            ]
        g = optparser.add_option_group("Depend output specific options")
        g.add_options(optlist)
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['depend'] = self
    def emit(self, ctx, modules, fd):
        # cannot do this unless everything is ok for our module
        modulenames = [m.arg for m in modules]
        for (epos, etag, eargs) in ctx.errors:
            if (epos.top.arg in modulenames and
                error.is_error(error.err_level(etag))):
                raise error.EmitError("%s contains errors" % epos.top.arg)
        emit_depend(ctx, modules, fd)
        
def emit_depend(ctx, modules, fd):
    for module in modules:
        if ctx.opts.depend_target is None:
            fd.write('%s :' % module.pos.ref)
        else:
            fd.write('%s :' % ctx.opts.depend_target)
        prereqs = module.search("import")
        if not ctx.opts.depend_no_submodules:
            prereqs += module.search("include")
        for i in prereqs:
            if i.arg in ctx.opts.depend_ignore:
                continue
            if ctx.opts.depend_include_path:
                m = ctx.get_module(i.arg)
                if ctx.opts.depend_extension is None:
                    filename = m.pos.ref
                else:
                    basename = os.path.splitext(m.pos.ref)[0]
                    filename = '%s%s' % (basename, ctx.opts.depend_extension)
                fd.write(' %s' % filename)
            else:
                if ctx.opts.depend_extension is None:
                    ext = ""
                else:
                    ext = ctx.opts.depend_extension
                fd.write(' %s%s' % (i.arg, ext))
        fd.write('\n')
