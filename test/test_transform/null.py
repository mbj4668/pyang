from pyang import plugin


def pyang_plugin_init():
    plugin.register_plugin(Null())


class Null(plugin.PyangPlugin):
    def add_transform(self, xforms):
        xforms['null'] = self

    def transform(self, ctx, modules):
        pass
