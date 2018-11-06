from pyang import plugin
from pyang import statements

plugin_name = 'add-foo'

def pyang_plugin_init():
    plugin.register_plugin(AddFoo())


class AddFoo(plugin.PyangPlugin):
    def add_opts(self, optparser):
        pass

    def add_transform(self, xforms):
        xforms[plugin_name] = self

    # what are the pros and cons for using pre-validate versus post-validate?
    # probably pre-validate is usually better?
    def post_validate_ctx(self, ctx, modules):
        if plugin_name not in ctx.opts.transforms:
            return

        for module in modules:
            for stmt in module.substmts:
                if stmt.keyword == 'container':
                    foo = stmt.search_one('foo')
                    if not foo:
                        foo = add_leaf(stmt, 'foo', 'string')

            # this is NECESSARY if the module was changed and any downstream
            # processing relies on it having been validated, e.g. uses
            # i_children (as does the tree output format)
            statements.validate_module(ctx, module)


def add_leaf(parent, name, type_name):
    leaf = statements.Statement(parent.top, parent, parent.pos, 'leaf', name)
    parent.substmts.append(leaf)
    add_type(leaf, type_name)
    return leaf


def add_type(leaf, type_name):
    type_ = statements.Statement(leaf.top, leaf, leaf.pos, 'type', type_name)
    leaf.substmts.append(type_)
    return type_
