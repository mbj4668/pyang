"""SMIv2 plugin

Verifies SMIv2 YANG statements as defined in RFC 6643.

This implementation relaxes one rule from RFC 6643; it allows
smiv2:subid if an ancestor statement has a smiv2:oid or smiv2:subid
statement.  RFC 6643 requires the parent statement to have the
smiv2:oid or smiv2:subid statement.

Verifies the grammar of the restcinf extension statements.
"""

import pyang
from pyang import plugin
from pyang import grammar
from pyang import statements

restconf_module_name = 'ietf-restconf'

class RESTCONFPlugin(plugin.PyangPlugin):
    def __init__(self):
        plugin.PyangPlugin.__init__(self, 'restconf')

def pyang_plugin_init():
    """Called by pyang plugin framework at to initialize the plugin."""

    # Register the plugin
    plugin.register_plugin(RESTCONFPlugin())

    # Register that we handle extensions from the YANG module 'ietf-restconf'
    grammar.register_extension_module(restconf_module_name)

    yd = (restconf_module_name, 'yang-data')
    statements.add_data_keyword(yd)
    statements.add_keyword_with_children(yd)
    statements.add_keywords_with_no_explicit_config(yd)

    # Register the special grammar
    for (stmt, occurance, (arg, rules), add_to_stmts) in restconf_stmts:
        grammar.add_stmt((restconf_module_name, stmt), (arg, rules))
        grammar.add_to_stmts_rules(add_to_stmts,
                                   [((restconf_module_name, stmt), occurance)])

restconf_stmts = [

    # (<keyword>, <occurance when used>,
    #  (<argument type name | None>, <substmts>),
    #  <list of keywords where <keyword> can occur>)

    ('yang-data', '?',
     ('identifier', grammar.data_def_stmts),
     ['module', 'submodule']),

]
