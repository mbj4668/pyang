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
    n = dict.iteritems()
    try:
        while True:
            (k,v) = n.next()
            if v == val:
                return k
    except StopIteration:
        return None

def is_prefixed(identifier):
    return type(identifier) == type(()) and len(identifier) == 2

def is_local(identifier):
    return type(identifier) == type('')


