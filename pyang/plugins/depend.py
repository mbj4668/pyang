"""Makefile dependency rule output plugin

"""

import optparse
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
            optparse.make_option("--depend-from-submodules",
                                 dest="depend_from_submodules",
                                 action="store_true",
                                 help="Generate dependencies from " \
                                 "included submodules"),
            optparse.make_option("--depend-recurse",
                                 dest="depend_recurse",
                                 action="store_true",
                                 help="Generate dependencies to all " \
                                     "imports, recursively"),
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
        for epos, etag, eargs in ctx.errors:
            if ((epos.top is None or epos.top.arg in modulenames) and
                error.is_error(error.err_level(etag))):
                raise error.EmitError("%s contains errors" % epos.top.arg)
        emit_depend(ctx, modules, fd)

def emit_depend(ctx, modules, fd):
    for module in modules:
        if ctx.opts.depend_target is None:
            fd.write('%s :' % module.pos.ref)
        else:
            fd.write('%s :' % ctx.opts.depend_target)
        prereqs = []  # list of (name, revision) pairs
        add_prereqs(ctx, module, prereqs)
        emitted = set()  # dedup on the emitted token, not the (name, rev) pair
        for name, revision in prereqs:
            if name in ctx.opts.depend_ignore:
                continue
            if ctx.opts.depend_include_path:
                # resolve with revision; a name-only lookup picks the latest
                # revision, which may not be loaded (so m would be None)
                m = ctx.get_module(name, revision)
                if m is None or m.pos is None:
                    # unresolvable; best-effort name@revision keeps the revision
                    base = '%s@%s' % (name, revision) if revision else name
                    filename = '%s%s' % (base, ctx.opts.depend_extension or "")
                elif ctx.opts.depend_extension is None:
                    filename = m.pos.ref
                else:
                    basename = os.path.splitext(m.pos.ref)[0]
                    filename = '%s%s' % (basename, ctx.opts.depend_extension)
            else:
                filename = '%s%s' % (name, ctx.opts.depend_extension or "")
            if filename not in emitted:
                emitted.add(filename)
                fd.write(' %s' % filename)
        fd.write('\n')

def _revision(stmt):
    rev = stmt.search_one("revision-date")
    return rev.arg if rev is not None else None

def add_prereqs(ctx, module, prereqs):
    # dedup on the (name, revision) pair, not the name alone
    seen = set(prereqs)
    new = []
    def add(stmts):
        for i in stmts:
            key = (i.arg, _revision(i))
            if key not in seen:
                seen.add(key)
                new.append(key)
    add(module.search("import"))
    if not ctx.opts.depend_no_submodules:
        add(module.search("include"))
    if ctx.opts.depend_from_submodules:
        for i in module.search("include"):
            subm = ctx.get_module(i.arg, _revision(i))
            if subm is not None:
                add(subm.search("import"))
    prereqs.extend(new)
    if ctx.opts.depend_recurse:
        for name, revision in new:
            m = ctx.get_module(name, revision)
            if m is not None:
                add_prereqs(ctx, m, prereqs)
