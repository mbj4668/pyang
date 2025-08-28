''' DTNMA-AMM Plugin
Copyright (c) 2023-2024 The Johns Hopkins University Applied Physics
Laboratory LLC.

This plugin implements the DTNMA Application Management Model (AMM) from
[I-D.ietf-dtn-adm-yang] as a collection of extensions and the module itself.
'''
from dataclasses import dataclass, field
import io
from typing import List, Tuple
from pyang import plugin, context, statements, syntax, grammar, error

# Use ARI processing library when possible
try:
    from ace import ari_text, ReferenceARI
except ImportError:
    ari_text = None

MODULE_NAME = 'ietf-amm'
''' Extension module name to hook onto '''
MODULE_PREFIX = 'amm'
''' Extension prefix '''


class DtnmaAmmPlugin(plugin.PyangPlugin):
    ''' This plugin is just validation. '''


def pyang_plugin_init():
    ''' Called by plugin framework to initialize this plugin.
    '''
    plugin.register_plugin(DtnmaAmmPlugin())

    # Register that we handle extensions from the associated YANG module
    grammar.register_extension_module(MODULE_NAME)
    # Extension argument types
    syntax.add_arg_type('ARI', AriChecker())

    for ext in MODULE_EXTENSIONS:
        name = (MODULE_NAME, ext.keyword)
        grammar.add_stmt(name, (ext.typename, ext.subs))
        if ext.subs:
            statements.add_keyword_with_children(name)

    # ADM enumeration only at module level and optional
    # allowing for non-ADM YANG modules
    grammar.add_to_stmts_rules(
        ['module'],
        [((MODULE_NAME, 'enum'), '?')],
    )
#    rules = grammar.stmt_map['module'][1]
#    rules.insert(rules.index(('prefix', '1')) + 1, ((MODULE_NAME, 'enum'), '?'))

    # AMM object extensions with preferred canonicalization order
    grammar.add_to_stmts_rules(
        ['module', 'submodule'],
        [('$interleave', [(name, '*') for name in AMM_OBJ_NAMES])],
    )
    # order of semantic type statements must be preserved because union and
    # dlist both depend on order
    for name in (AMM_OBJ_NAMES + AMM_ORDERED_NAMES):
        grammar.data_def_stmts.append((name, '*'))

    # Allow these to be present in "grouping" and for "uses"
    grammar.add_to_stmts_rules(
        ['grouping'],
        [(name, '*') for name in AMM_GROUPING_NAMES]
    )
    for name in AMM_GROUPING_NAMES:
        statements.add_data_keyword(name)

    statements.add_validation_fun(
        'grammar',
        ['namespace'],
        _stmt_check_namespace
    )
    statements.add_validation_fun(
        'grammar',
        ['module'],
        _stmt_check_mod_enum
    )
    statements.add_validation_fun(
        'grammar',
        AMM_OBJ_NAMES,
        _stmt_check_obj_enum
    )
    statements.add_validation_fun(
        'grammar',
        ['module', 'submodule'],
        _stmt_check_module_objs
    )
    statements.add_validation_fun(
        'grammar',
        [(MODULE_NAME, 'int-labels')],
        _stmt_check_intlabels
    )
    statements.add_validation_fun(
        'grammar',
        # Statements with 'ARI' type above
        [
            (MODULE_NAME, 'type'),
            (MODULE_NAME, 'base'),
            (MODULE_NAME, 'init-value'),
            (MODULE_NAME, 'default')
        ],
        _stmt_check_ari_import_use
    )
    statements.add_validation_fun(
        'unique_name',
        ['module'],
        _stmt_check_enum_unique
    )

    # Register special error codes
    error.add_error_code(
        'AMM_MODULE_NS', 1,
        "An ADM module must have an ARI namespace, not %s"
    )
    error.add_error_code(
        'AMM_MODULE_OBJS', 1,
        "An ADM module cannot contain a statement %r named \"%s\""
    )
    error.add_error_code(
        'AMM_MODULE_ENUM', 4,
        "The ADM module %s must contain an amm:enum statement"
    )
    error.add_error_code(
        'AMM_OBJ_ENUM', 4,
        "The ADM object %s named \"%s\" should contain an amm:enum statement"
    )
    error.add_error_code(
        'AMM_OBJ_ENUM_UNIQUE', 1,
        "An amm:enum must be unique among all %s objects, has value %s"
    )
    error.add_error_code(
        'AMM_INTLABELS', 1,
        "An amm:int-labels must have either 'enum' or 'bit' statements %s"
    )
    error.add_error_code(
        'AMM_INTLABELS_ENUM_VALUE', 1,
        "An amm:int-labels 'enum' statement %r must have a unique 'value'"
    )
    error.add_error_code(
        'AMM_INTLABELS_BIT_VALUE', 1,
        "An amm:int-labels 'bit' statement %r must have a unique 'position'"
    )


@dataclass
class Ext:
    ''' Define an extension schema.

    :param keyword: Keyword name.
    :param occurrence: Occurrence flag
    :param typename: Argument type name (or None)
    :param subs: sub-statement keywords
    '''
    keyword: str
    typename: str
    subs: List[Tuple[object]] = field(default_factory=list)


OBJ_SUBS_PRE = [
    ('if-feature', '?'),
    ((MODULE_NAME, 'enum'), '?'),
    ('status', '?'),
    ('description', '?'),
    ('reference', '?'),
]
''' Substatements at the front of object definitions. '''

AMM_OBJ_NAMES = (
    (MODULE_NAME, 'typedef'),
    (MODULE_NAME, 'ident'),
    (MODULE_NAME, 'const'),
    (MODULE_NAME, 'edd'),
    (MODULE_NAME, 'var'),
    (MODULE_NAME, 'ctrl'),
    (MODULE_NAME, 'oper'),
)
''' AMM object types at the module/submodule level. '''

AMM_ORDERED_NAMES = (
    # definition substatements
    (MODULE_NAME, 'parameter'),
    (MODULE_NAME, 'operand'),
    (MODULE_NAME, 'result'),
    # semantic type statements
    (MODULE_NAME, 'type'),
    (MODULE_NAME, 'ulist'),
    (MODULE_NAME, 'dlist'),
    (MODULE_NAME, 'umap'),
    (MODULE_NAME, 'tblt'),
    (MODULE_NAME, 'union'),
    (MODULE_NAME, 'seq'),
)
''' All data-like keywords to preserve order in canonical encoding. '''

AMM_GROUPING_NAMES = (
    (MODULE_NAME, 'parameter'),
    (MODULE_NAME, 'operand'),
    (MODULE_NAME, 'result'),
)
''' Extensions allowed in grouping statements. '''

MODULE_STMT_ALLOW = (
    '_comment',
    'contact',
    'description',
    'extension',
    'feature',
    'grouping',
    'import',
    'include',
    'namespace',
    'organization',
    'prefix',
    'reference',
    'revision',
    'yang-version',
    (MODULE_NAME, 'enum'),
) + AMM_OBJ_NAMES
''' Allowed statements at the ADM module level. '''


def type_use(parent:str) -> List:
    ''' Get a list of type-use substatements for a particular parent.

    :param parent: The parent statement keyword.
    :return: Choice of semantic type substatements.
    '''
    opts = [
        [((MODULE_NAME, 'type'), '1')],
        [((MODULE_NAME, 'ulist'), '1')],
        [((MODULE_NAME, 'dlist'), '1')],
        [((MODULE_NAME, 'umap'), '1')],
        [((MODULE_NAME, 'tblt'), '1')],
        [((MODULE_NAME, 'union'), '1')],
    ]
    if parent in ('dlist', 'parameter', 'operand'):
        opts.append(
            [((MODULE_NAME, 'seq'), '*')]
        )
    return [
        ('$choice', opts),
    ]


# List of extension statements defined by the module
MODULE_EXTENSIONS = (
    # ARI enum assignment
    Ext('enum', 'non-negative-integer'),

    # Type structure extensions
    Ext('type', 'ARI',
        subs=[
            ('units', '?'),
            ('range', '?'),
            ('length', '?'),
            ('pattern', '?'),
            ((MODULE_NAME, 'int-labels'), '?'),
            ((MODULE_NAME, 'cddl'), '?'),
            ((MODULE_NAME, 'base'), '?'),
            ('description', '?'),
            ('reference', '?'),
        ],
    ),
    Ext('ulist', None,
        subs=(
            [
                ('min-elements', '?'),
                ('max-elements', '?'),
                ('description', '?'),
                ('reference', '?'),
            ]
            +type_use('ulist')
        ),
    ),
    Ext('dlist', None,
        subs=[
            ('description', '?'),
            ('reference', '?'),
            ('$interleave', type_use('dlist')),
        ],
    ),
    Ext('seq', None,
        subs=(
            [
                ('min-elements', '?'),
                ('max-elements', '?'),
                ('description', '?'),
                ('reference', '?'),
            ]
            +type_use('seq')
        ),
    ),
    Ext('umap', None,
        subs=[
            ((MODULE_NAME, 'keys'), '?'),
            ((MODULE_NAME, 'values'), '?'),
            ('description', '?'),
            ('reference', '?'),
        ]
    ),
    Ext('keys', None,
        subs=(
            [
                ('description', '?'),
                ('reference', '?'),
            ]
            +type_use('keys')
        )
    ),
    Ext('values', None,
        subs=(
            [
                ('description', '?'),
                ('reference', '?'),
            ]
            +type_use('values')
        )
    ),
    Ext('tblt', None,
        subs=[
            ((MODULE_NAME, 'key'), '?'),
            ((MODULE_NAME, 'unique'), '*'),
            ('min-elements', '?'),
            ('max-elements', '?'),
            ('description', '?'),
            ('reference', '?'),
            ((MODULE_NAME, 'column'), '*'),
        ],
    ),
    Ext('column', 'identifier',
        subs=(
            [
                ('description', '?'),
                ('reference', '?'),
            ]
            +type_use('column')
        ),
    ),
    Ext('key', 'string'),
    Ext('unique', 'string'),
    Ext('union', None,
        subs=[
            ('description', '?'),
            ('reference', '?'),
            ('$interleave', type_use('union')),
        ],
    ),
    # Type narrowing extensions
    Ext('cddl', 'string'),
    Ext('int-labels', None,
        subs=[
            ('enum', '*'),
            ('bit', '*'),
        ],
    ),

    Ext('parameter', 'identifier',
        subs=(
            [
                ('description', '?'),
                ('reference', '?'),
                ((MODULE_NAME, 'default'), '?'),
            ]
            +type_use('parameter')
        ),
    ),
    Ext('default', 'ARI',
        subs=[
            ('description', '?'),
            ('reference', '?'),
        ],
    ),

    # managed objects
    Ext('typedef', 'identifier',
        subs=(
            OBJ_SUBS_PRE
            +type_use('typedef')
        ),
    ),

    Ext('ident', 'identifier',
        subs=(
            OBJ_SUBS_PRE
            +[
                ((MODULE_NAME, 'parameter'), '*'),
                ((MODULE_NAME, 'base'), '*'),
                ('uses', '*'),
            ]
        ),
    ),
    Ext('base', 'ARI'),

    Ext('const', 'identifier',
        subs=(
            OBJ_SUBS_PRE
            +[
                ((MODULE_NAME, 'parameter'), '*'),
                ((MODULE_NAME, 'init-value'), '1'),
                ('uses', '*'),
            ]
            +type_use('const')
        ),
    ),
    Ext('init-value', 'ARI'),

    Ext('edd', 'identifier',
        subs=(
            OBJ_SUBS_PRE
            +[
                ((MODULE_NAME, 'parameter'), '*'),
                ('uses', '*'),
            ]
            +type_use('edd')
        ),
    ),

    Ext('var', 'identifier',
        subs=(
            OBJ_SUBS_PRE
            +type_use('var')
            +[
                ((MODULE_NAME, 'parameter'), '*'),
                ((MODULE_NAME, 'init-value'), '?'),
                ('uses', '*'),
            ]
        ),
    ),

    Ext('ctrl', 'identifier',
        subs=(
            OBJ_SUBS_PRE + [
                ((MODULE_NAME, 'parameter'), '*'),
                ((MODULE_NAME, 'result'), '?'),
                ('uses', '*'),
            ]
        ),
    ),
    Ext('result', 'identifier',
        subs=(
            [
                ('description', '?'),
                ('reference', '?'),
            ]
            +type_use('result')
        ),
    ),

    Ext('oper', 'identifier',
        subs=(
            OBJ_SUBS_PRE
            +[
                ((MODULE_NAME, 'parameter'), '*'),
                ((MODULE_NAME, 'operand'), '*'),
                ((MODULE_NAME, 'result'), '?'),  # can be provided via uses
                ('uses', '*'),
            ]
        ),
    ),
    Ext('operand', 'identifier',
        subs=(
            [
                ('description', '?'),
                ('reference', '?'),
            ]
            +type_use('operand')
        ),
    ),
)


class AriChecker:
    ''' Verify that text is a well-formed ARI.

    If the :py:mod:`ace` module is not available this assumes any ARI is valid.
    '''

    def __init__(self):
        if ari_text:
            self._dec = ari_text.Decoder()
        else:
            self._dec = None

    def __call__(self, val:str) -> bool:
        if self._dec is None:
            return True

        buf = io.StringIO(val)
        try:
            self._dec.decode(buf)
            return True
        except:
            return False


def _stmt_check_namespace(ctx:context.Context, stmt:statements.Statement):
    ''' Verify namespace conforms to to an ADM module. '''
    if not ari_text:
        return
    if not stmt.arg.startswith('ari:'):
        return

    try:
        ns_ref = ari_text.Decoder().decode(io.StringIO(stmt.arg))
    except ari_text.ParseError:
        ns_ref = None

    if (not isinstance(ns_ref, ReferenceARI)
        or ns_ref.ident.ns_id != stmt.main_module().arg.casefold()
        or ns_ref.ident.type_id is not None
        or ns_ref.ident.obj_id is not None):
        error.err_add(ctx.errors, stmt.pos, 'AMM_MODULE_NS',
                      (stmt.arg))


def _stmt_check_ari_import_use(ctx:context.Context, stmt:statements.Statement):
    ''' Mark modules as used based on ARI content. '''
    if not ari_text:
        return

    mod_stmt = stmt.main_module()

    def visitor(ari):
        if not isinstance(ari, ReferenceARI):
            return

        mod_prefix = [
            key
            for key, (name, _rev) in mod_stmt.i_prefixes.items()
            if name == ari.ident.ns_id
        ]
        if mod_prefix:
            if mod_prefix[0] in mod_stmt.i_unused_prefixes:
                del mod_stmt.i_unused_prefixes[mod_prefix[0]]
        else:
            mod_stmt.i_missing_prefixes[ari.ident.ns_id] = True

    ari = ari_text.Decoder().decode(io.StringIO(stmt.arg))
    ari.visit(visitor)


def _stmt_check_mod_enum(ctx:context.Context, stmt:statements.Statement):
    ''' Check an enum value for an ADM module. '''
    enum_stmt = stmt.search_one((MODULE_NAME, 'enum'))
    if not enum_stmt:
        error.err_add(ctx.errors, stmt.pos, 'AMM_MODULE_ENUM',
                      (stmt.arg))


def _stmt_check_module_objs(ctx:context.Context, stmt:statements.Statement):
    ''' Verify only AMP objects are present in the module. '''
    if stmt.keyword != 'module':
        return
    ns_stmt = stmt.search_one('namespace')
    if ns_stmt is None or not ns_stmt.arg.startswith('ari:'):
        return

    allowed = frozenset(MODULE_STMT_ALLOW)
    for sub in stmt.substmts:
        if sub.keyword not in allowed:
            error.err_add(ctx.errors, sub.pos, 'AMM_MODULE_OBJS',
                          (sub.keyword, sub.arg))


def _stmt_check_obj_enum(ctx:context.Context, stmt:statements.Statement):
    ''' Check an enum value for an ADM object. '''
    enum_stmt = stmt.search_one((MODULE_NAME, 'enum'))
    if not enum_stmt:
        error.err_add(ctx.errors, stmt.pos, 'AMM_OBJ_ENUM',
                      (stmt.raw_keyword[1], stmt.arg))


def _stmt_check_intlabels(ctx:context.Context, stmt:statements.Statement):
    ''' Verify either enum or bit but not both are present. '''
    has_enum = stmt.search_one('enum') is not None
    has_bit = stmt.search_one('bit') is not None
    if not has_enum and not has_bit:
        error.err_add(ctx.errors, stmt.pos, 'AMM_INTLABELS',
                      (''))
    elif has_enum and has_bit:
        error.err_add(ctx.errors, stmt.pos, 'AMM_INTLABELS',
                      ('but not both'))

    seen = set()
    for enum_stmt in stmt.search('enum'):
        val_stmt = enum_stmt.search_one('value')
        if val_stmt is None:
            error.err_add(ctx.errors, enum_stmt.pos, 'AMM_INTLABELS_ENUM_VALUE',
                          enum_stmt.arg)
        else:
            got = int(val_stmt.arg)
            if got in seen:
                error.err_add(ctx.errors, enum_stmt.pos, 'AMM_INTLABELS_ENUM_VALUE',
                              enum_stmt.arg)
            seen.add(got)

    seen = set()
    for enum_stmt in stmt.search('bit'):
        pos_stmt = enum_stmt.search_one('position')
        if pos_stmt is None:
            error.err_add(ctx.errors, enum_stmt.pos, 'AMM_INTLABELS_BIT_VALUE',
                          enum_stmt.arg)
        else:
            got = int(pos_stmt.arg)
            if got in seen:
                error.err_add(ctx.errors, enum_stmt.pos, 'AMM_INTLABELS_BIT_VALUE',
                              enum_stmt.arg)
            seen.add(got)


def _stmt_check_enum_unique(ctx:context.Context, stmt:statements.Statement):
    for obj_kywd in AMM_OBJ_NAMES:
        seen_enum = set()
        for obj_stmt in stmt.search(obj_kywd):
            enum_stmt = obj_stmt.search_one((MODULE_NAME, 'enum'))
            if enum_stmt is None:
                continue
            enum_val = int(enum_stmt.arg)
            if enum_val in seen_enum:
                error.err_add(ctx.errors, obj_stmt.pos, 'AMM_OBJ_ENUM_UNIQUE',
                              (obj_kywd[1], enum_stmt.arg))
            seen_enum.add(enum_val)
