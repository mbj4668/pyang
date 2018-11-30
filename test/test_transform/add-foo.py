from pyang import error
from pyang import plugin
from pyang import statements


def pyang_plugin_init():
    plugin.register_plugin(AddFoo())


class AddFoo(plugin.PyangPlugin):
    def add_transform(self, xforms):
        xforms['add-foo'] = self

    def transform(self, ctx, modules):
        for module in modules:
            for stmt in module.substmts:
                if stmt.keyword == 'container':
                    foo = stmt.search_one('foo')
                    if not foo:
                        foo = add_leaf(stmt, 'foo', 'string')


def add_leaf(parent, name, type_name):
    leaf = statements.Statement(parent.top, parent, parent.pos, 'leaf', name)
    parent.substmts.append(leaf)
    add_type(leaf, type_name)
    return leaf


def add_type(leaf, type_name):
    type_ = statements.Statement(leaf.top, leaf, leaf.pos, 'type', type_name)
    leaf.substmts.append(type_)
    return type_
