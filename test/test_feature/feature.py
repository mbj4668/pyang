from pyang import plugin


def pyang_plugin_init():
    plugin.register_plugin(FeaturePlugin())


class FeaturePlugin(plugin.PyangPlugin):
    def add_transform(self, xforms):
        xforms['feature'] = self

    def transform(self, ctx, modules):
        for module in modules:
            print('# %s: features %s' % (module, ctx.features.get(
                    module.arg, None)))
