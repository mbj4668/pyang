import re
import sys

# not 100% XPath / XML, but good enough for YANG
namestr=r'[a-zA-Z_][a-zA-Z0-9_\-.]*'
ncnamestr = '((' + namestr + '):)?(' + namestr + ')'
prefixteststr = '((' + namestr + r'):)?\*'

patterns = [
    ('whitespace', re.compile(r'\s+')),
    # Expr tokens
    ('(', re.compile(r'\(')),
    (')', re.compile(r'\)')),
    ('[', re.compile(r'\[')),
    (']', re.compile(r'\]')),
    ('..', re.compile(r'\.\.')),
    ('.', re.compile(r'\.')),
    ('@', re.compile(r'\@')),
    (',', re.compile(r',')),
    ('::', re.compile(r'::')),
    # operators
    ('//', re.compile(r'\/\/')),
    ('/', re.compile(r'\/')),
    ('|', re.compile(r'\|')),
    ('+', re.compile(r'\+')),
    ('-', re.compile(r'-')),
    ('=', re.compile(r'=')),
    ('!=', re.compile(r'!=')),
    ('<=', re.compile(r'<=')),
    ('>=', re.compile(r'>=')),
    ('>', re.compile(r'>')),
    ('<', re.compile(r'<')),
    ('*', re.compile(r'\*')),
    # others
    ('number', re.compile(r'[0-9]+(\.[0-9]+)?')),
    ('prefix-test', re.compile(prefixteststr)),
    ('name', re.compile(ncnamestr)),
    ('attribute', re.compile(r'\@' + ncnamestr)),
    ('variable', re.compile(r'\$' + ncnamestr)),
    ('literal', re.compile(r'(\".*?\")|(\'.*?\')')),
    ]

operators = [ 'div', 'and', 'or', 'mod' ]
node_types = [ 'comment', 'text', 'processing-instruction', 'node' ]
axes = [ 'ancestor-or-self', 'ancestor', 'attribute', 'child',
         'descendant-or-self', 'descendant', 'following-sibling',
         'following', 'namespace', 'parent', 'preceding-sibling',
         'preceding', 'self' ]

re_open_para = re.compile(r'\s*\(')
re_axis = re.compile(r'\s*::')

def validate(s):
    """Validate the XPath expression in the string `s`
    Return True if the expression is correct, and throw
    SyntaxError on failure."""
    t = tokens(s)
    return True

def tokens(s):
    """Return a list of tokens, or throw SyntaxError on failure.
    A token is one of the patterns or:
      ('wildcard', '*')
      ('axis', axisname)
    """
    pos = 0
    toks = []
    while pos < len(s):
        matched = False
        for (tokname, r) in patterns:
            m = r.match(s, pos)
            if m is not None:
                # found a matching token
                prec = _preceding_token(toks)
                if tokname == '*' and prec is not None and _is_special(prec):
                    # XPath 1.0 spec, 3.7 special rule 1a
                    # interpret '*' as a wildcard
                    tok = ('wildcard', m.group(0))
                elif (tokname == 'name' and
                      prec is not None and not _is_special(prec) and
                      m.group(0) in operators):
                    # XPath 1.0 spec, 3.7 special rule 1b
                    # interpret the name as an operator
                    tok = (m.group(0), m.group(0))
                elif tokname == 'name':
                    # check if next token is '('
                    if re_open_para.match(s, pos + len(m.group(0))):
                        # XPath 1.0 spec, 3.7 special rule 2
                        if m.group(0) in node_types:
                            # XPath 1.0 spec, 3.7 special rule 2a
                            tok = (m.group(0), m.group(0))
                        else:
                            # XPath 1.0 spec, 3.7 special rule 2b
                            tok = ('function', m.group(0))
                    # check if next token is '::'
                    elif re_axis.match(s, pos + len(m.group(0))):
                        # XPath 1.0 spec, 3.7 special rule 3
                        if m.group(0) in axes:
                            tok = ('axis', m.group(0))
                        else:
                            e = "%s: unknown axis %s" % (pos+1, m.group(0))
                            raise SyntaxError(e)
                    else:
                        tok = ('name', m.group(0))
                else:
                    tok = (tokname, m.group(0))
                pos += len(m.group(0))
                toks.append(tok)
                matched = True
                break
        if matched == False:
            # no patterns matched
            raise SyntaxError("at position %s" % str(pos+1))
    return toks

def _preceding_token(toks):
    if len(toks) > 1 and toks[-1][0] == 'whitespace':
        return toks[-2][0]
    if len(toks) > 0 and toks[-1][0] != 'whitespace':
        return toks[-1][0]
    return None

_special_toks = [ ',', '@', '::', '(', '[', '/', '//', '|', '+', '-',
                 '=', '!=', '<', '<=', '>', '>=',
                 'and', 'or', 'mod', 'div' ]

def _is_special(tok):
    return tok in _special_toks


def add_prefix(prefix, s):
    "Add `prefix` to all unprefixed names in `s`"
    # tokenize the XPath expression
    toks = tokens(s)
    # add default prefix to unprefixed names
    toks2 = [_add_prefix(prefix, tok) for tok in toks]
    # build a string of the patched expression
    ls = [x for (_tokname, x) in toks2]
    return ''.join(ls)

_re_ncname = re.compile(ncnamestr)
def _add_prefix(prefix, tok):
    (tokname, s) = tok
    if tokname == 'name':
        m = _re_ncname.match(s)
        if m.group(2) == None:
            return (tokname, prefix + ':' + s)
    return tok

core_functions = [
    'last',
    'position',
    'count',
    'id',
    'local-name',
    'namespace-uri',
    'name',
    'string',
    'concat',
    'starts-with',
    'contains',
    'substring-before',
    'substring-after',
    'substring',
    'string-length',
    'normalize-space',
    'translate',
    'boolean',
    'not',
    'true',
    'false',
    'lang',
    'number',
    'sum',
    'floor',
    'ceiling',
    'round',
    ]
