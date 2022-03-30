from pyang import plugin


def pyang_plugin_init():
    plugin.register_plugin(FeaturePlugin())


def f(fs):
    if fs is None:
        return 'None'
    elif len(fs) == 0:
        return '[]'
    else:
        fs.sort()
        return ','.join(fs)

class FeaturePlugin(plugin.PyangPlugin):
    def add_transform(self, xforms):
        xforms['feature'] = self

    def transform(self, ctx, modules):
        for module in modules:
            print('# %s: features %s exclude_features %s' %
                  (module,
                   f(ctx.features.get(module.arg, None)),
                   f(ctx.exclude_features.get(module.arg, None))))
