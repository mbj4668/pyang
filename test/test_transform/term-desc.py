import re

from pyang import plugin


def pyang_plugin_init():
    plugin.register_plugin(TermDescPlugin())


class TermDescPlugin(plugin.PyangPlugin):
    def add_transform(self, xforms):
        xforms['term-desc'] = self

    def transform(self, ctx, modules):
        for module in modules:
            term_desc(module)


# XXX need to split the description into empty-line-separated paragraphs
def term_desc(stmt):
    desc = stmt.search_one('description')
    if desc:
        if re.search(r'\s+$', desc.arg):
            desc.arg = re.sub(r'\s+$', '', desc.arg)
        if not re.search(r'[.!?]$', desc.arg):
            desc.arg += '.'

    # XXX there may be a better idiom for this
    if hasattr(stmt, 'i_children'):
        for child in stmt.i_children:
            term_desc(child)
