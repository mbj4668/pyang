"""Description of YANG & YIN grammar."""

from pyang import statements
from pyang import util
from pyang import error
import syntax

# test:
# rpc foo {
#   typedef a1 { ... }
#   grouping a2 { ... }
#   typedef a3 { ... }
#   grouping a4 { ... }
#   input { ...}
# }
#
# also test negative w/ 2 input stmnts.

module_header_stmts = [
    ('yang-version', '?'),
    ('namespace', '1'),
    ('prefix', '1'),
]

submodule_header_stmts = [
    ('yang-version', '?'),
    ('belongs-to', '1'),
]

linkage_stmts = [
    ('import', '*'),
    ('include', '*'),
]

meta_stmts = [
    ('organization', '?'),
    ('contact', '?'),
    ('description', '?'),
    ('reference', '?'),
]

revision_stmts = [
    ('revision', '*'),
]

data_def_stmts = [
    ('container', '*'),
    ('leaf', '*'),
    ('leaf-list', '*'),
    ('list', '*'),
    ('choice', '*'),
    ('anyxml', '*'),
    ('uses', '*'),
    ('augment', '*'),
]

case_data_def_stmts = [
    ('container', '*'),
    ('leaf', '*'),
    ('leaf-list', '*'),
    ('list', '*'),
    ('anyxml', '*'),
    ('uses', '*'),
    ('augment', '*'),
]

# FIXME: not correct!! but if we introduce new keyword "refine" then
# this will be better...
refinement_stmts = [
    ('container', '*'),
    ('leaf', '*'),
    ('leaf-list', '*'),
    ('list', '*'),
    ('choice', '*'),
    ('anyxml', '*'),
]

body_stmts = [
    ('$interleave',
     [('extension', '*'),
      ('typedef', '*'),
      ('grouping', '*'),
      ('rpc', '*'),
      ('notification', '*'),
      ] +
     data_def_stmts
    )
]

cut = ('$cut', '*')
"""Marker for end of statement block.

Special substatement which marks the end of a block in which the
substatements may occur in any order.
"""

top_stmts = [
    ('$choice', [[('module', '1')],
                 [('submodule', '1')]])
]
"""Top-level statements."""

stmt_map = {
    'module':
        ('identifier',
         module_header_stmts +
         [cut] +
         linkage_stmts +
         [cut] +
         meta_stmts +
         [cut] +
         revision_stmts +
         [cut] +
         body_stmts),
    'submodule':
        ('identifier',
         submodule_header_stmts +
         [cut] +
         linkage_stmts +
         [cut] +
         meta_stmts +
         [cut] +
         revision_stmts +
         [cut] +
         body_stmts),
    'yang-version':
        ('version', []),
    'namespace':
        ('uri', []),
    'prefix':
        ('identifier', []),
    'import':
        ('identifier',
         [('prefix', '1')]),
    'include':
        ('identifier', []),
    'revision':
        ('date',
         [('description', '?')]),
    'belongs-to':
        ('identifier', []),
    'organization':
        ('string', []),
    'contact':
        ('string', []),
    'description':
        ('string', []),
    'reference':
        ('string', []),
    'units':
        ('string', []),
    'extension':
        ('identifier',
         [('argument', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?')]),
    'argument':
        ('identifier',
         [('yin-element', '?')]),
    'yin-element':
        ('boolean', []),
    'typedef':
        ('identifier',
         [('type', '1'),
          ('units', '?'),
          ('default', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'type':
        ('identifier-ref',
         [('$choice',
           [[('range', '?')],
            [('length', '?'),
             ('pattern', '*')],
            [('enum', '*')],
            [('bit', '*')],
            [('path', '?')],
            [('type', '*')]])]),
    'range':
        ('range-arg',
         [('error-message', '?'),
          ('error-app-tag', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'length':
        ('length-arg',
         [('error-message', '?'),
          ('error-app-tag', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'pattern':
        ('string',
         [('error-message', '?'),
          ('error-app-tag', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'default':
        ('string', []),
    'enum':
        ('identifier',
         [('value', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'path':
        ('path-arg', []),
    'bit':
        ('identifier',
         [('position', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'position':
        ('non-negative-decimal', []),
    'status':
        ('status-arg', []),
    'config':
        ('boolean', []),
    'mandatory':
        ('boolean', []),
    'presence':
        ('string', []),
    'ordered-by':
        ('ordered-by-arg', []),
    'must':
        ('string',
         [('error-message', '?'),
          ('error-app-tag', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'error-message':
        ('string', []),
    'error-app-tag':
        ('string', []),
    'min-elements':
        ('non-negative-decimal', []),
    'max-elements':
        ('max-value', []),
    'value':
        ('decimal', []),
    'grouping':
        ('identifier',
         [('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           [('typedef', '*'),
            ('grouping', '*')] +
           data_def_stmts),
          ]),
    'container':
        ('identifier',
         [('must', '*'),
          ('presence', '?'),
          ('config', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           [('typedef', '*'),
            ('grouping', '*')] +
           data_def_stmts),
          ]),
    'leaf':
        ('identifier',
         [('type', '1'),
          ('units', '?'),
          ('must', '*'),
          ('default', '?'),
          ('config', '?'),
          ('mandatory', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'refined-leaf':
        ('identifier',
         [('type', '?'),
          ('units', '?'),
          ('must', '*'),
          ('default', '?'),
          ('config', '?'),
          ('mandatory', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'leaf-list':
        ('identifier',
         [('type', '1'),
          ('units', '?'),
          ('must', '*'),
          ('config', '?'),
          ('min-elements', '?'),
          ('max-elements', '?'),
          ('ordered-by', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'refined-leaf-list':
        ('identifier',
         [('type', '?'),
          ('units', '?'),
          ('must', '*'),
          ('config', '?'),
          ('min-elements', '?'),
          ('max-elements', '?'),
          ('ordered-by', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'list':
        ('identifier',
         [('must', '*'),
          ('key', '?'),
          ('unique', '*'),
          ('config', '?'),
          ('min-elements', '?'),
          ('max-elements', '?'),
          ('ordered-by', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           [('typedef', '*'),
            ('grouping', '*')] +
           data_def_stmts),
          ]),
    'key':
        ('key-arg', []),
    'unique':
        ('unique-arg', []),
    'choice':
        ('identifier',
         [('default', '?'),
          ('must', '*'),
          ('config', '?'),
          ('mandatory', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           [('case', '*'),
            ('container', '*'),
            ('leaf', '*'),
            ('leaf-list', '*'),
            ('list', '*'),
            ('anyxml', '*'),
            ]),
          ]),
    'case':
        ('identifier',
         [('must', '*'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           case_data_def_stmts),
          ]),
    'anyxml':
        ('identifier',
         [('config', '?'),
          ('mandatory', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'uses':
        ('identifier-ref',
         [('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           refinement_stmts),
          ]),
    'augment':
        ('augment-arg',
         [('when', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           [('case', '*')] +
           data_def_stmts),
          ]),
    'when':
        ('string', []),
    'rpc':
        ('identifier',
         [('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           [('typedef', '*'),
            ('grouping', '*')]),
          ('input', '?'),
          ('output', '?'),
          ]),
    'input':
        (None,
         [('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           [('typedef', '*'),
            ('grouping', '*')] +
           data_def_stmts),
          ]),
    'output':
        (None,
         [('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           [('typedef', '*'),
            ('grouping', '*')] +
           data_def_stmts),
          ]),
    'notification':
        ('identifier',
         [('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           [('typedef', '*'),
            ('grouping', '*')] +
           data_def_stmts),
          ]),
    }
"""YANG statement definitions.

Maps a statement name to a 2-tuple:
    (<argument type name> | None, <list of substatements> )
Each substatement is a 2-tuple:
    (<statement name>, <occurance>) |
    ('$interleave', <list of substatements to interleave>)
    ('$choice', <list of <case>>)
where <occurance> is one of: '?', '1', '+', '*'.
and <case> is a list of substatements
"""

# FIXME: possibly remove in the future, if we don't have these special classes
handler_map = {
    'import': lambda a,b,c,d: statements.Import(a,b,c,d),
    'include': lambda a,b,c,d: statements.Include(a,b,c,d),
    'revision': lambda a,b,c,d: statements.Revision(a,b,c,d),
    'typedef': lambda a,b,c,d: statements.Typedef(a,b,c,d),
    'grouping': lambda a,b,c,d: statements.Grouping(a,b,c,d),
    'extension': lambda a,b,c,d: statements.Extension(a,b,c,d),
    'argument': lambda a,b,c,d: statements.Argument(a,b,c,d),
    'type': lambda a,b,c,d: statements.Type(a,b,c,d),
    'range': lambda a,b,c,d: statements.Range(a,b,c,d),
    'length': lambda a,b,c,d: statements.Length(a,b,c,d),
    'pattern': lambda a,b,c,d: statements.Pattern(a,b,c,d),
    'path': lambda a,b,c,d: statements.Path(a,b,c,d),
    'must': lambda a,b,c,d: statements.Must(a,b,c,d),
    'enum': lambda a,b,c,d: statements.Enum(a,b,c,d),
    'bit': lambda a,b,c,d: statements.Bit(a,b,c,d),
    'leaf': lambda a,b,c,d: statements.Leaf(a,b,c,d),
    'leaf-list': lambda a,b,c,d: statements.LeafList(a,b,c,d),
    'container': lambda a,b,c,d: statements.Container(a,b,c,d),
    'list': lambda a,b,c,d: statements.List(a,b,c,d),
    'uses': lambda a,b,c,d: statements.Uses(a,b,c,d),
    'choice': lambda a,b,c,d: statements.Choice(a,b,c,d),
    'case': lambda a,b,c,d: statements.Case(a,b,c,d),
    'augment': lambda a,b,c,d: statements.Augment(a,b,c,d),
    'anyxml': lambda a,b,c,d: statements.AnyXML(a,b,c,d),
    'rpc': lambda a,b,c,d: statements.Rpc(a,b,c,d),
    'input': lambda a,b,c,d: statements.Input(a,b,c,d),
    'output': lambda a,b,c,d: statements.Output(a,b,c,d),
    'notification': lambda a,b,c,d: statements.Notification(a,b,c,d),
    }
                  

def chk_module_statements(ctx, module_stmt, canonical=False):
    """Validate the statement hierarchy according to the grammar.

    Return True if module is valid, False otherwise.
    """
    n = len(ctx.errors)
    _chk_stmts(ctx, module_stmt.pos, [module_stmt], top_stmts, canonical)
    return n == len(ctx.errors)

def _chk_stmts(ctx, pos, stmts, spec, canonical, is_refinement = False):
    for stmt in stmts:
        if not util.is_prefixed(stmt.keyword):
            match_res = _match_stmt(ctx, stmt, spec, canonical)
            if match_res == None:
                error.err_add(ctx.errors, stmt.pos,
                              'UNEXPECTED_KEYWORD', stmt.keyword);
            else:
                (_arg_type, subspec) = stmt_map[stmt.keyword]
                # FIXME: hack to handle the current situation where some
                # stmts' grammar is context dependant.  I hope this gets
                # fixed with a special 'refine' statement.
                if is_refinement:
                    if stmt.keyword == 'leaf':
                        (_arg_type, subspec) = stmt_map['refined-leaf']
                    elif stmt.keyword == 'leaf-list':
                        (_arg_type, subspec) = stmt_map['refined-leaf-list']
                if stmt.keyword == 'uses':
                    is_refinement = True
                _chk_stmts(ctx, stmt.pos, stmt.substmts, subspec, canonical,
                           is_refinement)
                spec = match_res
        else:
            # FIXME: handle plugin-registered extension grammar
            _chk_stmts(ctx, stmt.pos, stmt.substmts, [('$any', '*')], canonical,
                       is_refinement)
        # update last know position
        pos = stmt.pos
    # any non-optional statements left are errors
    for (keywd, occurance) in spec:
        if occurance == '1' or occurance == '+':
            error.err_add(ctx.errors, pos, 'EXPECTED_KEYWORD', keywd)

def _match_stmt(ctx, stmt, spec, canonical):
    """Match stmt against the spec.

    Return None | spec'
    spec' is an updated spec with the matching spec consumed
    """
    i = 0
    while i < len(spec):
        (keywd, occurance) = spec[i]
        if keywd == '$any':
            return spec
        elif keywd == stmt.keyword:
            if occurance == '1' or occurance == '?':
                # consume this match
                if canonical == True:
                    return spec[i+1:]
                else:
                    return spec[:i] + spec[i+1:]
            if occurance == '+':
                # mark that we have found the one that was needed
                c = (keywd, '*')
                if canonical == True:
                    return [c] + spec[i+1:]
                else:
                    return spec[:i] + [c] + spec[i+1:]
            else:
                # occurane == '*'
                if canonical == True:
                    return spec[i:]
                else:
                    return spec
        elif keywd == '$choice':
            cases = occurance
            j = 0
            while j < len(cases):
                # check if this alternative matches - check for a
                # match with each optional keyword
                save_errors = ctx.errors
                match_res = _match_stmt(ctx, stmt, cases[j], canonical)
                if match_res != None:
                    # this case branch matched, use it
                    # remove the choice and add res to the spec
                    return spec[:i] + match_res + spec[i+1:]
                # we must not report errors on non-matching branches
                ctx.errors = save_errors
                j += 1
        elif keywd == '$interleave':
            cspec = occurance
            match_res = _match_stmt(ctx, stmt, cspec, canonical)
            if match_res != None:
                # we got a match
                return spec
        elif keywd == '$cut':
            # any non-optional statements left are errors
            for (keywd, occurance) in spec[:i]:
                if occurance == '1' or occurance == '+':
                    error.err_add(ctx.errors, stmt.pos, 'UNEXPECTED_KEYWORD_1',
                                  (stmt.keyword, keywd))
            # consume them so we don't report the same error again
            spec = spec[i:]
            i = 0
        elif canonical == True:
            if occurance == '1' or occurance == '+':
                error.err_add(ctx.errors, stmt.pos, 'UNEXPECTED_KEYWORD_1',
                              (stmt.keyword, keywd))
                # consume it so we don't report the same error again
                spec = spec[i:]
                i = 0
        # check next in spec
        i += 1
    return None

def sort_canonical(keyword, stmts):
    """Sort all `stmts` in the canonical order defined by `keyword`.
    Return the sorted list.  The `stmt` list is not modified.
    If `keyword` does not have a canonical order, the list is returned
    as is.
    """
    def flatten_spec(spec):
        res = []
        for (kw, s) in spec:
            if kw == '$interleave':
                res.extend(flatten_spec(s))
            elif kw == '$choice':
                for branch in s:
                    res.extend(flatten_spec(branch))
            else:
                res.append((kw,s))
        return res

    try:
        (_arg_type, subspec) = stmt_map[keyword]
    except KeyError:
        return stmts
    res = []
    for (kw, _spec) in flatten_spec(subspec):
        res.extend([stmt for stmt in stmts if stmt.keyword == kw])
    # then copy all other statements (extensions)
    res.extend([stmt for stmt in stmts if stmt not in res])
    return res
