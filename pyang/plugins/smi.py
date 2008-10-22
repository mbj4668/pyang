"""SMIv2 plugin"""

import re

import pyang
from pyang import plugin
from pyang import syntax
from pyang import grammar
from pyang import statements

smi_module_name = 'yang-smi'

re_smi_oid = re.compile("^(([0-1](\.[1-3]?[0-9]))|(2.(0|([1-9]\d*))))?"
                          + "(\.(0|([1-9]\d*)))+$")

class SMIPlugin(plugin.PyangPlugin):
    pass

def _chk_smi_oid(s):
    return re_smi_oid.search(s) is not None

def pyang_plugin_init():
    """Called by pyang plugin framework at to initialize the plugin."""

    # Register the plugin
    plugin.register_plugin(SMIPlugin())
    
    # Add our special argument syntax checker
    syntax.add_arg_type('smi-oid', _chk_smi_oid)

    # Register that we handle extensions from the YANG module 'smi' 
    grammar.register_extension_module(smi_module_name)

    # Register the special grammar
    for (stmt, occurance, (arg, rules), add_to_stmts) in smi_stmts:
        grammar.add_stmt((smi_module_name, stmt), (arg, rules))
        grammar.add_to_stmts_rules(add_to_stmts,
                                   [((smi_module_name, stmt), occurance)])

    # Add validation step
    statements.add_validation_fun('type',
                                  [(smi_module_name, 'oid')],
                                  v_parse_oid)
    statements.add_validation_phase('smi_set_oid', after='inherit_properties')
    statements.add_validation_fun('smi_set_oid',
                                  ['module', 'submodule'],
                                  v_set_oid)

smi_stmts = [
    
    # (<keyword>, <occurance when used>,
    #  (<argument type name | None>, <substmts>),
    #  <list of keywords where <keyword> can occur>)

    ('oid', '?',
     ('smi-oid', []),
     ['leaf', 'leaf-list', 'list', 'container', 'module',
      'augment', 'notification']),
    
    ('display-hint', '?',
     ('string', []),
     ['leaf', 'typedef']),

    ('default', '?',
     ('string', []),
     ['leaf', 'typedef']),

]
    
re_sub = re.compile("[0-9]+")

def v_parse_oid(ctx, stmt):
    oid = [int(s) for s in re_sub.findall(stmt.arg)]
    stmt.parent.i_smi_oid = oid

def v_set_oid(ctx, stmt):
    pass
    
