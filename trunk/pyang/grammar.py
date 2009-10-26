"""Description of YANG & YIN grammar."""

from pyang import util
from pyang import error
import syntax

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
]

case_data_def_stmts = [
    ('container', '*'),
    ('leaf', '*'),
    ('leaf-list', '*'),
    ('list', '*'),
    ('anyxml', '*'),
    ('uses', '*'),
]

body_stmts = [
    ('$interleave',
     [('extension', '*'),
      ('feature', '*'),
      ('identity', '*'),
      ('typedef', '*'),
      ('grouping', '*'),
      ('rpc', '*'),
      ('notification', '*'),
      ('deviation', '*'),
      ('augment', '*'),
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

def add_stmt(stmt, (arg, rules)):
    """Use by plugins to add grammar for an extension statement."""
    stmt_map[stmt] = (arg, rules)

def add_to_stmts_rules(stmts, rules):
    """Use by plugins to add extra rules to the existing rules for
    a statement."""
    for s in stmts:
        (arg, rules0) = stmt_map[s]
        stmt_map[s] = (arg, rules0 + rules)

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
         [('prefix', '1'),
          ('revision-date', '?')]),
    'include':
        ('identifier',
         [('revision-date', '?')]),
    'revision-date':
        ('date', []),
    'revision':
        ('date',
         [('description', '?'),
          ('reference', '?')]),
    'belongs-to':
        ('identifier',
         [('prefix', '1')]),
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
    'feature':
        ('identifier',
         [('if-feature', '*'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?')]),
    'if-feature':
        ('identifier-ref', []),
    'identity':
        ('identifier',
         [('base', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?')]),
    'base':
        ('identifier-ref', []),
    'require-instance':
        ('boolean', []),
    'fraction-digits':
        ('fraction-digits-arg', []),
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
           [[('fraction-digits', '?'),
             ('range', '?')],
            [('length', '?'),
             ('pattern', '*')],
            [('enum', '*')],
            [('bit', '*')],
            [('path', '?'),
             ('require-instance', '?')],
            [('require-instance', '?')],
            [('base', '?')],
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
        ('enum-arg',
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
        ('non-negative-integer', []),
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
        ('non-negative-integer', []),
    'max-elements':
        ('max-value', []),
    'value':
        ('integer', []),
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
         [('when', '?'),
          ('if-feature', '*'),
          ('must', '*'),
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
         [('when', '?'),
          ('if-feature', '*'),
          ('type', '1'),
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
         [('when', '?'),
          ('if-feature', '*'),
          ('type', '1'),
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
         [('when', '?'),
          ('if-feature', '*'),
          ('must', '*'),
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
         [('when', '?'),
          ('if-feature', '*'),
          ('default', '?'),
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
         [('when', '?'),
          ('if-feature', '*'),
          ('must', '*'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           case_data_def_stmts),
          ]),
    'anyxml':
        ('identifier',
         [('when', '?'),
          ('if-feature', '*'),
          ('config', '?'),
          ('mandatory', '?'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ]),
    'uses':
        ('identifier-ref',
         [('when', '?'),
          ('if-feature', '*'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('refine', '*'),
          ('augment', '*'),
          ]),
    'refine':
        ('descendant-schema-nodeid',
         [('$interleave',
           [('must', '*'),
            ('presence', '?'),
            ('default', '?'),
            ('config', '?'),
            ('mandatory', '?'),
            ('min-elements', '?'),
            ('max-elements', '?'),
            ('description', '?'),
            ('reference', '?'),
            ]),
          ]),
    'augment':
        ('schema-nodeid',
         [('when', '?'),
          ('if-feature', '*'),
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
         [('if-feature', '*'),
          ('status', '?'),
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
         [('if-feature', '*'),
          ('status', '?'),
          ('description', '?'),
          ('reference', '?'),
          ('$interleave',
           [('typedef', '*'),
            ('grouping', '*')] +
           data_def_stmts),
          ]),
    'deviation':
        ('absolute-schema-nodeid',
         [('description', '?'),
          ('reference', '?'),
          ('deviate', '*')]),
    'deviate':
        ('deviate-arg',
         [('type', '?'),
          ('units', '?'),
          ('must', '*'),
          ('unique', '*'),
          ('default', '?'),
          ('config', '?'),
          ('mandatory', '?'),
          ('min-elements', '?'),
          ('max-elements', '?'),
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

extension_modules = []
"""A list of YANG module names for which extensions are validated"""

def register_extension_module(modname):
    """Add a modulename to the list of known YANG module where extensions
    are defined.
    Used by plugins to register that they implement extensions from
    a particular module."""
    extension_modules.append(modname)

def chk_module_statements(ctx, module_stmt, canonical=False):
    """Validate the statement hierarchy according to the grammar.

    Return True if module is valid, False otherwise.
    """
    return chk_statement(ctx, module_stmt, top_stmts, canonical)

def chk_statement(ctx, stmt, grammar, canonical=False):
    """Validate `stmt` according to `grammar`.

    Marks each statement in the hirearchy with stmt.is_grammatically_valid,
    which is a boolean.

    Return True if stmt is valid, False otherwise.
    """
    n = len(ctx.errors)
    _chk_stmts(ctx, stmt.pos, [stmt], None, grammar, canonical)
    return n == len(ctx.errors)

def _chk_stmts(ctx, pos, stmts, parent, spec, canonical):
    for stmt in stmts:
        stmt.is_grammatically_valid = False
        if not util.is_prefixed(stmt.keyword):
            chk_grammar = True
        else:
            (modname, _identifier) = stmt.keyword
            if modname in extension_modules:
                chk_grammar = True
            else:
                chk_grammar = False
        if chk_grammar == True:
            match_res = _match_stmt(ctx, stmt, spec, canonical)
        else:
            match_res = None
        if match_res is None and chk_grammar == True:
            error.err_add(ctx.errors, stmt.pos, 'UNEXPECTED_KEYWORD', 
                          util.keyword_to_str(stmt.raw_keyword))
        elif match_res is not None and chk_grammar == True:
            try:
                (arg_type, subspec) = stmt_map[stmt.keyword]
            except KeyError:
                error.err_add(ctx.errors, stmt.pos, 'UNEXPECTED_KEYWORD', 
                              util.keyword_to_str(stmt.raw_keyword))
                return
            # verify the statement's argument
            if arg_type is None and stmt.arg is not None:
                error.err_add(ctx.errors, stmt.pos,
                              'UNEXPECTED_ARGUMENT', stmt.arg)
            elif arg_type is not None and stmt.arg is None:
                error.err_add(ctx.errors, stmt.pos,
                              'EXPECTED_ARGUMENT',
                              util.keyword_to_str(stmt.keyword))
            elif (arg_type is not None and arg_type != 'string' and
                  syntax.arg_type_map[arg_type](stmt.arg) == False):
                error.err_add(ctx.errors, stmt.pos,
                              'BAD_VALUE', (stmt.arg, arg_type))
            else:
                stmt.is_grammatically_valid = True

            _chk_stmts(ctx, stmt.pos, stmt.substmts, stmt, subspec, canonical)
            spec = match_res
        else:
            # unknown extension
            stmt.is_grammatically_valid = True
            _chk_stmts(ctx, stmt.pos, stmt.substmts, stmt, 
                       [('$any', '*')], canonical)
        # update last know position
        pos = stmt.pos
    # any non-optional statements left are errors
    for (keywd, occurance) in spec:
        if occurance == '1' or occurance == '+':
            if parent is None:
                error.err_add(ctx.errors, pos, 'EXPECTED_KEYWORD',
                              util.keyword_to_str(keywd))
            else:
                error.err_add(ctx.errors, pos, 'EXPECTED_KEYWORD_2',
                              (util.keyword_to_str(keywd),
                               util.keyword_to_str(parent.raw_keyword)))

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
        elif util.is_prefixed(stmt.keyword):
            # allow extension statements mixed with these
            # set canonical to False in this call to just remove the
            # matching stmt from the spec
            match_res = _match_stmt(ctx, stmt, spec[i+1:], False)
            if match_res != None:
                return spec[:i+1] + match_res
            else:
                return None
        elif keywd == '$cut':
            # any non-optional statements left are errors
            for (keywd, occurance) in spec[:i]:
                if occurance == '1' or occurance == '+':
                    error.err_add(ctx.errors, stmt.pos, 'UNEXPECTED_KEYWORD_1',
                                  (util.keyword_to_str(stmt.raw_keyword),
                                   util.keyword_to_str(keywd)))
            # consume them so we don't report the same error again
            spec = spec[i:]
            i = 0
        elif canonical == True:
            if occurance == '1' or occurance == '+':
                error.err_add(ctx.errors, stmt.pos, 'UNEXPECTED_KEYWORD_1',
                              (util.keyword_to_str(stmt.raw_keyword),
                               util.keyword_to_str(keywd)))
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
