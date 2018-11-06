from pyang import plugin
from pyang import statements

plugin_name = 'mod-desc'

def pyang_plugin_init():
    plugin.register_plugin(ModDescPlugin())


class ModDescPlugin(plugin.PyangPlugin):
    def add_opts(self, optparser):
        pass

    def add_transform(self, xforms):
        xforms[plugin_name] = self

    def pre_validate_ctx(self, ctx, modules):
        if plugin_name not in ctx.opts.transforms:
            return

        for module in modules:
            mod_desc(module, '-- I added this!')
            statements.validate_module(ctx, module)


def mod_desc(stmt, text):
    desc = stmt.search_one('description')
    if desc:
        desc.arg += ' ' + text

    # XXX for some reason validate_module() crashes with undefined i_module if
    #     add description to module or submodule
    elif stmt.keyword not in ['module', 'submodule']:
        desc = statements.Statement(stmt.top, stmt, stmt.pos, 'description',
                                    text)
        stmt.substmts.append(desc)

    # XXX there may be a better idiom for this
    if hasattr(stmt, 'i_children'):
        for child in stmt.i_children:
            mod_desc(child, text)
