"""IETF usage guidelines plugin
See draft-ietf-netmod-yang-usage
"""

import optparse
import sys

from pyang import plugin
from pyang import statements
from pyang import error
from pyang.error import err_add

def pyang_plugin_init():
    plugin.register_plugin(IETFPlugin())

class IETFPlugin(plugin.PyangPlugin):
    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--ietf",
                                 dest="ietf",
                                 action="store_true",
                                 help="Validate the module(s) according to " \
                                 "IETF rules."),
            ]
        optparser.add_options(optlist)

    def setup_ctx(self, ctx):
        if not ctx.opts.ietf:
            return

        ctx.canonical = True;
        ctx.max_line_len = 72
        ctx.max_identifier_len = 64
        ctx.implicit_errors = False

        # register our grammar validation funs

        statements.add_validation_var(
            '$chk_default',
            lambda keyword: keyword in _keyword_with_default)
        statements.add_validation_var(
            '$chk_required',
            lambda keyword: keyword in _required_substatements)

        statements.add_validation_var(
            '$chk_recommended',
            lambda keyword: keyword in _recommended_substatements)
            
        statements.add_validation_fun(
            'grammar', ['$chk_default'],
            lambda ctx, s: v_chk_default(ctx, s))
        statements.add_validation_fun(
            'grammar', ['$chk_required'],
            lambda ctx, s: v_chk_required_substmt(ctx, s))
        statements.add_validation_fun(
            'grammar', ['$chk_recommended'],
            lambda ctx, s: v_chk_recommended_substmt(ctx, s))

        statements.add_validation_fun(
            'grammar', ['namespace'],
            lambda ctx, s: v_chk_namespace(ctx, s))

        statements.add_validation_fun(
            'grammar', ['module', 'submodule'],
            lambda ctx, s: v_chk_module_name(ctx, s))        

        statements.add_validation_fun(
            'unique_name', ['module'],
            lambda ctx, s: v_chk_top_level_nodes(ctx, s))

        # register our error codes
        error.add_error_code(
            'IETF_EXPLICIT_DEFAULT', 4,
            'IETF rule: statement "%s" is given with its default value "%s"')
        error.add_error_code(
            'IETF_MISSING_REQUIRED_SUBSTMT', 3,
            'IETF rule: statement "%s" must have a "%s" substatement')
        error.add_error_code(
            'IETF_MISSING_RECOMMENDED_SUBSTMT', 4,
            'IETF rule: statement "%s" should have a "%s" substatement')
        error.add_error_code(
            'IETF_BAD_NAMESPACE_VALUE', 4,
            'IETF rule: namespace value should be "%s"')
        error.add_error_code(
            'IETF_TOO_MANY_TOP_LEVEL_NODES', 4,
            'IETF rule: too many top-level data nodes: %s')
        error.add_error_code(
            'IETF_NO_MODULE_PREFIX', 4,
            'IETF rule: no module name prefix used, suggest ietf-%s')

        # override std error string
        error.add_error_code(
            'LONG_LINE', 4,
            'IETF rule: line length %s exceeds %s characters')
        error.add_error_code(
            'LONG_IDENTIFIER', 3,
            'IETF rule: identifier %s exceeds %s characters')
        
        
_keyword_with_default = {
    'status': 'current',
    'mandatory': 'false',
    'min-elements': '0',
    'max-elements': 'unbounded',
    'config': 'true',
    'yin-element': 'false',
    }

_required_substatements = {
    'module': ('contact', 'organization', 'description', 'revision'),
    'submodule': ('contact', 'organization', 'description', 'revision'),
    'revision':('reference',),
    'extension':('description',),
    'feature':('description',),
    'identity':('description',),
    'typedef':('description',),
    'grouping':('description',),
    'grouping':('description',),
    'augment':('description',),
    'rpc':('description',),
    'notification':('description',),
    'container':('description',),
    'leaf':('description',),
    'leaf-list':('description',),
    'list':('description',),
    'choice':('description',),
    'anyxml':('description',),
    }

_recommended_substatements = {
    'must':('description',),
    'when':('description',),
    'enum':('description',),
    'bit':('description',),
    }


_ietf_namespace_prefix = 'urn:ietf:params:xml:ns:yang:'

def v_chk_default(ctx, stmt):
    if stmt.arg == _keyword_with_default[stmt.keyword]:
        err_add(ctx.errors, stmt.pos, 'IETF_EXPLICIT_DEFAULT',
                (stmt.keyword, stmt.arg))

def v_chk_required_substmt(ctx, stmt):
    if stmt.keyword in _required_substatements:
        for r in _required_substatements[stmt.keyword]:
            if stmt.search_one(r) is None:
                err_add(ctx.errors, stmt.pos,
                        'IETF_MISSING_REQUIRED_SUBSTMT',
                        (stmt.keyword, r))

def v_chk_recommended_substmt(ctx, stmt):
    if stmt.keyword in _recommended_substatements:
        for r in _recommended_substatements[stmt.keyword]:
            if stmt.search_one(r) is None:
                err_add(ctx.errors, stmt.pos,
                        'IETF_MISSING_RECOMMENDED_SUBSTMT',
                        (stmt.keyword, r))

def v_chk_namespace(ctx, stmt):
    if not stmt.arg == _ietf_namespace_prefix + stmt.i_module.arg:
        err_add(ctx.errors, stmt.pos, 'IETF_BAD_NAMESPACE_VALUE',
                _ietf_namespace_prefix + stmt.i_module.arg)
        
def v_chk_top_level_nodes(ctx, stmt):
    top = [x for x in stmt.i_children if x.keyword not in ['rpc','notification']]
    if len(top) > 1:
        err_add(ctx.errors, stmt.pos, 'IETF_TOO_MANY_TOP_LEVEL_NODES',
                ", ".join(x.arg for x in top))

def v_chk_module_name(ctx, stmt):
    # can't check much, but we can check that a prefix is used
    if stmt.arg.find('-') == -1:
        err_add(ctx.errors, stmt.pos, 'IETF_NO_MODULE_PREFIX', stmt.arg)
