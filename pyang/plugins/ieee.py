"""IEEE usage guidelines plugin
See RFC 6087
"""

import optparse
import sys

from pyang import plugin
from pyang import statements
from pyang import error
from pyang.error import err_add
from pyang.plugins import lint

def pyang_plugin_init():
    plugin.register_plugin(IEEEPlugin())

class IEEEPlugin(lint.LintPlugin):
    def __init__(self):
        lint.LintPlugin.__init__(self)
        self.namespace_prefixes = ['urn:ieee:std:']
        self.modulename_prefixes = ['ieee']

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--ieee",
                                 dest="ieee",
                                 action="store_true",
                                 help="Validate the module(s) according to " \
                                 "IEEE rules."),
            ]
        optparser.add_options(optlist)

    def setup_ctx(self, ctx):
        if not ctx.opts.ieee:
            return
        self._setup_ctx(ctx)
