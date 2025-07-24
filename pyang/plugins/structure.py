"""YANG structure plugin

Verifies the grammar of the structure extension statements,
as defined in RFC 8791.
"""

import pyang
from pyang import plugin
from pyang import grammar
from pyang import statements
from pyang import error
from pyang.error import err_add

module_name = 'ietf-yang-structure-ext'

class StructurePlugin(plugin.PyangPlugin):
    def __init__(self):
        plugin.PyangPlugin.__init__(self, 'structure')

def pyang_plugin_init():
    """Called by pyang plugin framework at to initialize the plugin."""

    # Register the plugin
    plugin.register_plugin(StructurePlugin())

    # Register that we handle extensions from the YANG module
    # 'ietf-yang-structure-ext'
    grammar.register_extension_module(module_name)

    sx = (module_name, 'structure')
    statements.add_data_keyword(sx)
    statements.add_keyword_with_children(sx)
    statements.add_keywords_with_no_explicit_config(sx)
    asx = (module_name, 'augment-structure')
    statements.add_data_keyword(asx)
    statements.add_keyword_with_children(asx)
    statements.add_keywords_with_no_explicit_config(asx)

    # Register the special grammar
    for (stmt, occurance, (arg, rules), add_to_stmts) in structure_stmts:
        grammar.add_stmt((module_name, stmt), (arg, rules))
        grammar.add_to_stmts_rules(add_to_stmts,
                                   [((module_name, stmt), occurance)])

    # Add validation functions
    statements.add_validation_fun('expand_2',
                                  [asx],
                                  v_expand_2_augment_sx)
    statements.add_validation_fun('expand_3',
                                  [asx],
                                  v_expand_3_augment_sx)

    # Register special erro codes
    error.add_error_code('BAD_AUGMENT_STRUCTURE_TARGET_NODE', 1,
                         "target node of 'augment-structure' statement " +
                         "must be 'structure' node")

def v_expand_2_augment_sx(ctx, stmt):
    """
    First pass of two-pass augment expansion algorithm changed for
    augment-structure.

    First observation: since we validate each imported module, all
    nodes that are augmented by other modules already exist.  For each
    node in the path to the target node, if it does not exist, it
    might get created by an augment later in this module.  This only
    applies to nodes defined in our namespace (since all other modules
    already are validated).  For each such node, we add a temporary
    Statement instance, and store a pointer to it.  If we find such a
    temporary node in the nodes we add, we replace it with our real
    node, and delete it from the list of temporary nodes created.
    When we're done with all augment statements, the list of temporary
    nodes should be empty, otherwise it is an error.
    """
    statements.v_expand_2_augment(ctx, stmt)

def v_expand_3_augment_sx(ctx, stmt):
    """
    Second pass of two-pass augment expansion algorithm changed for
    augment-structure statement.

    Find the (possibly expanded) target nodes again. The reason for
    this is that stmt.i_target_node may point to a __tmp__augment__ node.
    """
    statements.v_expand_3_augment(ctx, stmt)
    if not hasattr(stmt, 'i_target_node') or stmt.i_target_node is None:
        err_add(ctx.errors, stmt.pos, 'BAD_NODE_IN_AUGMENT', ())
    target = stmt.i_target_node
    # Try to find toplevel 'structure' node parent
    while (target.parent != None and
           target.parent.keyword not in ('module', 'submodule')):
        target = target.parent
    if target.keyword != (module_name, 'structure'):
        err_add(ctx.errors, stmt.pos, 'BAD_AUGMENT_STRUCTURE_TARGET_NODE', ())

sx_body_stmts = [
    ('must', '*'),
    ('status', '?'),
    ('description', '?'),
    ('reference', '?'),
    ('$interleave', [('typedef', '*'),
                     ('grouping', '*')] +
                    grammar.data_def_stmts),
    ]

asx_body_stmts = [
    ('status', '?'),
    ('description', '?'),
    ('reference', '?'),
    ## FIXME at least one data-def-stmt substatement \
    ## or case statement is required
    ('$interleave', [('case', '*')] +
                    grammar.data_def_stmts),
    ]

structure_stmts = [

    # (<keyword>, <occurance when used>,
    #  (<argument type name | None>, <substmts>),
    #  <list of keywords where <keyword> can occur>)

    ('structure', '*',
     ('identifier', sx_body_stmts),
     ['module', 'submodule']),

    ('augment-structure', '*',
     ('absolute-schema-nodeid', asx_body_stmts),
     ['module', 'submodule']),

]
