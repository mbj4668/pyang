"""Test adding validation for multiple keywords
"""

from pyang import plugin
from pyang import statements
from pyang import error
from pyang.error import err_add

def pyang_plugin_init():
    plugin.register_plugin(ComposedPlugin())

class ComposedPlugin(plugin.PyangPlugin):
    def setup_ctx(self, ctx):

        statements.add_validation_fun(
            'grammar', ['module'],
            v_chk_module)

        statements.add_validation_fun(
            'grammar', ['submodule'],
            v_chk_submodule)

        statements.add_validation_fun(
            'grammar', ['module', 'submodule'],
            v_chk_both)

        error.add_error_code(
            'COMPOSE_MODULE_ONLY', 2,
            'Module-only validation called for %s %s')

        error.add_error_code(
            'COMPOSE_SUBMODULE_ONLY', 2,
            'Submodule-only validation called for %s %s')

        error.add_error_code(
            'COMPOSE_CALLED', 4,
            'Check %s issued for %s %s')

def v_chk_module(ctx, stmt):
    err_add(ctx.errors, stmt.pos, 'COMPOSE_CALLED', ('module', stmt.keyword, stmt.arg))
    if stmt.keyword != 'module':
        err_add(ctx.errors, stmt.pos, 'COMPOSE_MODULE_ONLY', (stmt.keyword, stmt.arg))

def v_chk_submodule(ctx, stmt):
    err_add(ctx.errors, stmt.pos, 'COMPOSE_CALLED', ('submodule', stmt.keyword, stmt.arg))
    if stmt.keyword != 'submodule':
        err_add(ctx.errors, stmt.pos, 'COMPOSE_SUBMODULE_ONLY', (stmt.keyword, stmt.arg))

def v_chk_both(ctx, stmt):
    err_add(ctx.errors, stmt.pos, 'COMPOSE_CALLED', ('both', stmt.keyword, stmt.arg))
