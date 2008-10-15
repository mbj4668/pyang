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

def keyword_to_str(keyword):
    if is_prefixed(keyword):
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
