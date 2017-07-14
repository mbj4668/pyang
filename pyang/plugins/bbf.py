"""BBF usage guidelines plugin
See BBF Assigned Names and Numbers at https://wiki.broadband-forum.org/display/BBF/Assigned+Names+and+Numbers#AssignedNamesandNumbers-URNNamespaces
"""

import optparse
import sys

from pyang import plugin
from pyang import statements
from pyang import error
from pyang.error import err_add
from pyang.plugins import lint

def pyang_plugin_init():
    plugin.register_plugin(BBFPlugin())

class BBFPlugin(lint.LintPlugin):
    def __init__(self):
        lint.LintPlugin.__init__(self)
        self.namespace_prefixes = ['urn:bbf:yang:']
        self.modulename_prefixes = ['bbf']

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--bbf",
                                 dest="bbf",
                                 action="store_true",
                                 help="Validate the module(s) according to " \
                                 "BBF rules."),
            ]
        optparser.add_options(optlist)

    def setup_ctx(self, ctx):
        if not ctx.opts.bbf:
            return
        self._setup_ctx(ctx)
