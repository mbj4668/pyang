"""Description of YANG & YIN grammar."""

from pyang import main
from pyang import util
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

# FIXME: move to util
def is_prefixed(identifier):
    return type(identifier) == type(()) and len(identifier) == 2


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
"""Special substatement which marks the end of a block in which
   the substatements may occur in any order."""

top_stmts = [
    ('$choice', [[('module', '1')],
                 [('submodule', '1')]])
]
"""top-level statements"""

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
        ('identifier',
         [('$choice',
           [[('range', '?')],
            [('length', '?'),
             ('pattern', '?')],
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
        ('lentgh-arg',
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
         [('status', '?'),
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
           # FIXME: should handle input & output here, unless the
           # spec is fixed (see mail thread)
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
"""YANG statement definitions

Maps a statement name to a 2-tuple:
    (<argument type name> | None, <list of substatements> )
Each substatement is a 2-tuple:
    (<statement name>, <occurance>) |
    ('$interleave', <list of substatements to interleave>)
    ('$choice', <list of <case>>)
where <occurance> is one of: '?', '1', '+', '*'.
and <case> is a list of substatements
"""

# FIXME: this map is not correct yet
# possibly remove in the future, if we don't have these special classes
handler_map = {
    'module':
        lambda parent, pos, arg: main.Module(pos, None, arg, is_submodule=False),
    'submodule':
        lambda parent, pos, arg: main.Module(pos, arg, is_submodule=True),
    'typedef':
        lambda parent, pos, arg: main.Typedef(parent, pos, None, arg),
    }
                  

def chk_module_statements(ctx, module_stmt, canonical=False):
    """Validates the statement hierarchy according to the grammar.

    ret: True if module is valid, False otherwise.
    """
    
    n = len(ctx.errors)
    if canonical:
        _chk_stmts_canonical(ctx, [module_stmt], top_stmts)
    else:
        _chk_stmts(ctx, [module_stmt], top_stmts)
    return n == len(ctx.errors)

def _chk_stmts(ctx, stmts, spec):
    for stmt in stmts:
        if not is_prefixed(stmt.keyword):
            match_res = _match_stmt(ctx, stmt, spec)
            if match_res == None:
                main.err_add(ctx.errors, stmt.pos,
                             'UNEXPECTED_KEYWORD', stmt.keyword);
            else:
                (_arg_type, subspec) = stmt_map[stmt.keyword]
                _chk_stmts(ctx, stmt.substmts, subspec)
                spec = match_res
        else:
            _chk_stmts(ctx, stmt.substmts, [])
    # any non-optional statements left are errors
    for (keywd, occurance) in spec:
        if occurance == '1' or occurance == '+':
            main.err_add(ctx.errors, stmt.pos, 'UNEXPECTED_KEYWORD_1',
                         (stmt.keyword, keywd))

def _match_stmt(ctx, stmt, spec):
    """tries to match stmt against the spec.

    ret: None | spec'
    spec' is an updated spec with the matching spec consumed
    """

    i = 0
    prev_cut = 0
    while i < len(spec):
        (keywd, occurance) = spec[i]
        if keywd == stmt.keyword:
            if occurance == '1' or occurance == '?':
                return spec[:i] + spec[i+1:]
            if occurance == '+':
                c = (keywd, '*')
                return spec[:i] + [c] + spec[i+1:]
            else:
                return spec
        elif keywd == '$choice':
            cases = occurance
            j = 0
            while j < len(cases):
                # check if this alternative matches - check for a
                # match with each optional keyword
                match_res = _match_stmt(ctx, stmt, cases[j])
                if match_res != None:
                    # this case branch matched, use it
                    # remove the choice and add res to the spec
                    return spec[:i] + match_res + spec[i+1:]
                j = j + 1
        elif keywd == '$interleave':
            cspec = occurance
            match_res = _match_stmt(ctx, stmt, cspec)
            if match_res != None:
                # we got a match
                return spec
        elif keywd == '$cut':
            # any non-optional statements left are errors
            for (keywd, occurance) in spec[prev_cut:i]:
                if occurance == '1' or occurance == '+':
                    main.err_add(ctx.errors, stmt.pos, 'UNEXPECTED_KEYWORD_1',
                                 (stmt.keyword, keywd))
            prev_cut = i + 1
        # check next in spec
        i = i + 1
    return None

## FIXME: it *got* to be possible to make this simpler.
##        idea: use the same alg. as above; do a version of _match_stmt
##        for the canonical order.
def _chk_stmts_canonical(ctx, stmts, spec, recurse=True):
    i = 0
    j = 0
    # first loop over each specificed child, and compare with the
    # statements we've got
    while j < len(spec):
        # skip extensions; they are always allowed
        # FIXME: check w/ plugin-registered grammar
        while i < len(stmts) and is_prefixed(stmts[i].keyword):
            i += 1
        if i == len(stmts):
            break
        (keywd, occurance) = spec[j]
        if keywd == '$cut':
            pass
        elif keywd == '$interleave':
            chspec = occurance
            # check that each stmt is in the interleave spec
            # this code does not check occurance within the interleave spec,
            # but this is currently ok, since we don't allow anything but '*'
            # in an interleave child spec
            while (i < len(stmts) and
                   (is_prefixed(stmts[i].keyword) or
                    not util.keysearch(stmts[i].keyword, 1, chspec))):
                i += 1
            if i == len(stmts):
                j += 1
                break
        elif keywd == '$choice':
            cases = occurance
            case_n = 0
            found = False
            while not found and case_n < len(cases):
                # check if this case branch matches - check for a
                # match with each optional keyword
                k = 0
                while not found and k < len(cases[case_n]):
                    if stmts[i].keyword == cases[case_n][k][0]:
                        # this choice alternative matched, use it
                        chspec = cases[case_n]
                        found = True
                    occ = cases[case_n][k][1]
                    if (occ == '+' or occ == '1'):
                        # this stmt was mandatory but not found; check
                        # next case branch
                        break
                    k += 1
                case_n += 1
            if not found:
                main.err_add(ctx.errors, stmts[i].pos,
                             'UNEXPECTED_KEYWORD', stmts[i].keyword)
            else:
                # this code assumes that there are no other stmts
                # allowed after the choice.
                _chk_stmts_canonical(ctx, stmts[i:], chspec, recurse=False)
                i = len(stmts)
                j = len(spec)
                break
        elif stmts[i].keyword == keywd:
            i += 1
            if occurance == '*' or occurance == '+':
                # skip multi statements, and skip extensions
                while i < len(stmts) and (is_prefixed(stmts[i].keyword) or
                                          stmts[i].keyword == keywd):
                    i += 1
            if i == len(stmts):
                j += 1
                break
        elif occurance == '1' or occurance == '+':
            main.err_add(ctx.errors, stmts[i].pos,
                         'UNEXPECTED_KEYWORD_1', (stmts[i].keyword, keywd))
        j += 1

    # any statements left are errors
    for stmt in stmts[i:]:
        main.err_add(ctx.errors, stmt.pos,
                     'UNEXPECTED_KEYWORD', stmt.keyword)

    # any non-optional statements in the spec are error
    for (keywd, occurance) in spec[j:]:
        if occurance == '1' or occurance == '+':
            # FIXME: need pos from parent?
            main.err_add(ctx.errors, None, 'EXPECTED_KEYWORD', keywd)
        
    # next, recursively check each statement to the spec
    if recurse:
        for stmt in stmts:
            if is_prefixed(stmt.keyword):
                subspec = []
            else:
                (_arg_type, subspec) = stmt_map[stmt.keyword]
            _chk_stmts_canonical(ctx, stmt.substmts, subspec)
