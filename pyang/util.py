import datetime

from .error import err_add

## unicode literal support
import sys
if sys.version < '3':
    import codecs
    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def u(x):
        return x

def attrsearch(tag, attr, list):
    for x in list:
        if x.__dict__[attr] == tag:
            return x
    return None

def keysearch(tag, n, list):
    for x in list:
        if x[n] == tag:
            return x
    return None

def dictsearch(val, dict):
    if sys.version < '3':
        n = dict.iteritems()
        try:
            while True:
                (k,v) = n.next()
                if v == val:
                    return k
        except StopIteration:
            return None
    else:
        n = iter(dict.items())
        try:
            while True:
                (k,v) = next(n)
                if v == val:
                    return k
        except StopIteration:
            return None

def is_prefixed(identifier):
    return type(identifier) == type(()) and len(identifier) == 2

def is_local(identifier):
    return type(identifier) == type('') or type(identifier) == type(u(''))

def keyword_to_str(keyword):
    if keyword == '__tmp_augment__':
        return "undefined"
    elif is_prefixed(keyword):
        (prefix, keyword) = keyword
        return prefix + ":" + keyword
    else:
        return keyword

def guess_format(text):
    """Guess YANG/YIN format

    If the first non-whitespace character is '<' then it is XML.
    Return 'yang' or 'yin'"""
    format = 'yang'
    i = 0
    while i < len(text) and text[i].isspace():
        i += 1
    if i < len(text):
        if text[i] == '<':
            format = 'yin'
    return format

def listsdelete(x, xs):
    """Return a new list with x removed from xs"""
    i = xs.index(x)
    return xs[:i] + xs[(i+1):]

def get_latest_revision(module):
    latest = None
    for r in module.search('revision'):
        if latest is None or r.arg > latest:
            latest = r.arg
    if latest is None:
        #return datetime.date.today().isoformat()
        return "unknown"
    else:
        return latest

def prefix_to_modulename_and_revision(module, prefix, pos, errors):
    if prefix == '':
        return module.arg, None
    if prefix == module.i_prefix:
        return module.arg, None
    try:
        (modulename, revision) = module.i_prefixes[prefix]
    except KeyError:
        if prefix not in module.i_missing_prefixes:
            err_add(errors, pos, 'PREFIX_NOT_DEFINED', prefix)
        module.i_missing_prefixes[prefix] = True
        return None, None
    # remove the prefix from the unused
    if prefix in module.i_unused_prefixes:
        del module.i_unused_prefixes[prefix]
    return modulename, revision

def prefix_to_module(module, prefix, pos, errors):
    if prefix == '':
        return module
    if prefix == module.i_prefix:
        return module
    modulename, revision = \
        prefix_to_modulename_and_revision(module, prefix, pos, errors)
    if modulename is None:
        return None
    return module.i_ctx.get_module(modulename, revision)

def unique_prefixes(context):
    """Return a dictionary with unique prefixes for modules in `context`.

    Keys are 'module' statements and values are prefixes,
    disambiguated where necessary.
    """
    res = {}
    for m in context.modules.values():
        if m.keyword == "submodule": continue
        prf = new = m.i_prefix
        suff = 0
        while new in res.values():
            suff += 1
            new = "%s%x" % (prf, suff)
        res[m] = new
    return res
