"""Cisco usage guidelines plugin
"""

import optparse
import sys

from pyang import plugin
from pyang import statements
from pyang import error
from pyang.error import err_add
from pyang.plugins import lint

def pyang_plugin_init():
    plugin.register_plugin(CiscoPlugin())

class CiscoPlugin(lint.LintPlugin):
    def __init__(self):
        lint.LintPlugin.__init__(self)
        self.namespace_prefixes = ['http://cisco.com/ns/yang/']
        self.modulename_prefixes = ['Cisco-IOS-XR', 'Cisco-IOS-XE', 'Cisco-IOS-NX-OS', 'cisco']

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--cisco",
                                 dest="cisco",
                                 action="store_true",
                                 help="Validate the module(s) according to " \
                                 "Cisco rules."),
            ]
        optparser.add_options(optlist)

    def setup_ctx(self, ctx):
        if not ctx.opts.cisco:
            return
        self._setup_ctx(ctx)
