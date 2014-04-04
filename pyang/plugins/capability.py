"""Capability URL plugin

"""

import optparse
import sys
import os.path

from pyang import plugin
from pyang import util

def pyang_plugin_init():
    plugin.register_plugin(CapabilityPlugin())

class CapabilityPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['capability'] = self
    def emit(self, ctx, modules, fd):
        for m in modules:
            emit_capability(ctx, m, fd)

def emit_capability(ctx, m, fd):
    ns = m.search_one('namespace')
    if ns is None:
        return
    s = ns.arg + "?module=" + m.i_modulename

    latest_rev = util.get_latest_revision(m)
    if latest_rev != "unknown":
        s = s + "&revision=" + latest_rev

    if m.i_modulename in ctx.features:
        if len(ctx.features[m.i_modulename]) > 0:
            s = s + "&features=" + ",".join(ctx.features[m.i_modulename])
        else:
            # do not report any features from the module
            pass
    else:
        # report all features defined in the module
        fs = [x.arg for x in m.search('feature')]
        s = s + "&features=" + ",".join(fs)

    devs = []
    for d in ctx.deviation_modules:
        # check if this deviation module deviates anything in our module
        for dev in d.search('deviation'):
            if (dev.i_target_node is not None and
                dev.i_target_node.i_module.i_modulename == m.i_modulename):
                devs.append(m.i_modulename)
                break

    if len(devs) > 0:
        s = s + "&deviations=" +  ",".join(devs)

    fd.write(s + '\n')