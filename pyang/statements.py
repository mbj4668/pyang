import copy
import re

from . import util
from .util import attrsearch, keysearch, prefix_to_module, \
    prefix_to_modulename_and_revision
from .error import err_add
from . import types
from . import syntax
from . import grammar
from . import xpath

### Functions that plugins can use

def add_validation_phase(phase, before=None, after=None):
    """Add a validation phase to the framework.

    Can be used by plugins to do special validation of extensions."""
    idx = 0
    for x in _validation_phases:
        if x == before:
            _validation_phases.insert(idx, phase)
            return
        elif x == after:
            _validation_phases.insert(idx+1, phase)
            return
        idx = idx + 1
    # otherwise append at the end
    _validation_phases.append(phase)

def add_validation_fun(phase, keywords, f):
    """Add a validation function to some phase in the framework.

    Function `f` is called for each valid occurance of each keyword in
    `keywords`.
    Can be used by plugins to do special validation of extensions."""
    for keyword in keywords:
        if (phase, keyword) in _validation_map:
            oldf = _validation_map[(phase, keyword)]
            def newf(ctx, s):
                oldf(ctx, s)
                f(ctx, s)
            _validation_map[(phase, keyword)] = newf
        else:
            _validation_map[(phase, keyword)] = f

def add_validation_var(var_name, var_fun):
    """Add a validation variable to the framework.

    Can be used by plugins to do special validation of extensions."""
    _validation_variables.append((var_name, var_fun))

def set_phase_i_children(phase):
    """Marks that the phase is run over the expanded i_children.

    Default is to run over substmts."""
    _v_i_children[phase] = True

def add_keyword_phase_i_children(phase, keyword):
    """Marks that the stmt is run in the expanded i_children phase."""
    _v_i_children_keywords[(phase, keyword)] = True

def add_data_keyword(keyword):
    """Can be used by plugins to register extensions as data keywords."""
    _data_keywords.append(keyword)

def add_keyword_with_children(keyword):
    _keyword_with_children[keyword] = True

def is_keyword_with_children(keyword):
    return keyword in _keyword_with_children

def add_keywords_with_no_explicit_config(keyword):
    _keywords_with_no_explicit_config.append(keyword)

def add_copy_uses_keyword(keyword):
    _copy_uses_keywords.append(keyword)

def add_copy_augment_keyword(keyword):
    _copy_augment_keywords.append(keyword)

def add_xpath_function(name):
    extra_xpath_functions.append(name)

def add_refinement_element(keyword, element, merge = False, v_fun=None):
    """Add an element to the <keyword>'s list of refinements"""
    for (key, valid_keywords, m, v_fun) in _refinements:
        if key == keyword:
            valid_keywords.append(element)
            return
    _refinements.append((keyword, [element], merge, v_fun))

def add_deviation_element(keyword, element):
  """Add an element to the <keyword>'s list of deviations.

  Can be used by plugins that add support for specific extension
  statements."""
  if keyword in _valid_deviations:
      _valid_deviations[keyword].append(element)
  else:
      _valid_deviations[keyword] = [element]

### Exceptions

class NotFound(Exception):
    """used when a referenced item is not found"""
    pass

class Abort(Exception):
    """used to abort an iteration"""
    pass

### Constants

re_path = re.compile('(.*)/(.*)')
re_deref = re.compile('deref\s*\(\s*(.*)\s*\)/\.\./(.*)')

yang_xpath_functions = [
    'current',
    ]

yang_1_1_xpath_functions = [
    'bit-is-set',
    'enum-value',
    'deref',
    'derived-from',
    'derived-from-or-self',
    're-match',
    ]

extra_xpath_functions = [
    'deref', # pyang extension for 1.0
    ]

data_definition_keywords = ['container', 'leaf', 'leaf-list', 'list',
                            'choice', 'anyxml', 'anydata', 'uses', 'augment']

_validation_phases = [
    # init phase:
    #   initalizes the module/submodule statement, and maps
    #   the prefix in all extensions to their modulename
    #   from this point, extensions will be validated just as the
    #   other statements
    'init',
    # second init phase initializes statements, including extensions
    'init2',

    # grammar phase:
    #   verifies that the statement hierarchy is correct
    #   and that all arguments are of correct type
    #   complex arguments are parsed and saved in statement-specific
    #   variables
    'grammar',

    # import and include phase:
    #   tries to load each imported and included (sub)module
    'import',

    # type and grouping phase:
    #   verifies all typedefs, types and groupings
    'type',
    'type_2',

    'prune',

    # expansion phases:
    #   first expansion: copy data definition stmts into i_children
    'expand_1',

    # inherit properties phase:
    #   set i_config
    'inherit_properties',

    #   second expansion: expand augmentations into i_children
    'expand_2',

    # unique name check phase:
    'unique_name',

    # reference phase:
    #   verifies all references; e.g. leafref, unique, key for config
    'reference_1',
    'reference_2',
    'reference_3',
    'reference_4',

    # unused definitions phase:
    #   add warnings for unused definitions
    'unused',

    # strict phase: check YANG strictness
    'strict',
    ]

_validation_map = {
    ('init', 'module'):lambda ctx, s: v_init_module(ctx, s),
    ('init', 'submodule'):lambda ctx, s: v_init_module(ctx, s),
    ('init', '$extension'):lambda ctx, s: v_init_extension(ctx, s),
    ('init2', 'import'):lambda ctx, s: v_init_import(ctx, s),
    ('init2', '$has_children'):lambda ctx, s: v_init_has_children(ctx, s),
    ('init2', '*'):lambda ctx, s: v_init_stmt(ctx, s),

    ('grammar', 'module'):lambda ctx, s: v_grammar_module(ctx, s),
    ('grammar', 'submodule'):lambda ctx, s: v_grammar_module(ctx, s),
    ('grammar', 'typedef'):lambda ctx, s: v_grammar_typedef(ctx, s),
    ('grammar', '*'):lambda ctx, s: v_grammar_unique_defs(ctx, s),

    ('import', 'module'):lambda ctx, s: v_import_module(ctx, s),
    ('import', 'submodule'):lambda ctx, s: v_import_module(ctx, s),

    ('type', 'grouping'):lambda ctx, s: v_type_grouping(ctx, s),
    ('type', 'augment'):lambda ctx, s: v_type_augment(ctx, s),
    ('type', 'uses'):lambda ctx, s: v_type_uses(ctx, s),
    ('type', 'feature'):lambda ctx, s: v_type_feature(ctx, s),
    ('type', 'if-feature'):lambda ctx, s: v_type_if_feature(ctx, s),
    ('type', 'identity'):lambda ctx, s: v_type_identity(ctx, s),
    ('type', 'base'):lambda ctx, s: v_type_base(ctx, s),
    ('type', '$extension'): lambda ctx, s: v_type_extension(ctx, s),

    ('type_2', 'type'):lambda ctx, s: v_type_type(ctx, s),
    ('type_2', 'typedef'):lambda ctx, s: v_type_typedef(ctx, s),
    ('type_2', 'leaf'):lambda ctx, s: v_type_leaf(ctx, s),
    ('type_2', 'leaf-list'):lambda ctx, s: v_type_leaf_list(ctx, s),

    ('prune', 'module'):lambda ctx, s: v_prune_module(ctx, s),
    ('prune', 'submodule'):lambda ctx, s: v_prune_module(ctx, s),

    ('expand_1', 'module'):lambda ctx, s: v_expand_1_children(ctx, s),
    ('expand_1', 'submodule'):lambda ctx, s: v_expand_1_children(ctx, s),

    ('inherit_properties', 'module'): \
        lambda ctx, s: v_inherit_properties(ctx, s),
    ('inherit_properties', 'submodule'): \
        lambda ctx, s: v_inherit_properties(ctx, s),

    ('expand_2', 'augment'):lambda ctx, s: v_expand_2_augment(ctx, s),

    ('unique_name', 'module'): \
        lambda ctx, s: v_unique_name_defintions(ctx, s),
    ('unique_name', '$has_children'): \
        lambda ctx, s: v_unique_name_children(ctx, s),
    ('unique_name', 'leaf-list'): \
        lambda ctx, s: v_unique_name_leaf_list(ctx, s),

    ('reference_1', 'list'):lambda ctx, s:v_reference_list(ctx, s),
    ('reference_1', 'choice'):lambda ctx, s: v_reference_choice(ctx, s),
    ('reference_2', 'leaf'):lambda ctx, s:v_reference_leaf_leafref(ctx, s),
    ('reference_2', 'leaf-list'):lambda ctx, s:v_reference_leaf_leafref(ctx, s),
    ('reference_3', 'typedef'):lambda ctx, s:v_reference_leaf_leafref(ctx, s),
    ('reference_3', 'must'):lambda ctx, s:v_reference_must(ctx, s),
    ('reference_3', 'when'):lambda ctx, s:v_reference_when(ctx, s),
    ('reference_3', 'deviation'):lambda ctx, s:v_reference_deviation(ctx, s),
    ('reference_3', 'deviate'):lambda ctx, s:v_reference_deviate(ctx, s),
    ('reference_4', 'deviation'):lambda ctx, s:v_reference_deviation_4(ctx, s),

    ('unused', 'module'):lambda ctx, s: v_unused_module(ctx, s),
    ('unused', 'submodule'):lambda ctx, s: v_unused_module(ctx, s),
    ('unused', 'typedef'):lambda ctx, s: v_unused_typedef(ctx, s),
    ('unused', 'grouping'):lambda ctx, s: v_unused_grouping(ctx, s),

    ('strict', 'path'):lambda ctx, s: v_strict_xpath(ctx, s),
    ('strict', 'must'):lambda ctx, s: v_strict_xpath(ctx, s),
    ('strict', 'when'):lambda ctx, s: v_strict_xpath(ctx, s),

    }

_v_i_children = {
    'unique_name':True,
    'expand_2':True,
    'reference_1':True,
    'reference_2':True,
}
"""Phases in this dict are run over the stmts which has i_children.
Note that the tests are not run in grouping definitions."""

_v_i_children_keywords = {
}
"""Keywords in this dict are iterated over in a phase in _v_i_children."""

_keyword_with_children = {
    'module':True,
    'submodule':True,
    'container':True,
    'list':True,
    'case':True,
    'choice':True,
    'grouping':True,
    'uses':True,
    'augment':True,
    'input':True,
    'output':True,
    'notification':True,
    'rpc':True,
    'action':True,
    }

_validation_variables = [
    ('$has_children', lambda keyword: keyword in _keyword_with_children),
    ('$extension', lambda keyword: util.is_prefixed(keyword)),
    ]

_data_keywords = ['leaf', 'leaf-list', 'container', 'list', 'choice', 'case',
                  'anyxml', 'anydata', 'action', 'rpc', 'notification']

_keywords_with_no_explicit_config = ['action', 'rpc', 'notification']

_copy_uses_keywords = []

_copy_augment_keywords = []

_refinements = [
    # (<keyword>, <list of keywords for which <keyword> can be refined>,
    #  <merge>, <validation function>)
    ('description',
     ['container', 'leaf', 'leaf-list', 'list', 'choice', 'case',
      'anyxml', 'anydata'],
     False, None),
    ('reference',
     ['container', 'leaf', 'leaf-list', 'list', 'choice', 'case',
      'anyxml', 'anydata'],
     False, None),
    ('config',
     ['container', 'leaf', 'leaf-list', 'list', 'choice', 'anyxml', 'anydata'],
     False, None),
    ('presence', ['container'], False, None),
    ('must', ['container', 'leaf', 'leaf-list', 'list', 'anyxml', 'anydata'],
     True, None),
    ('default', ['leaf', 'choice'],
     False, lambda ctx, target, default: v_default(ctx, target, default)),
    ('mandatory', ['leaf', 'choice', 'anyxml', 'anydata'], False, None),
    ('min-elements', ['leaf-list', 'list'], False, None),
    ('max-elements', ['leaf-list', 'list'], False, None),
    ('if-feature',
     ['container', 'leaf', 'leaf-list', 'list', 'choice', 'case',
      'anyxml', 'anydata'],
     True, None),
]

_singleton_keywords = {
    'type':True,
    'units':True,
    'default':True,
    'config':True,
    'mandatory':True,
    'min-elements':True,
    'max-elements':True
    }

_valid_deviations = {
    'type':['leaf', 'leaf-list'],
    'units':['leaf', 'leaf-list'],
    'default':['leaf', 'choice'],
    'config':['leaf', 'choice', 'container', 'list', 'leaf-list'],
    'mandatory':['leaf', 'choice'],
    'min-elements':['leaf-list', 'list'],
    'max-elements':['leaf-list', 'list'],
    'must':['leaf', 'choice', 'container', 'list', 'leaf-list'],
    'unique':['list'],
}

### Validation

def validate_module(ctx, module):
    """Validate `module`, which is a Statement representing a (sub)module"""

    def iterate(stmt, phase):
        # if the grammar is not yet checked or if it is checked and
        # valid, then we continue.
        if (hasattr(stmt, 'is_grammatically_valid') and
            stmt.is_grammatically_valid == False):
            return
        # first check an exact match
        key = (phase, stmt.keyword)
        res = 'recurse'
        if key in _validation_map:
            f = _validation_map[key]
            res = f(ctx, stmt)
            if res == 'stop':
                raise Abort
        # then also run match by special variable
        for (var_name, var_f) in _validation_variables:
            key = (phase, var_name)
            if key in _validation_map and var_f(stmt.keyword) == True:
                f = _validation_map[key]
                res = f(ctx, stmt)
                if res == 'stop':
                    raise Abort
        # then run wildcard
        wildcard = (phase, '*')
        if wildcard in _validation_map:
            f = _validation_map[wildcard]
            res = f(ctx, stmt)
            if res == 'stop':
                raise Abort
        if res == 'continue':
            pass
        else:
            # default is to recurse
            if phase in _v_i_children:
                if stmt.keyword == 'grouping':
                    return
                if stmt.i_module is not None and stmt.i_module != module:
                    # this means that the stmt is from an included, expanded
                    # submodule - already validated.
                    return
                if hasattr(stmt, 'i_children'):
                    for s in stmt.i_children:
                        iterate(s, phase)
                for s in stmt.substmts:
                    if (hasattr(s, 'i_has_i_children') or
                        (phase, s.keyword) in _v_i_children_keywords):
                        iterate(s, phase)
            else:
                for s in stmt.substmts:
                    iterate(s, phase)

    module.i_is_validated = 'in_progress'
    try:
        for phase in _validation_phases:
            iterate(module, phase)
    except Abort:
        pass
    module.i_is_validated = True

def v_init_module(ctx, stmt):
    ## remember that the grammar is not validated
    vsn = stmt.search_one('yang-version')
    if vsn is not None:
        stmt.i_version = vsn.arg
    else:
        stmt.i_version = '1'
    # create a prefix map in the module:
    #   <prefix string> -> (<modulename>, <revision-date> | None)
    stmt.i_prefixes = {}
    # keep track of unused prefixes: <prefix string> -> <import statement>
    stmt.i_unused_prefixes = {}
    # keep track of missing prefixes, to supress mulitple errors
    stmt.i_missing_prefixes = {}
    # insert our own prefix into the map
    prefix = None
    if stmt.keyword == 'module':
        prefix = stmt.search_one('prefix')
        stmt.i_modulename = stmt.arg
    else:
        belongs_to = stmt.search_one('belongs-to')
        if belongs_to is not None and belongs_to.arg is not None:
            prefix = belongs_to.search_one('prefix')
            stmt.i_modulename = belongs_to.arg
        else:
            stmt.i_modulename = ""

    if prefix is not None and prefix.arg is not None:
        stmt.i_prefixes[prefix.arg] = (stmt.arg, None)
        stmt.i_prefix = prefix.arg
    else:
        stmt.i_prefix = None
    # next we try to add prefixes for each import
    for i in stmt.search('import'):
        p = i.search_one('prefix')
        # verify that the prefix is not used
        if p is not None:
            prefix = p.arg
            r = i.search_one('revision-date')
            if r is not None:
                revision = r.arg
            else:
                revision = None
            # check if the prefix is already used by someone else
            if prefix in stmt.i_prefixes:
                (m, _rev) = stmt.i_prefixes[prefix]
                err_add(ctx.errors, p.pos, 'PREFIX_ALREADY_USED', (prefix, m))
            # add the prefix to the unused prefixes
            if (i.arg is not None and p.arg is not None
                and i.arg != stmt.i_modulename):
                stmt.i_prefixes[p.arg] = (i.arg, revision)
                stmt.i_unused_prefixes[p.arg] = i

    stmt.i_features = {}
    stmt.i_identities = {}
    stmt.i_extensions = {}
    stmt.i_prune = []

    stmt.i_including_modulename = None

    # save a pointer to the context
    stmt.i_ctx = ctx
    # keep track of created augment nodes
    stmt.i_undefined_augment_nodes = {}
    # next, set the attribute 'i_module' in each statement to point to the
    # module where the statement is defined.  if the module is a submodule,
    # 'i_module' will point to the main module.
    # 'i_orig_module' will point to the real module / submodule.
    def set_i_module(s):
        s.i_orig_module = s.top
        s.i_module = s.top
        return
    iterate_stmt(stmt, set_i_module)

def v_init_extension(ctx, stmt):
    """find the modulename of the prefix, and set `stmt.keyword`"""
    (prefix, identifier) = stmt.raw_keyword
    (modname, revision) = \
        prefix_to_modulename_and_revision(stmt.i_module, prefix,
                                          stmt.pos, ctx.errors)
    stmt.keyword = (modname, identifier)
    stmt.i_extension_modulename = modname
    stmt.i_extension_revision = revision
    stmt.i_extension = None

def v_init_stmt(ctx, stmt):
    stmt.i_typedefs = {}
    stmt.i_groupings = {}
    stmt.i_uniques = []

def v_init_has_children(ctx, stmt):
    stmt.i_children = []

def v_init_import(ctx, stmt):
    stmt.i_is_safe_import = False

### grammar phase

def v_grammar_module(ctx, stmt):
    # check the statement hierarchy
    grammar.chk_module_statements(ctx, stmt, ctx.canonical)
    # check revision statements order
    prev = None
    stmt.i_latest_revision = None
    for r in stmt.search('revision'):
        if (stmt.i_latest_revision is None or
            r.arg > stmt.i_latest_revision):
            stmt.i_latest_revision = r.arg
        if prev is not None and r.arg > prev:
            err_add(ctx.errors, r.pos, 'REVISION_ORDER', ())
        prev = r.arg

def v_grammar_typedef(ctx, stmt):
    if types.is_base_type(stmt.arg):
        err_add(ctx.errors, stmt.pos, 'BAD_TYPE_NAME', stmt.arg)

def v_grammar_unique_defs(ctx, stmt):
    """Verify that all typedefs and groupings are unique
    Called for every statement.
    Stores all typedefs in stmt.i_typedef, groupings in stmt.i_grouping
    """
    defs = [('typedef', 'TYPE_ALREADY_DEFINED', stmt.i_typedefs),
            ('grouping', 'GROUPING_ALREADY_DEFINED', stmt.i_groupings)]
    if stmt.parent is None:
        defs.extend(
            [('feature', 'FEATURE_ALREADY_DEFINED', stmt.i_features),
             ('identity', 'IDENTITY_ALREADY_DEFINED', stmt.i_identities),
             ('extension', 'EXTENSION_ALREADY_DEFINED', stmt.i_extensions)])
    for (keyword, errcode, dict) in defs:
        for definition in stmt.search(keyword):
            if definition.arg in dict:
                other = dict[definition.arg]
                err_add(ctx.errors, definition.pos,
                        errcode, (definition.arg, other.pos))
            else:
                dict[definition.arg] = definition

### import and include phase

def v_import_module(ctx, stmt):
    imports = stmt.search('import')
    includes = stmt.search('include')
    if stmt.keyword == 'module':
        mymodulename = stmt.arg
    else:
        b = stmt.search_one('belongs-to')
        if b is not None:
            mymodulename = b.arg
        else:
            mymodulename = None
    def add_module(i):
        # check if the module to import is already added
        modulename = i.arg
        r = i.search_one('revision-date')
        rev = None
        if r is not None:
            rev = r.arg
        m = ctx.get_module(modulename, rev)
        if m is not None and i.keyword == 'import' and i.i_is_safe_import:
            pass
        elif m is not None and m.i_is_validated == 'in_progress':
            err_add(ctx.errors, i.pos,
                    'CIRCULAR_DEPENDENCY', ('module', modulename))
        # try to add the module to the context
        m = ctx.search_module(i.pos, modulename, rev)
        if (m is not None and r is not None and
            stmt.i_version == '1' and m.i_version == '1.1'):
            err_add(ctx.errors, i.pos,
                    'BAD_IMPORT_YANG_VERSION',
                    (stmt.i_version, m.i_version))
        return m

    for i in imports:
        module = add_module(i)
        if module is not None and module.keyword != 'module':
            err_add(ctx.errors, i.pos,
                    'BAD_IMPORT', (module.keyword, i.arg))

    for i in includes:
        submodule = add_module(i)
        if submodule is not None and submodule.keyword != 'submodule':
            err_add(ctx.errors, i.pos,
                    'BAD_INCLUDE', (submodule.keyword, i.arg))
            return
        if submodule is not None:
            if submodule.i_version != stmt.i_version:
                err_add(ctx.errors, i.pos,
                        'BAD_INCLUDE_YANG_VERSION',
                        (submodule.i_version, stmt.i_version))
                return
            if stmt.keyword == 'module':
                submodule.i_including_modulename = stmt.arg
            else:
                submodule.i_including_modulename = mymodulename
            b = submodule.search_one('belongs-to')
            if b is not None and b.arg != mymodulename:
                err_add(ctx.errors, b.pos,
                    'BAD_SUB_BELONGS_TO',
                        (stmt.arg, submodule.arg, submodule.arg))
            else:
                # check that each submodule included by this submodule
                # is also included by the module
                if stmt.keyword == 'module':
                    for s in submodule.search('include'):
                        if stmt.search_one('include', s.arg) is None:
                            err_add(ctx.errors, s.pos,
                                    'MISSING_INCLUDE',
                                    (s.arg, submodule.arg, stmt.arg))

                # add typedefs, groupings, nodes etc to this module
                for ch in submodule.i_children:
                    if ch not in stmt.i_children:
                        stmt.i_children.append(ch)
                # verify that the submodule's definitions do not collide
                # with the module's definitions
                defs = \
                    [(submodule.i_typedefs, stmt.i_typedefs,
                      'TYPE_ALREADY_DEFINED'),
                     (submodule.i_groupings, stmt.i_groupings,
                      'GROUPING_ALREADY_DEFINED'),
                     (submodule.i_features, stmt.i_features,
                      'FEATURE_ALREADY_DEFINED'),
                     (submodule.i_identities, stmt.i_identities,
                      'IDENTITY_ALREADY_DEFINED'),
                     (submodule.i_extensions, stmt.i_extensions,
                      'EXTENSION_ALREADY_DEFINED')]
                for (subdict, dict, errcode) in defs:
                    for name in subdict:
                        subdefinition = subdict[name]
                        if name in dict:
                            # when the same submodule is inlcuded twice
                            # (e.g. by the module and by another submodule)
                            # the same definition will exist multiple times.
                            other = dict[name]
                            if other != subdefinition:
                                err_add(ctx.errors, other.pos,
                                        errcode, (name, subdefinition.pos))
                        else:
                            dict[name] = subdefinition

### type phase

def v_type_typedef(ctx, stmt):
    if hasattr(stmt, 'i_is_validated'):
        if stmt.i_is_validated == True:
            # this type has already been validated
            return
        elif stmt.i_is_circular == True:
            return
        elif stmt.i_is_validated == 'in_progress':
            err_add(ctx.errors, stmt.pos,
                    'CIRCULAR_DEPENDENCY', ('type', stmt.arg) )
            stmt.i_is_circular = True
            return

    stmt.i_is_circular = False
    stmt.i_is_validated = 'in_progress'
    stmt.i_default = None
    stmt.i_default_str = ""
    stmt.i_is_unused = True

    stmt.i_leafref = None # path_type_spec
    stmt.i_leafref_ptr = None # pointer to the leaf the leafref refer to
    stmt.i_leafref_expanded = False

    name = stmt.arg
    if stmt.parent.parent is not None:
        # non-top-level typedef; check if it is already defined
        ptype = search_typedef(stmt.parent.parent, name)
        if ptype is not None:
            err_add(ctx.errors, stmt.pos, 'TYPE_ALREADY_DEFINED',
                    (name, ptype.pos))
    type_ = stmt.search_one('type')
    if type_ is None or type_.is_grammatically_valid == False:
        # error is already reported by grammar check
        return
    # ensure our type is validated
    v_type_type(ctx, type_)

    # keep track of our leafref
    type_spec = type_.i_type_spec
    if type(type_spec) == types.PathTypeSpec:
        stmt.i_leafref = type_spec

    def check_circular_typedef(ctx, type_):
        # ensure the type is validated
        v_type_type(ctx, type_)
        # check the direct typedef
        if (type_.i_typedef is not None and
            type_.i_typedef.is_grammatically_valid == True):
            v_type_typedef(ctx, type_.i_typedef)
        # check all union's types
        membertypes = type_.search('type')
        for t in membertypes:
            check_circular_typedef(ctx, t)

    check_circular_typedef(ctx, type_)

    stmt.i_is_validated = True

    # check if we have a default value
    default = stmt.search_one('default')
    # ... or if we don't; check if our base typedef has one
    if (default is None and
        type_.i_typedef is not None and
        type_.i_typedef.i_default is not None):
        # validate that the base type's default value is still valid
        stmt.i_default = type_.i_typedef.i_default
        stmt.i_default_str = type_.i_typedef.i_default_str
        type_.i_type_spec.validate(ctx.errors, stmt.pos,
                                   stmt.i_default,
                                   ' for the inherited default value ')
    elif (default is not None and
          default.arg is not None and
          type_.i_type_spec is not None):
        stmt.i_default = type_.i_type_spec.str_to_val(ctx.errors,
                                                      default.pos,
                                                      default.arg)
        stmt.i_default_str = default.arg
        if stmt.i_default is not None:
            type_.i_type_spec.validate(ctx.errors, default.pos,
                                       stmt.i_default,
                                       ' for the default value')

def v_type_type(ctx, stmt):
    if hasattr(stmt, 'i_is_validated'):
        # already validated
        return

    # set statement-specific variables
    stmt.i_is_validated = True
    stmt.i_is_derived = False
    stmt.i_type_spec = None
    stmt.i_typedef = None
    # Find the base type_spec
    name = stmt.arg
    if name.find(":") == -1:
        prefix = None
    else:
        [prefix, name] = name.split(':', 1)
    if prefix is None or stmt.i_module.i_prefix == prefix:
        # check local typedefs
        stmt.i_typedef = search_typedef(stmt, name)
        if stmt.i_typedef is None:
            # check built-in types
            try:
                stmt.i_type_spec = types.yang_type_specs[name]
            except KeyError:
                err_add(ctx.errors, stmt.pos,
                        'TYPE_NOT_FOUND', (name, stmt.i_module.arg))
                return
        else:
            # ensure the typedef is validated
            if stmt.i_typedef.is_grammatically_valid == True:
                v_type_typedef(ctx, stmt.i_typedef)
            else:
                stmt.i_typedef.i_default = None
                stmt.i_typedef.i_default_str = ""
            stmt.i_typedef.i_is_unused = False
    else:
        # this is a prefixed name, check the imported modules
        pmodule = prefix_to_module(stmt.i_module, prefix, stmt.pos, ctx.errors)
        if pmodule is None:
            return
        stmt.i_typedef = search_typedef(pmodule, name)
        if stmt.i_typedef is None:
            err_add(ctx.errors, stmt.pos, 'TYPE_NOT_FOUND', (name, pmodule.arg))
            return
        else:
            stmt.i_typedef.i_is_unused = False

    if stmt.i_typedef is not None:
        typedef_type = stmt.i_typedef.search_one('type')
        if typedef_type is not None and hasattr(typedef_type, 'i_type_spec'):
            # copy since we modify the typespec's definition
            stmt.i_type_spec = copy.copy(typedef_type.i_type_spec)
            if stmt.i_type_spec is not None:
                stmt.i_type_spec.definition = ('at ' +
                                               str(stmt.i_typedef.pos) +
                                               ' ')

    if stmt.i_type_spec is None:
        # an error has been added already; skip further validation
        return

    # check the fraction-digits - only applicable when the type is the builtin
    # decimal64
    frac = stmt.search_one('fraction-digits')
    if frac is not None and stmt.arg != 'decimal64':
        err_add(ctx.errors, frac.pos, 'BAD_RESTRICTION', 'fraction_digits')
    elif stmt.arg == 'decimal64' and frac is None:
        err_add(ctx.errors, stmt.pos, 'MISSING_TYPE_SPEC_1',
                ('decimal64', 'fraction-digits'))
    elif stmt.arg == 'decimal64' and frac.is_grammatically_valid:
        stmt.i_is_derived = True
        stmt.i_type_spec = types.Decimal64TypeSpec(frac)

    # check the range restriction
    stmt.i_ranges = []
    range = stmt.search_one('range')
    if (range is not None and
        'range' not in stmt.i_type_spec.restrictions()):
        err_add(ctx.errors, range.pos, 'BAD_RESTRICTION', 'range')
    elif range is not None:
        stmt.i_is_derived = True
        ranges_spec = types.validate_range_expr(ctx.errors, range, stmt)
        if ranges_spec is not None:
            stmt.i_ranges = ranges_spec[0]
            stmt.i_type_spec = types.RangeTypeSpec(stmt.i_type_spec,
                                                   ranges_spec)

    # check the length restriction
    stmt.i_lengths = []
    length = stmt.search_one('length')
    if (length is not None and
        'length' not in stmt.i_type_spec.restrictions()):
        err_add(ctx.errors, length.pos, 'BAD_RESTRICTION', 'length')
    elif length is not None:
        stmt.i_is_derived = True
        lengths_spec = types.validate_length_expr(ctx.errors, length)
        if lengths_spec is not None:
            stmt.i_lengths = lengths_spec[0]
            stmt.i_type_spec = types.LengthTypeSpec(stmt.i_type_spec,
                                                    lengths_spec)

    # check the pattern restrictions
    patterns = stmt.search('pattern')
    if (patterns != [] and
        'pattern' not in stmt.i_type_spec.restrictions()):
        err_add(ctx.errors, patterns[0].pos, 'BAD_RESTRICTION', 'pattern')
    elif patterns != []:
        stmt.i_is_derived = True
        pattern_specs = [types.validate_pattern_expr(ctx.errors, p)
                         for p in patterns]
        if None not in pattern_specs:
            # all patterns valid
            stmt.i_type_spec = types.PatternTypeSpec(stmt.i_type_spec,
                                                     pattern_specs)

    # check the path restriction
    path = stmt.search_one('path')
    if path is not None and stmt.arg != 'leafref':
        err_add(ctx.errors, path.pos, 'BAD_RESTRICTION', 'path')
    elif stmt.arg == 'leafref' and path is None:
        err_add(ctx.errors, stmt.pos, 'MISSING_TYPE_SPEC_1',
                ('leafref', 'path'))
    elif path is not None:
        stmt.i_is_derived = True
        if path.is_grammatically_valid == True:
            path_spec = types.validate_path_expr(ctx.errors, path)
            if path_spec is not None:
                stmt.i_type_spec = types.PathTypeSpec(stmt.i_type_spec,
                                                      path_spec, path, path.pos)
                stmt.i_type_spec.i_source_stmt = stmt

    # check the base restriction
    bases = stmt.search('base')
    if bases != [] and stmt.arg != 'identityref':
        err_add(ctx.errors, bases[0].pos, 'BAD_RESTRICTION', 'base')
    elif len(bases) > 1 and stmt.i_module.i_version == '1':
        err_add(ctx.errors, bases[1].pos, 'UNEXPECTED_KEYWORD', 'base')
    elif stmt.arg == 'identityref' and bases == []:
        err_add(ctx.errors, stmt.pos, 'MISSING_TYPE_SPEC',
                ('identityref', 'base'))
    else:
        idbases = []
        for base in bases:
            v_type_base(ctx, base)
            if base.i_identity is not None:
               idbases.append(base)
        if len(idbases) > 0:
            stmt.i_is_derived = True
            stmt.i_type_spec = types.IdentityrefTypeSpec(idbases)

    # check the require-instance restriction
    req_inst = stmt.search_one('require-instance')
    if (req_inst is not None and
        'require-instance' not in stmt.i_type_spec.restrictions()):
        err_add(ctx.errors, req_inst.pos, 'BAD_RESTRICTION', 'require-instance')
    if (req_inst is not None and stmt.i_type_spec.name == 'leafref' and
        stmt.i_module.i_version == '1'):
        err_add(ctx.errors, req_inst.pos, 'BAD_RESTRICTION', 'require-instance')
    if (req_inst is not None):
        stmt.i_type_spec.require_instance = req_inst.arg == 'true'

    # check the enums - only applicable when the type is the builtin
    # enumeration type in YANG version 1, and for derived enumerations in 1.1
    enums = stmt.search('enum')
    if (enums != [] and
        ('enum' not in stmt.i_type_spec.restrictions() or
         stmt.i_module.i_version == '1' and stmt.arg != 'enumeration')):
        err_add(ctx.errors, enums[0].pos, 'BAD_RESTRICTION', 'enum')
    elif stmt.arg == 'enumeration' and enums == []:
        err_add(ctx.errors, stmt.pos, 'MISSING_TYPE_SPEC',
                ('enumeration', 'enum'))
    elif enums != []:
        stmt.i_is_derived = True

        enum_spec = types.validate_enums(ctx.errors, enums, stmt)
        if enum_spec is not None:
            stmt.i_type_spec = types.EnumTypeSpec(stmt.i_type_spec,
                                                  enum_spec)

    # check the bits - only applicable when the type is the builtin
    # bits type in YANG version 1, and for derived bits in 1.1
    bits = stmt.search('bit')
    if (bits != [] and
        ('bit' not in stmt.i_type_spec.restrictions() or
         stmt.i_module.i_version == '1' and stmt.arg != 'bits')):
        err_add(ctx.errors, bits[0].pos, 'BAD_RESTRICTION', 'bit')
    elif stmt.arg == 'bits' and bits == []:
        err_add(ctx.errors, stmt.pos, 'MISSING_TYPE_SPEC',
                ('bits', 'bit'))
    elif bits != []:
        stmt.i_is_derived = True
        bit_spec = types.validate_bits(ctx.errors, bits, stmt)
        if bit_spec is not None:
            stmt.i_type_spec = types.BitTypeSpec(stmt.i_type_spec,
                                                 bit_spec)

    # check the union types
    membertypes = stmt.search('type')
    if membertypes != [] and stmt.arg != 'union':
        err_add(ctx.errors, membertypes[0].pos, 'BAD_RESTRICTION', 'union')
    elif membertypes == [] and stmt.arg == 'union':
        err_add(ctx.errors, stmt.pos, 'MISSING_TYPE_SPEC',
                ('union', 'type'))
    elif membertypes != []:
        stmt.i_is_derived = True
        for t in membertypes:
            if t.is_grammatically_valid == True:
                v_type_type(ctx, t)
        stmt.i_type_spec = types.UnionTypeSpec(membertypes)
        if stmt.i_module.i_version == '1':
            t = has_type(stmt, ['empty', 'leafref'])
            if t is not None:
                err_add(ctx.errors, stmt.pos, 'BAD_TYPE_IN_UNION',
                        (t.arg, t.pos))
                return False

def v_type_leaf(ctx, stmt):
    stmt.i_default = None
    stmt.i_default_str = ""
    if _v_type_common_leaf(ctx, stmt) == False:
        return
    # check if we have a default value
    default = stmt.search_one('default')
    type_ = stmt.search_one('type')
    if default is not None and type_.i_type_spec is not None :
        defval = type_.i_type_spec.str_to_val(ctx.errors,
                                              default.pos,
                                              default.arg)
        stmt.i_default = defval
        stmt.i_default_str = default.arg
        if defval is not None:
            type_.i_type_spec.validate(ctx.errors, default.pos,
                                       defval, ' for the default value')
    elif (default is None and
          type_.i_typedef is not None and
          hasattr(type_.i_typedef, 'i_default') and
          type_.i_typedef.i_default is not None):
        stmt.i_default = type_.i_typedef.i_default
        stmt.i_default_str = type_.i_typedef.i_default_str
        # validate the type's default value with our new restrictions
        if type_.i_type_spec is not None:
            type_.i_type_spec.validate(ctx.errors, stmt.pos,
                                       stmt.i_default,
                                       ' for the default  value')

    if default is not None:
        m = stmt.search_one('mandatory')
        if m is not None and m.arg == 'true':
            err_add(ctx.errors, stmt.pos, 'DEFAULT_AND_MANDATORY', ())
            return False

def v_type_leaf_list(ctx, stmt):
    stmt.i_default = []
    if _v_type_common_leaf(ctx, stmt) == False:
        return
    # check if we have default values
    type_ = stmt.search_one('type')
    for default in stmt.search('default'):
        if type_.i_type_spec is not None :
            defval = type_.i_type_spec.str_to_val(ctx.errors,
                                                  default.pos,
                                                  default.arg)
            if defval is not None:
                stmt.i_default.append(defval)
                type_.i_type_spec.validate(ctx.errors, default.pos,
                                           defval, ' for the default value')

    if stmt.i_default != []:
        m = stmt.search_one('min-elements')
        if m is not None and int(m.arg) > 0:
            d = stmt.search_one('default')
            err_add(ctx.errors, d.pos, 'DEFAULT_AND_MIN_ELEMENTS', ())
            return False

    if (stmt.i_default == [] and
          type_.i_typedef is not None and
          hasattr(type_.i_typedef, 'i_default') and
          type_.i_typedef.i_default is not None):
        stmt.i_default.append(type_.i_typedef.i_default)
        # validate the type's default value with our new restrictions
        if type_.i_type_spec is not None:
            type_.i_type_spec.validate(ctx.errors, stmt.pos,
                                       type_.i_typedef.i_default,
                                       ' for the default  value')

def _v_type_common_leaf(ctx, stmt):
    stmt.i_leafref = None # path_type_spec
    stmt.i_leafref_ptr = None # pointer to the leaf the leafref refer to
    stmt.i_leafref_expanded = False
    # check our type
    type_ = stmt.search_one('type')
    if type_ is None or type_.is_grammatically_valid == False:
        # error is already reported by grammar check
        return False

    # ensure our type is validated
    v_type_type(ctx, type_)

    # keep track of our leafref
    type_spec = type_.i_type_spec
    if type(type_spec) == types.PathTypeSpec:
        stmt.i_leafref = type_spec

def v_type_grouping(ctx, stmt):
    if hasattr(stmt, 'i_is_validated'):
        if stmt.i_is_validated == True:
            # this grouping has already been validated
            return True
        elif stmt.i_is_validated == 'in_progress':
            err_add(ctx.errors, stmt.pos,
                    'CIRCULAR_DEPENDENCY', ('grouping', stmt.arg) )
            return False

    stmt.i_is_validated = 'in_progress'
    stmt.i_is_unused = True
    stmt.i_has_i_children = True

    name = stmt.arg
    if stmt.parent.parent is not None:
        # non-top-level grouping; check if it is already defined
        pgrouping = search_grouping(stmt.parent.parent, name)
        if pgrouping is not None:
            err_add(ctx.errors, stmt.pos, 'GROUPING_ALREADY_DEFINED',
                    (name, pgrouping.pos))

    # search for circular grouping definitions
    def validate_uses(s):
        if (s.keyword == "uses" and
            hasattr(s, 'is_grammatically_valid') and
            s.is_grammatically_valid == True):
            v_type_uses(ctx, s, no_error_report=True)

    iterate_stmt(stmt, validate_uses)

    stmt.i_is_validated = True
    return True

def v_type_uses(ctx, stmt, no_error_report=False):
    # Find the grouping
    name = stmt.arg
    if name.find(":") == -1:
        prefix = None
    else:
        [prefix, name] = name.split(':', 1)
    if hasattr(stmt, 'i_grouping'):
        if stmt.i_grouping is None and no_error_report == False:
            if prefix is None or stmt.i_module.i_prefix == prefix:
                # check local groupings
                pmodule = stmt.i_module
            else:
                pmodule = prefix_to_module(stmt.i_module, prefix,
                                           stmt.pos, ctx.errors)
                if pmodule is None:
                    return
            err_add(ctx.errors, stmt.pos,
                    'GROUPING_NOT_FOUND', (name, pmodule.arg))
        return

    stmt.i_grouping = None
    if prefix is None or stmt.i_module.i_prefix == prefix:
        # check local groupings
        pmodule = stmt.i_module
        i_grouping = search_grouping(stmt, name)
        if i_grouping is not None and i_grouping.is_grammatically_valid == True:
            if v_type_grouping(ctx, i_grouping) == True:
                stmt.i_grouping = i_grouping

    else:
        # this is a prefixed name, check the imported modules
        pmodule = prefix_to_module(stmt.i_module, prefix, stmt.pos, ctx.errors)
        if pmodule is None:
            return
        stmt.i_grouping = search_grouping(pmodule, name)
    if stmt.i_grouping is None and no_error_report == False:
        err_add(ctx.errors, stmt.pos,
                'GROUPING_NOT_FOUND', (name, pmodule.arg))
    if stmt.i_grouping is not None:
        stmt.i_grouping.i_is_unused = False

def v_type_augment(ctx, stmt):
    # make sure the _v_i_children phases run over this one
    stmt.i_has_i_children = True
    if stmt.parent.keyword == 'uses' and stmt.arg.startswith("/"):
        stmt.i_target_node = None
        err_add(ctx.errors, stmt.pos, 'BAD_VALUE',
                (stmt.arg, "descendant-node-id"))
    elif stmt.parent.keyword != 'uses' and not stmt.arg.startswith("/"):
        stmt.i_target_node = None
        err_add(ctx.errors, stmt.pos, 'BAD_VALUE',
                (stmt.arg, "absolute-node-id"))

def v_type_extension(ctx, stmt):
    """verify that the extension matches the extension definition"""
    (modulename, identifier) = stmt.keyword
    revision = stmt.i_extension_revision
    module = modulename_to_module(stmt.i_module, modulename, revision)
    if module is None:
        return
    if identifier not in module.i_extensions:
        if module.i_modulename == stmt.i_orig_module.i_modulename:
            # extension defined in current submodule
            if identifier not in stmt.i_orig_module.i_extensions:
                err_add(ctx.errors, stmt.pos, 'EXTENSION_NOT_DEFINED',
                        (identifier, module.arg))
                return
            else:
                stmt.i_extension = stmt.i_orig_module.i_extensions[identifier]
        else:
            err_add(ctx.errors, stmt.pos, 'EXTENSION_NOT_DEFINED',
                    (identifier, module.arg))
            return
    else:
        stmt.i_extension = module.i_extensions[identifier]
    ext_arg = stmt.i_extension.search_one('argument')
    if stmt.arg is not None and ext_arg is None:
        err_add(ctx.errors, stmt.pos, 'EXTENSION_ARGUMENT_PRESENT',
                identifier)
    elif stmt.arg is None and ext_arg is not None:
        err_add(ctx.errors, stmt.pos, 'EXTENSION_NO_ARGUMENT_PRESENT',
                identifier)

def v_type_feature(ctx, stmt):
    if hasattr(stmt, 'i_is_validated'):
        if stmt.i_is_validated == True:
            # this feature has already been validated
            return
        elif stmt.i_is_validated == 'in_progress':
            err_add(ctx.errors, stmt.pos,
                    'CIRCULAR_DEPENDENCY', ('feature', stmt.arg) )
            return

    stmt.i_is_validated = 'in_progress'

    name = stmt.arg

    # search for circular feature definitions
    def validate_if_feature(s):
        if s.keyword == "if-feature":
            v_type_if_feature(ctx, s, no_error_report=True)
    iterate_stmt(stmt, validate_if_feature)

    stmt.i_is_validated = True

def v_type_if_feature(ctx, stmt, no_error_report=False):
    """verify that the referenced feature exists."""
    stmt.i_feature = None
    # Verify the argument type
    expr = syntax.parse_if_feature_expr(stmt.arg)
    if stmt.i_module.i_version == '1':
        # version 1 allows only a single value as if-feature
        if type(expr) != type(''):
            err_add(ctx.errors, stmt.pos,
                    'BAD_VALUE', (stmt.arg, 'identifier-ref'))
            return

    def eval(expr):
        if type(expr) == type(''):
            return has_feature(expr)
        else:
            (op, op1, op2) = expr
            if op == 'not':
                return not eval(op1)
            elif op == 'and':
                return eval(op1) and eval(op2)
            elif op == 'or':
                return eval(op1) or eval(op2)

    def has_feature(name):
        # raises Abort if the feature is not defined
        # returns True if we compile with the feature
        # returns False if we compile without the feature
        found = None
        if name.find(":") == -1:
            prefix = None
        else:
            [prefix, name] = name.split(':', 1)
        if prefix is None or stmt.i_module.i_prefix == prefix:
            # check local features
            pmodule = stmt.i_module
        else:
            # this is a prefixed name, check the imported modules
            pmodule = prefix_to_module(stmt.i_module, prefix,
                                       stmt.pos, ctx.errors)
            if pmodule is None:
                raise Abort
        if name in pmodule.i_features:
            f = pmodule.i_features[name]
            if prefix is None and not is_submodule_included(stmt, f):
                pass
            else:
                found = pmodule.i_features[name]
                v_type_feature(ctx, found)
                if pmodule.i_modulename in ctx.features:
                    if name not in ctx.features[pmodule.i_modulename]:
                        return False

        if found is None and no_error_report == False:
            err_add(ctx.errors, stmt.pos,
                    'FEATURE_NOT_FOUND', (name, pmodule.arg))
            raise Abort
        return found is not None

    # Evaluate the if-feature expression, and verify that all
    # referenced features exist.
    try:
        if eval(expr) == False:
            # prune the parent.
            # since the parent can have more than one if-feature
            # statement, we must check if the parent
            # already has been scheduled for removal
            if stmt.parent not in stmt.i_module.i_prune:
                stmt.i_module.i_prune.append(stmt.parent)
    except Abort:
        pass

def v_type_identity(ctx, stmt):
    if hasattr(stmt, 'i_is_validated'):
        if stmt.i_is_validated == True:
            # this identity has already been validated
            return
        elif stmt.i_is_validated == 'in_progress':
            err_add(ctx.errors, stmt.pos,
                    'CIRCULAR_DEPENDENCY', ('identity', stmt.arg) )
            return

    stmt.i_is_validated = 'in_progress'

    name = stmt.arg

    if stmt.i_module.i_version == '1':
        bases = stmt.search('base')
        if len(bases) > 1:
            err_add(ctx.errors, bases[1].pos, 'UNEXPECTED_KEYWORD', 'base')
    # search for circular identity definitions
    def validate_base(s):
        if s.keyword == "base":
            v_type_base(ctx, s, no_error_report=True)
    iterate_stmt(stmt, validate_base)

    stmt.i_is_validated = True

def v_type_base(ctx, stmt, no_error_report=False):
    """verify that the referenced identity exists."""
    # Find the identity
    name = stmt.arg
    stmt.i_identity = None
    if name.find(":") == -1:
        prefix = None
    else:
        [prefix, name] = name.split(':', 1)
    if prefix is None or stmt.i_module.i_prefix == prefix:
        # check local identities
        pmodule = stmt.i_module
    else:
        # this is a prefixed name, check the imported modules
        pmodule = prefix_to_module(stmt.i_module, prefix, stmt.pos, ctx.errors)
        if pmodule is None:
            return
    if name in pmodule.i_identities:
        i = pmodule.i_identities[name]
        if prefix is None and not is_submodule_included(stmt, i):
            pass
        else:
            stmt.i_identity = i
            v_type_identity(ctx, stmt.i_identity)
    if stmt.i_identity is None and no_error_report == False:
        err_add(ctx.errors, stmt.pos,
                'IDENTITY_NOT_FOUND', (name, pmodule.arg))

### Prune phase

def v_prune_module(ctx, stmt):
    for s in stmt.i_prune:
        idx = s.parent.substmts.index(s)
        del s.parent.substmts[idx]

### Expand phases

def v_expand_1_children(ctx, stmt):
    if (hasattr(stmt, 'is_grammatically_valid') and
        stmt.is_grammatically_valid == False):
        return
    if stmt.keyword == 'grouping' and hasattr(stmt, "i_expanded"):
        # already expanded
        return
    elif stmt.keyword == 'choice':
        shorthands = ['leaf', 'leaf-list', 'container', 'list', 'choice',
                      'anyxml', 'anydata']
        for s in stmt.substmts:
            if s.keyword in shorthands:
                # create an artifical case node for the shorthand
                create_new_case(ctx, stmt, s)
            elif s.keyword == 'case':
                stmt.i_children.append(s)
                v_expand_1_children(ctx, s)
        return
    elif stmt.keyword in ('action', 'rpc'):
        input_ = stmt.search_one('input')
        if input_ is None:
            # create the implicitly defined input node
            input_ = Statement(stmt.top, stmt, stmt.pos, 'input', 'input')
            v_init_stmt(ctx, input_)
            input_.i_children = []
            input_.i_module = stmt.i_module
            stmt.i_children.append(input_)
        else:
            # check that there is at least one data definition statement
            found = False
            for c in input_.substmts:
                if c.keyword in data_definition_keywords:
                    found = True
            if not found:
                err_add(ctx.errors, input_.pos,'EXPECTED_DATA_DEF', 'input')

        output = stmt.search_one('output')
        if output is None:
            # create the implicitly defined output node
            output = Statement(stmt.top, stmt, stmt.pos, 'output', 'output')
            v_init_stmt(ctx, output)
            output.i_children = []
            output.i_module = stmt.i_module
            stmt.i_children.append(output)
        else:
            # check that there is at least one data definition statement
            found = False
            for c in output.substmts:
                if c.keyword in data_definition_keywords:
                    found = True
            if not found:
                err_add(ctx.errors, output.pos,'EXPECTED_DATA_DEF', 'output')

    if stmt.keyword == 'grouping':
        stmt.i_expanded = False
    for s in stmt.substmts:
        if s.keyword in ['input', 'output']:
            # must create a copy of the statement which sets the argument,
            # since we need to keep the original stmt hierarchy valid
            news = s.copy(nocopy=['type','typedef','grouping'])
            news.i_groupings = s.i_groupings
            news.i_typedefs = s.i_typedefs
            news.arg = news.keyword
            stmt.i_children.append(news)
            v_expand_1_children(ctx, news)
        elif (s.keyword == 'uses' and hasattr(s, 'is_grammatically_valid') and
              s.is_grammatically_valid):
            v_expand_1_uses(ctx, s)
            for a in s.search('augment'):
                v_expand_1_children(ctx, a)
            v_inherit_properties(ctx, stmt)
            for a in s.search('augment'):
                v_expand_2_augment(ctx, a)

        elif s.keyword in _data_keywords and hasattr(stmt, 'i_children'):
            stmt.i_children.append(s)
            v_expand_1_children(ctx, s)
        elif s.keyword in _keyword_with_children:
            v_expand_1_children(ctx, s)

    if stmt.keyword == 'grouping':
        stmt.i_expanded = True

    # do not recurse - recursion already done above
    return 'continue'

def v_default(ctx, target, default):
    type_ = target.search_one('type')
    if (type_ is not None and
        hasattr(type_, 'i_type_spec') and
        type_.i_type_spec is not None):
        defval = type_.i_type_spec.str_to_val(ctx.errors,
                                              default.pos,
                                              default.arg)
        target.i_default = defval
        target.i_default_str = default.arg
        if defval is not None:
            type_.i_type_spec.validate(ctx.errors, default.pos,
                                       defval, ' for the default value')

def v_expand_1_uses(ctx, stmt):
    if (hasattr(stmt, 'is_grammatically_valid') and
        stmt.is_grammatically_valid == False):
        return

    if stmt.i_grouping is None:
        return

    # possibly expand any uses within the grouping
    v_expand_1_children(ctx, stmt.i_grouping)

    def find_refine_node(refinement):
        # parse the path into a list of two-tuples of (prefix,identifier)
        pstr = '/' + refinement.arg
        path = [(m[1], m[2]) \
                    for m in syntax.re_schema_node_id_part.findall(pstr)]
        node = stmt.parent
        # recurse down the path
        for (prefix, identifier) in path:
            module = prefix_to_module(stmt.i_module, prefix, refinement.pos,
                                      ctx.errors)
            if hasattr(node, 'i_children'):
                if module is None:
                    return None
                child = search_child(node.i_children, module.i_modulename,
                                     identifier)
                if child is None:
                    err_add(ctx.errors, refinement.pos, 'NODE_NOT_FOUND',
                            (module.i_modulename, identifier))
                    return None
                node = child
            else:
                err_add(ctx.errors, refinement.pos, 'BAD_NODE_IN_REFINE',
                        (module.i_modulename, identifier))
                return None
        return node

    def replace_from_refinement(target, refinement, keyword, valid_keywords,
                                v_fun=None):
        """allow `keyword` as a refinement in `valid_keywords`"""
        new = refinement.search_one(keyword)
        if new is not None and target.keyword in valid_keywords:
            old = target.search_one(keyword)
            if old is not None:
                target.substmts.remove(old)
            if v_fun is not None:
                v_fun(ctx, target, new)
            target.substmts.append(new)
        elif new is not None:
            err_add(ctx.errors, refinement.pos, 'BAD_REFINEMENT',
                    (target.keyword, target.i_module.i_modulename,
                     target.arg, keyword))
            return

    def merge_from_refinement(target, refinement, keyword, valid_keywords,
                              v_fun=None):
        """allow `keyword` as a refinement in `valid_keywords`"""
        for new in refinement.search(keyword):
            if target.keyword in valid_keywords:
                if v_fun is not None:
                    v_fun(ctx, target, new)
                target.substmts.append(new)
            else:
                err_add(ctx.errors, refinement.pos, 'BAD_REFINEMENT',
                        (target.keyword, target.i_module.i_modulename,
                         target.arg, keyword))
                return

    # first, copy the grouping into our i_children
    for g in stmt.i_grouping.i_children:
        # don't copy the type since it cannot be modified anyway.
        # not copying the type also works better for some plugins that
        # generate output from the i_children list, e.g. the XSD plugin.
        def post_copy(old, new):
            # inline the definition into our module
            new.i_module = stmt.i_module
            new.i_children = []
            new.i_uniques = []
            new.pos.uses_pos = stmt.pos
            # build the i_children list of pointers
            if hasattr(old, 'i_children'):
                for x in old.i_children:
                    # check if this i_child is a pointer to a substmt
                    if x in old.substmts:
                        # if so, create an equivalent pointer
                        idx = old.substmts.index(x)
                        new.i_children.append(new.substmts[idx])
                    else:
                        # otherwise, copy the i_child
                        newx = x.copy(new, stmt,
                                      nocopy=['type','uses', 'unique',
                                              'typedef','grouping'],
                                      copyf=post_copy)
                        new.i_children.append(newx)
        newg = g.copy(stmt.parent, stmt,
                      nocopy=['type','uses','unique','typedef','grouping'],
                      copyf=post_copy)
        stmt.parent.i_children.append(newg)

    # copy plain statements from the grouping
    for s in stmt.i_grouping.substmts:
        if s.keyword in _copy_uses_keywords:
            news = s.copy()
            news.parent = stmt.parent
            stmt.parent.substmts.append(news)

    # keep track of already refined nodes
    refined = {}
    # then apply all refinements
    for refinement in stmt.search('refine'):
        target = find_refine_node(refinement)
        if target is None:
            continue
        if target in refined:
            err_add(ctx.errors, refinement.pos, 'MULTIPLE_REFINE',
                    (target.arg, refined[target]))
            continue
        refined[target] = refinement.pos

        for (keyword, valid_keywords, merge, v_fun) in _refinements:
            if merge:
                merge_from_refinement(target, refinement, keyword,
                                      valid_keywords, v_fun)
            else:
                replace_from_refinement(target, refinement, keyword,
                                        valid_keywords, v_fun)

        # replace all vendor-specific statements
        for s in refinement.substmts:
            if util.is_prefixed(s.keyword):
                old = target.search_one(s.keyword)
                if old is not None:
                    target.substmts.remove(old)
                s.parent = target
                target.substmts.append(s)
    v_inherit_properties(ctx, stmt.parent)
    for ch in refined:
        # after refinement, we need to re-run some of the tests, e.g. if
        # the refinement added a default value it needs to be checked.
        v_recheck_target(ctx, ch, reference=False)

def v_inherit_properties(ctx, stmt, child=None):
    def iter(s, config_value, allow_explicit):
        cfg = s.search_one('config')
        if cfg is not None:
            if config_value is None and not allow_explicit:
                err_add(ctx.errors, cfg.pos, 'CONFIG_IGNORED', ())
            elif cfg.arg == 'true' and config_value == False:
                err_add(ctx.errors, cfg.pos, 'INVALID_CONFIG', ())
            elif cfg.arg == 'true':
                config_value = True
            elif cfg.arg == 'false':
                config_value = False
        s.i_config = config_value
        if (hasattr(s, 'is_grammatically_valid') and
            s.is_grammatically_valid == False):
            return
        if s.keyword in _keyword_with_children:
            for ch in s.search('grouping'):
                iter(ch, None, True)
            for ch in s.search('grouping'):
                iter(ch, None, True)
            for ch in s.i_children:
                if ch.keyword in _keywords_with_no_explicit_config:
                    iter(ch, None, False)
                else:
                    if hasattr(ch, 'i_uses'):
                        iter(ch, config_value, True)
                    else:
                        iter(ch, config_value, allow_explicit)

    if child is not None:
        iter(child, stmt.i_config, True)
        return

    for s in stmt.search('grouping'):
        iter(s, None, True)
    for s in stmt.search('augment'):
        if hasattr(stmt,'i_config'):
           iter(s, stmt.i_config, True)
        else:
           iter(s, True, True)
    for s in stmt.i_children:
        if s.keyword in _keywords_with_no_explicit_config:
            iter(s, None, False)
        else:
            iter(s, True, True)

    # do not recurse in this phase
    return 'continue'

def v_expand_2_augment(ctx, stmt):
    """
    One-pass augment expansion algorithm: First observation: since we
    validate each imported module, all nodes that are augmented by
    other modules already exist.  For each node in the path to the
    target node, if it does not exist, it might get created by an
    augment later in this module.  This only applies to nodes defined
    in our namespace (since all other modules already are validated).
    For each such node, we add a temporary Statement instance, and
    store a pointer to it.  If we find such a temporary node in the
    nodes we add, we replace it with our real node, and delete it from
    the list of temporary nodes created.  When we're done with all
    augment statements, the list of temporary nodes should be empty,
    otherwise it is an error.
    """
    if hasattr(stmt, 'i_target_node'):
        # already expanded
        return
    stmt.i_target_node = find_target_node(ctx, stmt, is_augment=True)

    if stmt.i_target_node is None:
        return
    if not hasattr(stmt.i_target_node, 'i_children'):
        err_add(ctx.errors, stmt.pos, 'BAD_NODE_IN_AUGMENT',
                (stmt.i_target_node.i_module.arg, stmt.i_target_node.arg,
                 stmt.i_target_node.keyword))
        return

    def chk_mandatory(s):
        if s.keyword == 'leaf':
            m = s.search_one('mandatory')
            if m is not None and m.arg == 'true':
                err_add(ctx.errors, m.pos, 'AUGMENT_MANDATORY', s.arg)
        elif s.keyword == 'list' or s.keyword == 'leaf-list':
            m = s.search_one('min-elements')
            if m is not None and int(m.arg) >= 1:
                err_add(ctx.errors, m.pos, 'AUGMENT_MANDATORY', s.arg)
        elif s.keyword == 'container':
            p = s.search_one('presence')
            if p == None:
                for sc in s.i_children:
                    chk_mandatory(sc)
    # if we're augmenting another module, make sure we're not
    # trying to add a mandatory node
    if stmt.i_module.i_modulename != stmt.i_target_node.i_module.i_modulename:
        # 1.1 allows mandatory augment if the augment is conditional
        if stmt.i_module.i_version == '1' or stmt.search_one('when') is None:
            for sc in stmt.i_children:
                chk_mandatory(sc)

    # copy the expanded children into the target node
    def add_tmp_children(node, tmp_children):
        for tmp in tmp_children:
            ch = search_child(node.i_children, stmt.i_module.i_modulename,
                              tmp.arg)
            if ch is not None:
                del ch.i_module.i_undefined_augment_nodes[tmp]
                if not hasattr(ch, 'i_children'):
                    err_add(ctx.errors, tmp.pos, 'BAD_NODE_IN_AUGMENT',
                            (stmt.i_module.i_modulename, ch.arg,
                             ch.keyword))
                    raise Abort
                add_tmp_children(ch, tmp.i_children)
            elif node.keyword == 'choice' and tmp.keyword != 'case':
                # create an artifical case node for the shorthand
                new_case = create_new_case(ctx, node, tmp, expand=False)
                new_case.parent = node
            else:
                node.i_children.append(tmp)
                tmp.parent = node

    for c in stmt.i_children:
        c.i_augment = stmt

        ch = search_child(stmt.i_target_node.i_children,
                          stmt.i_module.i_modulename, c.arg)
        if ch is not None:
            if ch.keyword == '__tmp_augment__':
                # replace this node with the proper one,
                # and also do this recursively
                del ch.i_module.i_undefined_augment_nodes[ch]
                if not hasattr(c, 'i_children'):
                    err_add(ctx.errors, stmt.pos, 'BAD_NODE_IN_AUGMENT',
                            (stmt.i_module.i_modulename, c.arg,
                             c.keyword))
                    return
                idx = stmt.i_target_node.i_children.index(ch)
                stmt.i_target_node.i_children[idx] = c
                c.parent = stmt.i_target_node
                try:
                    add_tmp_children(c, ch.i_children)
                except Abort:
                    return
            else:
                err_add(ctx.errors, c.pos, 'DUPLICATE_CHILD_NAME',
                        (stmt.arg, stmt.pos, c.arg, ch.pos))
                return
        elif stmt.i_target_node.keyword == 'choice' and c.keyword != 'case':
            # create an artifical case node for the shorthand
            new_case = create_new_case(ctx, stmt.i_target_node, c, expand=False)
            new_case.parent = stmt.i_target_node
            v_inherit_properties(ctx, stmt.i_target_node, new_case)
        else:
            stmt.i_target_node.i_children.append(c)
            c.parent = stmt.i_target_node
            v_inherit_properties(ctx, stmt.i_target_node, c)
    for s in stmt.substmts:
        if s.keyword in _copy_augment_keywords:
            stmt.i_target_node.substmts.append(s)
            s.parent = stmt.i_target_node

def create_new_case(ctx, choice, child, expand=True):
    new_case = Statement(child.top, choice, child.pos, 'case', child.arg)
    v_init_stmt(ctx, new_case)
    child.parent = new_case
    new_case.i_children = [child]
    new_case.i_module = child.i_module
    choice.i_children.append(new_case)
    if expand:
        v_expand_1_children(ctx, child)
    return new_case

### Unique name check phase

def v_unique_name_defintions(ctx, stmt):
    """Make sure that all top-level definitions in a module are unique"""
    defs = [('typedef', 'TYPE_ALREADY_DEFINED', stmt.i_typedefs),
            ('grouping', 'GROUPING_ALREADY_DEFINED', stmt.i_groupings)]
    def f(s):
        for (keyword, errcode, dict) in defs:
            if s.keyword == keyword and s.arg in dict:
                err_add(ctx.errors, dict[s.arg].pos,
                        errcode, (s.arg, s.pos))

    for i in stmt.search('include'):
        submodulename = i.arg
        subm = ctx.get_module(submodulename)
        if subm is not None:
            for s in subm.substmts:
                for ss in s.substmts:
                    iterate_stmt(ss, f)


def v_unique_name_children(ctx, stmt):
    """Make sure that each child of stmt has a unique name"""

    def sort_pos(p1, p2):
        if p1.line < p2.line:
            return (p1,p2)
        else:
            return (p2,p1)

    dict = {}
    chs = stmt.i_children

    def check(c):
        key = (c.i_module.i_modulename, c.arg)
        if key in dict:
            dup = dict[key]
            (minpos, maxpos) = sort_pos(c.pos, dup.pos)
            pos = chk_uses_pos(c, maxpos)
            err_add(ctx.errors, pos,
                    'DUPLICATE_CHILD_NAME', (stmt.arg, stmt.pos, c.arg, minpos))
        else:
            dict[key] = c
        # also check all data nodes in the cases
        if c.keyword == 'choice':
            for case in c.i_children:
                for cc in case.i_children:
                    check(cc)

    for c in chs:
        check(c)

def v_unique_name_leaf_list(ctx, stmt):
    """Make sure config true leaf-lists do nothave duplicate defaults"""

    if not stmt.i_config:
        return
    seen = []
    for defval in stmt.i_default:
        if defval in seen:
            err_add(ctx.errors, stmt.pos, 'DUPLICATE_DEFAULT', (defval))
        else:
            seen.append(defval)

### Reference phase

def v_reference_list(ctx, stmt):
    if hasattr(stmt, 'i_is_validated') and stmt.i_is_validated == True:
        return
    stmt.i_is_validated = True

    def v_key():
        key = stmt.search_one('key')
        if stmt.i_config == True and key is None:
            if hasattr(stmt, 'i_uses_pos'):
                err_add(ctx.errors, stmt.i_uses_pos, 'NEED_KEY_USES',
                        (stmt.pos))
            else:
                err_add(ctx.errors, stmt.pos, 'NEED_KEY', ())

        stmt.i_key = []
        if key is not None and key.arg is not None:
            found = []
            for x in key.arg.split():
                if x == '':
                    continue
                if x.find(":") == -1:
                    name = x
                else:
                    [prefix, name] = x.split(':', 1)
                    if prefix != stmt.i_module.i_prefix:
                        err_add(ctx.errors, key.pos, 'BAD_KEY', x)
                        return
                ptr = attrsearch(name, 'arg', stmt.i_children)
                if x in found:
                    err_add(ctx.errors, key.pos, 'DUPLICATE_KEY', x)
                    return
                elif ((ptr is None) or (ptr.keyword != 'leaf')):
                    err_add(ctx.errors, key.pos, 'BAD_KEY', x)
                    return
                type_ = ptr.search_one('type')
                if stmt.i_module.i_version == '1':
                    if type_ is not None:
                        t = has_type(type_, ['empty'])
                        if t is not None:
                            err_add(ctx.errors, key.pos, 'BAD_TYPE_IN_KEY',
                                    (t.arg, x))
                            return
                default = ptr.search_one('default')
                if default is not None:
                        err_add(ctx.errors, default.pos, 'KEY_HAS_DEFAULT', ())
                for substmt in ['if-feature', 'when']:
                    s = ptr.search_one(substmt)
                    if s is not None:
                        err_add(ctx.errors, s.pos, 'KEY_BAD_SUBSTMT', substmt)
                mandatory = ptr.search_one('mandatory')
                if mandatory is not None and mandatory.arg == 'false':
                    err_add(ctx.errors, mandatory.pos,
                            'KEY_HAS_MANDATORY_FALSE', ())

                if ptr.i_config != stmt.i_config:
                    err_add(ctx.errors, ptr.search_one('config').pos,
                            'KEY_BAD_CONFIG', name)

                stmt.i_key.append(ptr)
                ptr.i_is_key = True
                found.append(x)

    def v_unique():
        # i_unique is a list of entries, one entry per 'unique' stmt.
        # each entry is a list of pointers to the nodes that make up
        # the unique constraint.
        stmt.i_unique = []
        uniques = stmt.search('unique')
        for u in uniques:
            found = []
            uconfig = None
            for expr in u.arg.split():
                if expr == '':
                    continue
                ptr = stmt
                for x in expr.split('/'):
                    if x == '':
                        continue
                    if ptr.keyword not in ['container', 'list',
                                           'choice', 'case']:
                        err_add(ctx.errors, u.pos, 'BAD_UNIQUE_PART', x)
                        return
                    if x.find(":") == -1:
                        name = x
                    else:
                        [prefix, name] = x.split(':', 1)
                        if prefix != stmt.i_module.i_prefix:
                            err_add(ctx.errors, u.pos, 'BAD_UNIQUE_PART', x)
                            return
                    ptr = attrsearch(name, 'arg', ptr.i_children)
                    if ptr is None:
                        err_add(ctx.errors, u.pos, 'BAD_UNIQUE_PART', x)
                        return
                    if ptr.keyword == 'list':
                        err_add(ctx.errors, u.pos, 'BAD_UNIQUE_PART_LIST', x)
                if ((ptr is None) or (ptr.keyword != 'leaf')):
                    err_add(ctx.errors, u.pos, 'BAD_UNIQUE', expr)
                    return
                if ptr in found:
                    err_add(ctx.errors, u.pos, 'DUPLICATE_UNIQUE', expr)
                if hasattr(ptr, 'i_config'):
                    if uconfig is None:
                        uconfig = ptr.i_config
                    elif uconfig != ptr.i_config:
                        err_add(ctx.errors, u.pos, 'BAD_UNIQUE_CONFIG', expr)
                        return
                # add this unique statement to ptr's list of unique conditions
                # it is part of.
                ptr.i_uniques.append(u)
                found.append(ptr)
            if found == []:
                err_add(ctx.errors, u.pos, 'BAD_UNIQUE', u.arg)
                return
            # check if all leafs in the unique statements are keys
            if len(list(stmt.i_key)) > 0:
                key = list(stmt.i_key)
                for f in found:
                    if f in key:
                        key.remove(f)
                if len(key) == 0:
                    err_add(ctx.errors, u.pos, 'UNIQUE_IS_KEY', ())
            u.i_leafs = found
            stmt.i_unique.append((u, found))

    v_key()
    v_unique()

def v_reference_choice(ctx, stmt):
    """Make sure that the default case exists"""
    d = stmt.search_one('default')
    if d is not None:
        m = stmt.search_one('mandatory')
        if m is not None and m.arg == 'true':
            err_add(ctx.errors, stmt.pos, 'DEFAULT_AND_MANDATORY', ())
        ptr = attrsearch(d.arg, 'arg', stmt.i_children)
        if ptr is None:
            err_add(ctx.errors, d.pos, 'DEFAULT_CASE_NOT_FOUND', d.arg)
        else:
            # make sure there are no mandatory nodes in the default case
            def chk_no_defaults(s):
                for c in s.i_children:
                    if c.keyword in ('leaf', 'choice'):
                        m = c.search_one('mandatory')
                        if m is not None and m.arg == 'true':
                            err_add(ctx.errors, c.pos,
                                    'MANDATORY_NODE_IN_DEFAULT_CASE', ())
                    elif c.keyword in ('list', 'leaf-list'):
                        m = c.search_one('min-elements')
                        if m is not None and int(m.arg) > 0:
                            err_add(ctx.errors, c.pos,
                                    'MANDATORY_NODE_IN_DEFAULT_CASE', ())
                    elif c.keyword == 'container':
                        p = c.search_one('presence')
                        if p == None or p.arg == 'false':
                            chk_no_defaults(c)
            chk_no_defaults(ptr)

def v_reference_leaf_leafref(ctx, stmt):
    """Verify that all leafrefs in a leaf or leaf-list have correct path"""

    if (hasattr(stmt, 'i_leafref') and
        stmt.i_leafref is not None and
        stmt.i_leafref_expanded is False):
        path_type_spec = stmt.i_leafref
        not_req_inst = not(path_type_spec.require_instance)
        x = validate_leafref_path(ctx, stmt,
                                  path_type_spec.path_spec,
                                  path_type_spec.path_,
                                  accept_non_config_target=not_req_inst
        )
        if x is None:
            return
        ptr, expanded_path, path_list = x
        path_type_spec.i_target_node = ptr
        path_type_spec.i_expanded_path = expanded_path
        path_type_spec.i_path_list = path_list
        stmt.i_leafref_expanded = True
        if ptr is not None:
            stmt.i_leafref_ptr = (ptr, path_type_spec.pos)

def v_reference_must(ctx, stmt):
    # verify that the xpath expression is correct, and that
    # each prefix is defined
    # NOTE: currently only primitive tokenization is done; we should
    # also parse the expression to detect more errors
    v_xpath(ctx, stmt)

def v_xpath(ctx, stmt):
    try:
        toks = xpath.tokens(stmt.arg)
        for (tokname, s) in toks:
            if tokname == 'name' or tokname == 'prefix-match':
                i = s.find(':')
                if i != -1:
                    prefix = s[:i]
                    prefix_to_module(stmt.i_module, prefix, stmt.pos,
                                     ctx.errors)
            elif tokname == 'literal':
                # kind of hack to detect qnames, and mark the prefixes
                # as being used in order to avoid warnings.
                if s[0] == s[-1] and s[0] in ("'", '"'):
                    s = s[1:-1]
                    i = s.find(':')
                    # make sure there is just one : present
                    if i != -1 and s[i+1:].find(':') == -1:
                        prefix = s[:i]
                        # we don't want to report an error; just mark the
                        # prefix as being used.
                        my_errors = []
                        prefix_to_module(stmt.i_module, prefix, stmt.pos,
                                         my_errors)
                        for (pos, code, arg) in my_errors:
                            if code == 'PREFIX_NOT_DEFINED':
                                err_add(ctx.errors, pos,
                                        'WPREFIX_NOT_DEFINED', arg)
            elif ctx.lax_xpath_checks == True:
                pass
            elif tokname == 'variable':
                err_add(ctx.errors, stmt.pos, 'XPATH_VARIABLE', s)
            elif tokname == 'function':
                if not (s in xpath.core_functions or
                        s in yang_xpath_functions or
                        (stmt.i_module.i_version != '1' and
                         s in yang_1_1_xpath_functions) or
                        s in extra_xpath_functions):
                    err_add(ctx.errors, stmt.pos, 'XPATH_FUNCTION', s)

    except SyntaxError as e:
        err_add(ctx.errors, stmt.pos, 'XPATH_SYNTAX_ERROR', e)

def v_reference_when(ctx, stmt):
    v_xpath(ctx, stmt)

def v_reference_deviation(ctx, stmt):
    stmt.i_target_node = find_target_node(ctx, stmt)

def v_reference_deviate(ctx, stmt):
    if stmt.parent.i_target_node is None:
        # this is set in v_reference_deviation above.  if none
        # is found, an error has already been reported.
        return
    t = stmt.parent.i_target_node
    if stmt.arg == 'not-supported':
        # make sure there are no sibling deviate statements
        siblings = stmt.parent.search('deviate')
        idx = siblings.index(stmt)
        del siblings[idx]
        if len(siblings) > 0:
            err_add(ctx.errors, siblings[0].pos,
                    'BAD_DEVIATE_WITH_NOT_SUPPORTED', ())
            return
        if ((t.parent.keyword == 'list') and
            (t in t.parent.i_key)):
            err_add(ctx.errors, stmt.pos, 'BAD_DEVIATE_KEY',
                    (t.i_module.arg, t.arg))
            return
        t.i_this_not_supported = True
        if not hasattr(t.parent, 'i_not_supported'):
            t.parent.i_not_supported = []
        t.parent.i_not_supported.append(t)
        # delete the node from i_children
        idx = t.parent.i_children.index(t)
        del t.parent.i_children[idx]
        # find and delete the node from substmts
        # it may not be there if it is a shorthand case
        t1 = t.parent.search_one(t.keyword, t.arg, t.parent.substmts)
        if t1 is not None:
            idx = t.parent.substmts.index(t1)
            del t.parent.substmts[idx]
    elif stmt.arg == 'add':
        for c in stmt.substmts:
            if (c.keyword == 'config'
                and hasattr(t, 'i_config')):
                # config is special: since it is an inherited property
                # with a default, all nodes has a config property.  this means
                # that it can only be replaced.
                err_add(ctx.errors, c.pos, 'BAD_DEVIATE_ADD',
                        (c.keyword, t.i_module.arg, t.arg))
            elif c.keyword in _singleton_keywords:
                if t.search_one(c.keyword) != None:
                    err_add(ctx.errors, c.pos, 'BAD_DEVIATE_ADD',
                            (c.keyword, t.i_module.arg, t.arg))
                elif t.keyword not in _valid_deviations[c.keyword]:
                    err_add(ctx.errors, c.pos, 'BAD_DEVIATE_TYPE',
                            c.keyword)
                else:
                    t.substmts.append(c)
            else:
                # multi-valued keyword; just add the statement if it is valid
                if (c.keyword not in _valid_deviations):
                    if util.is_prefixed(c.keyword):
                        (prefix, name) = c.keyword
                        pmodule = prefix_to_module(c.i_module, prefix, c.pos,
                                                   [])
                        if (pmodule is not None and
                            pmodule.modulename in grammar.extension_modules):
                            err_add(ctx.errors, c.pos, 'BAD_DEVIATE_TYPE',
                                    c.keyword)

                        else:
                            # unknown module, let's assume the extension can
                            # be deviated
                            t.substmts.append(c)
                    else:
                        err_add(ctx.errors, c.pos, 'BAD_DEVIATE_TYPE',
                                c.keyword)
                elif t.keyword not in _valid_deviations[c.keyword]:
                    err_add(ctx.errors, c.pos, 'BAD_DEVIATE_TYPE',
                            c.keyword)

                else:
                    t.substmts.append(c)
    else: # delete or replace
        for c in stmt.substmts:
            if (c.keyword == 'config'
                and stmt.arg == 'replace'
                and hasattr(t, 'i_config')):
                # config is special: since it is an inherited property
                # with a default, all nodes has a config property.  this means
                # that it can only be replaced.
                # first, set the property...
                if c.arg == 'true':
                    t.i_config = True
                elif c.arg == 'false':
                    t.i_config = False
                # ... and then modify the original statement, if any
                old = t.search_one(c.keyword)
                if old is not None:
                    old.arg = c.arg
                else:
                    t.substmts.append(c)
                # make sure the target's children have proper config stmts
                sub = t.substmts
                if hasattr(t, 'i_children'):
                    sub = sub + t.i_children
                for d in sub:
                    if d.keyword in data_definition_keywords:
                        if (hasattr(d, 'i_config') and
                            d.i_config != t.i_config):
                            # this child has another config property,
                            # maybe fix the statment
                            old = d.search_one('config')
                            if old is None:
                                negc = copy.copy(c)
                                if c.arg == 'true':
                                    negc.arg = 'false'
                                else:
                                    negc.arg = 'true'
                                d.substmts.append(negc)

            if c.keyword in _singleton_keywords:
                old = t.search_one(c.keyword)
            else:
                old = t.search_one(c.keyword, c.arg)
            if old is None:
                err_add(ctx.errors, c.pos, 'BAD_DEVIATE_DEL',
                        (c.keyword, t.i_module.arg, t.arg))
            else:
                idx = t.substmts.index(old)
                del t.substmts[idx]
                if stmt.arg == 'replace':
                    if (c.keyword == 'type'
                        and c.i_typedef is not None
                        and c.arg.find(":") == -1
                        and t.i_module.i_prefix !=
                            c.i_module.i_prefix):
                        c.arg = c.i_module.i_prefix + ':' + c.arg
                    t.substmts.append(c)

# after deviation, we need to re-run some of the tests, e.g. if
# the deviation added a default value it needs to be checked.
def v_reference_deviation_4(ctx, stmt):
    if not hasattr(stmt, 'i_target_node') or stmt.i_target_node is None:
        # this is set in v_reference_deviation above.  if none
        # is found, an error has already been reported.
        return
    if hasattr(stmt.i_target_node, 'i_this_not_supported'):
        return
    v_recheck_target(ctx, stmt.i_target_node, reference=True)

def v_recheck_target(ctx, t, reference=False):
    if t.keyword == 'leaf':
        v_type_leaf(ctx, t)
        if reference:
            v_reference_leaf_leafref(ctx, t)
    elif t.keyword == 'leaf-list':
        v_type_leaf_list(ctx, t)
        if reference:
            v_reference_leaf_leafref(ctx, t)
    elif t.keyword == 'list':
        t.i_is_validated = False
        if reference:
            v_reference_list(ctx, t)

### Unused definitions phase

def v_unused_module(ctx, module):
    for prefix in module.i_unused_prefixes:
        import_ = module.i_unused_prefixes[prefix]
        err_add(ctx.errors, import_.pos,
                'UNUSED_IMPORT', import_.arg)

    for s in module.i_undefined_augment_nodes:
        err_add(ctx.errors, s.pos, 'NODE_NOT_FOUND',
                (s.i_module.arg, s.arg))

def v_unused_typedef(ctx, stmt):
    if stmt.parent.parent is not None:
        # this is a locallay scoped typedef
        if stmt.i_is_unused == True:
            err_add(ctx.errors, stmt.pos,
                    'UNUSED_TYPEDEF', stmt.arg)

def v_unused_grouping(ctx, stmt):
    if stmt.parent.parent is not None:
        # this is a locallay scoped grouping
        if stmt.i_is_unused == True:
            err_add(ctx.errors, stmt.pos,
                    'UNUSED_GROUPING', stmt.arg)

### Strict phase

def v_strict_xpath(ctx, stmt):
    if not ctx.strict:
        return
    if stmt.i_module.i_version != '1':
        # deref is valid in 1.1
        return
    try:
        toks = xpath.tokens(stmt.arg)
        for (tokname, s) in toks:
            if tokname == 'function' and s == 'deref':
                err_add(ctx.errors, stmt.pos, 'STRICT_XPATH_FUNCTION', s)
    except SyntaxError as e:
        # already reported
        pass

### Utility functions

def chk_uses_pos(s, pos):
    if hasattr(s, 'i_uses_pos'):
        return s.i_uses_pos
    else:
        return pos

def modulename_to_module(module, modulename, revision=None):
    if modulename == module.arg:
        return module
    # even if the prefix is defined, the module might not be
    # loaded; the load might have failed
    return module.i_ctx.get_module(modulename, revision)

def has_type(type, names):
    """Return type with name if `type` has name as one of its base types,
    and name is in the `names` list.  otherwise, return None."""
    if type.arg in names:
        return type
    for t in type.search('type'): # check all union's member types
        r = has_type(t, names)
        if r is not None:
            return r
    if not hasattr(type, 'i_typedef'):
        return None
    if (type.i_typedef is not None and
        hasattr(type.i_typedef, 'i_is_circular') and
        type.i_typedef.i_is_circular == False):
        t = type.i_typedef.search_one('type')
        if t is not None:
            return has_type(t, names)
    return None

def is_mandatory_node(stmt):
    if hasattr(stmt, 'i_config') and stmt.i_config == False:
        return False
    if stmt.keyword == 'leaf':
        m = stmt.search_one('mandatory')
        if m is not None and m.arg == 'true':
            return True
    elif stmt.keyword in ('list', 'leaf-list'):
        m = stmt.search_one('min-elements')
        if m is not None and int(m.arg) > 0:
            return True
    elif stmt.keyword == 'container':
        p = stmt.search_one('presence')
        if p is None:
            for c in stmt.i_children:
                if is_mandatory_node(c):
                    return True
    return False

def search_child(children, modulename, identifier):
    for child in children:
        if child.arg == identifier:
            if ((child.i_module.i_modulename == modulename) or
                child.i_module.i_including_modulename is not None and
                child.i_module.i_including_modulename == modulename):
                return child
    return None

def search_data_node(children, modulename, identifier, last_skipped = None):
    skip = ['choice', 'case']
    if last_skipped is not None:
        skip.append(last_skipped)
    for child in children:
        if child.keyword in skip:
            r = search_data_node(child.i_children,
                                 modulename, identifier)
            if r is not None:
                return r
        elif ((child.arg == identifier) and
              (child.i_module.i_modulename == modulename)):
            return child
    return None

def search_typedef(stmt, name):
    """Search for a typedef in scope
    First search the hierarchy, then the module and its submodules."""
    mod = stmt.i_orig_module
    while stmt is not None:
        if name in stmt.i_typedefs:
            t = stmt.i_typedefs[name]
            if (mod is not None and
                mod != t.i_orig_module and
                t.i_orig_module.keyword == 'submodule'):
                # make sure this submodule is included
                if mod.search_one('include', t.i_orig_module.arg) is None:
                    return None
            return t
        stmt = stmt.parent
    return None

def search_grouping(stmt, name):
    """Search for a grouping in scope
    First search the hierarchy, then the module and its submodules."""
    mod = stmt.i_orig_module
    while stmt is not None:
        if name in stmt.i_groupings:
            g = stmt.i_groupings[name]
            if (mod is not None and
                mod != g.i_orig_module and
                g.i_orig_module.keyword == 'submodule'):
                # make sure this submodule is included
                if mod.search_one('include', g.i_orig_module.arg) is None:
                    return None
            return g
        stmt = stmt.parent
    return None

def search_data_keyword_child(children, modulename, identifier):
    for child in children:
        if ((child.arg == identifier) and
            (child.i_module.i_modulename == modulename) and
            child.keyword in _data_keywords):
            return child
    return None

def find_target_node(ctx, stmt, is_augment=False):
    if (hasattr(stmt, 'is_grammatically_valid') and
        stmt.is_grammatically_valid == False):
        return None
    if stmt.arg.startswith("/"):
        is_absolute = True
        arg = stmt.arg
    else:
        is_absolute = False
        arg = "/" + stmt.arg # to make node_id_part below work
    # parse the path into a list of two-tuples of (prefix,identifier)
    path = [(m[1], m[2]) for m in syntax.re_schema_node_id_part.findall(arg)]
    # find the module of the first node in the path
    (prefix, identifier) = path[0]
    module = prefix_to_module(stmt.i_module, prefix, stmt.pos, ctx.errors)
    if module is None:
        # error is reported by prefix_to_module
        return None

    if (stmt.parent.keyword in ('module', 'submodule') or
        is_absolute):
        # find the first node
        node = search_child(module.i_children, module.i_modulename, identifier)
        if not is_submodule_included(stmt, node):
            node = None
        if node is None:
            err_add(ctx.errors, stmt.pos, 'NODE_NOT_FOUND',
                    (module.i_modulename, identifier))
            return None
    else:
        chs = [c for c in stmt.parent.parent.i_children \
                   if hasattr(c, 'i_uses') and c.i_uses[0] == stmt.parent]
        node = search_child(chs, module.i_modulename, identifier)
        if not is_submodule_included(stmt, node):
            node = None
        if node is None:
            err_add(ctx.errors, stmt.pos, 'NODE_NOT_FOUND',
                    (module.i_modulename, identifier))
            return None

    # then recurse down the path
    for (prefix, identifier) in path[1:]:
        if hasattr(node, 'i_children'):
            module = prefix_to_module(stmt.i_module, prefix, stmt.pos,
                                      ctx.errors)
            if module is None:
                return None
            child = search_child(node.i_children, module.i_modulename,
                                 identifier)
            if child is None and module == stmt.i_module and is_augment:
                # create a temporary statement
                child = Statement(node.top, node, stmt.pos, '__tmp_augment__',
                                  identifier)
                v_init_stmt(ctx, child)
                child.i_module = module
                child.i_children = []
                child.i_config = node.i_config
                node.i_children.append(child)
                # keep track of this temporary statement
                stmt.i_module.i_undefined_augment_nodes[child] = child
            elif child is None:
                err_add(ctx.errors, stmt.pos, 'NODE_NOT_FOUND',
                        (module.i_modulename, identifier))
                return None
            node = child
        else:
            err_add(ctx.errors, stmt.pos, 'NODE_NOT_FOUND',
                    (module.i_modulename, identifier))
            return None
    return node

def iterate_stmt(stmt, f):
    def _iterate(stmt):
        res = f(stmt)
        if res == 'stop':
            raise Abort
        elif res == 'continue':
            pass
        else:
            # default is to recurse
            for s in stmt.substmts:
                _iterate(s)

    try:
        _iterate(stmt)
    except Abort:
        pass

def iterate_i_children(stmt, f):
    def _iterate(stmt):
        res = f(stmt)
        if res == 'stop':
            raise Abort
        elif res == 'continue':
            pass
        else:
            # default is to recurse
            if hasattr(stmt, 'i_children'):
                for s in stmt.i_children:
                    _iterate(s)

    try:
        _iterate(stmt)
    except Abort:
        pass

def is_submodule_included(src, tgt):
    """Check that the tgt's submodule is included by src, if they belong
    to the same module."""
    if tgt is None or not hasattr(tgt, 'i_orig_module'):
        return True
    if (tgt.i_orig_module.keyword == 'submodule' and
        src.i_orig_module != tgt.i_orig_module and
        src.i_orig_module.i_modulename == tgt.i_orig_module.i_modulename):
        if src.i_orig_module.search_one('include',
                                        tgt.i_orig_module.arg) is None:
            return False
    return True

def validate_leafref_path(ctx, stmt, path_spec, path,
                          accept_non_leaf_target=False,
                          accept_non_config_target=False):
    """Return the leaf that the path points to and the expanded path arg,
    or None on error."""

    pathpos = path.pos

    # Unprefixed paths in typedefs in YANG 1 were underspecified.  In
    # YANG 1.1 the semantics are defined.  The code below is compatible
    # with old pyang for YANG 1 modules.

    # If an un-prefixed identifier is found, it defaults to the
    # module where the path is defined, except if found within
    # a grouping, in which case it defaults to the module where the
    # grouping is used.
    if (path.parent.parent is not None and
        path.parent.parent.keyword == 'typedef'):
        if path.i_module.i_version == '1':
            local_module = path.i_module
        else:
            local_module = stmt.i_module
    elif stmt.keyword == 'module':
        local_module = stmt
    else:
        local_module = stmt.i_module
    if stmt.keyword == 'typedef':
        in_typedef = True
    else:
        in_typedef = False

    def find_identifier(identifier):
        if util.is_prefixed(identifier):
            (prefix, name) = identifier
            pmodule = prefix_to_module(path.i_module, prefix, stmt.pos,
                                       ctx.errors)
            if pmodule is None:
                raise NotFound
            return (pmodule, name)
        elif in_typedef and stmt.i_module.i_version != '1':
            raise Abort
        else: # local identifier
            return (local_module, identifier)

    def is_identifier(x):
        if util.is_local(x):
            return True
        if type(x) == type(()) and len(x) == 2:
            return True
        return False

    def is_predicate(x):
        if type(x) == type(()) and len(x) == 4 and x[0] == 'predicate':
            return True
        return False

    def follow_path(ptr, up, dn):
        path_list = []
        last_skipped = None
        if up == -1: # absolute path
            (pmodule, name) = find_identifier(dn[0])
            ptr = search_child(pmodule.i_children, pmodule.i_modulename, name)
            if not is_submodule_included(path, ptr):
                ptr = None
            if ptr is None:
                # check all our submodules
                for inc in path.i_orig_module.search('include'):
                    submod = ctx.get_module(inc.arg)
                    if submod is not None:
                        ptr = search_child(submod.i_children,
                                           submod.arg, name)
                        if ptr is not None:
                            break
                if ptr is None:
                    err_add(ctx.errors, pathpos, 'LEAFREF_IDENTIFIER_NOT_FOUND',
                            (pmodule.arg, name, stmt.arg, stmt.pos))
                    raise NotFound
            path_list.append(('dn', ptr))
            dn = dn[1:]
        else:
            while up > 0:
                if ptr is None:
                    err_add(ctx.errors, pathpos, 'LEAFREF_TOO_MANY_UP',
                            (stmt.arg, stmt.pos))
                    raise NotFound
                if ptr.keyword in ('augment', 'grouping'):
                    # don't check the path here - check in the expanded tree
                    raise Abort
                ptr = ptr.parent
                if ptr is None:
                    err_add(ctx.errors, pathpos, 'LEAFREF_TOO_MANY_UP',
                            (stmt.arg, stmt.pos))
                    raise NotFound
                while ptr.keyword in ['case', 'choice', 'input', 'output']:
                    if ptr.keyword in ['input', 'output']:
                        last_skipped = ptr.keyword
                    ptr = ptr.parent
                    if ptr is None:
                        err_add(ctx.errors, pathpos, 'LEAFREF_TOO_MANY_UP',
                                (stmt.arg, stmt.pos))
                        raise NotFound
                    # continue after the case, maybe also skip the choice
                if ptr is None:
                    err_add(ctx.errors, pathpos, 'LEAFREF_TOO_MANY_UP',
                            (stmt.arg, stmt.pos))
                    raise NotFound
                path_list.append(('up', ptr))
                up = up - 1
            if ptr is None: # or ptr.keyword == 'grouping':
                err_add(ctx.errors, pathpos, 'LEAFREF_TOO_MANY_UP',
                        (stmt.arg, stmt.pos))
                raise NotFound
        if ptr.keyword in ('augment', 'grouping'):
            # don't check the path here - check in the expanded tree
            raise Abort
        i = 0
        key_list = None
        keys = []
        while i < len(dn):
            if is_identifier(dn[i]) == True:
                (pmodule, name) = find_identifier(dn[i])
                module_name = pmodule.i_modulename
            elif ptr.keyword == 'list': # predicate on a list, good
                key_list = ptr
                keys = []
                # check each predicate
                while i < len(dn) and is_predicate(dn[i]) == True:
                    # unpack the predicate
                    (_tag, keyleaf, pup, pdn) = dn[i]
                    (pmodule, pname) = find_identifier(keyleaf)
                    # make sure the keyleaf is really a key in the list
                    pleaf = search_child(ptr.i_key, pmodule.i_modulename, pname)
                    if pleaf is None:
                        err_add(ctx.errors, pathpos, 'LEAFREF_NO_KEY',
                                (pmodule.arg, pname, stmt.arg, stmt.pos))
                        raise NotFound
                    # make sure it's not already referenced
                    if keyleaf in keys:
                        err_add(ctx.errors, pathpos, 'LEAFREF_MULTIPLE_KEYS',
                                (pmodule.arg, pname, stmt.arg, stmt.pos))
                        raise NotFound
                    keys.append((pmodule.arg, pname))
                    if pup == 0:
                        i = i + 1
                        break
                    # check what this predicate refers to; make sure it's
                    # another leaf; either of type leafref to keyleaf, OR same
                    # type as the keyleaf
                    (xkey_list, x_key, xleaf, _x) = follow_path(stmt, pup, pdn)
                    stmt.i_derefed_leaf = xleaf
                    if xleaf.keyword != 'leaf':
                        err_add(ctx.errors, pathpos,
                                'LEAFREF_BAD_PREDICATE_PTR',
                                (pmodule.arg, pname, xleaf.arg, xleaf.pos))
                        raise NotFound
                    i = i + 1
                continue
            else:
                err_add(ctx.errors, pathpos, 'LEAFREF_BAD_PREDICATE',
                        (ptr.i_module.arg, ptr.arg, stmt.arg, stmt.pos))
                raise NotFound
            if ptr.keyword in _keyword_with_children:
                ptr = search_data_node(ptr.i_children, module_name, name,
                                       last_skipped)
                if not is_submodule_included(path, ptr):
                    ptr = None
                if ptr is None:
                    err_add(ctx.errors, pathpos, 'LEAFREF_IDENTIFIER_NOT_FOUND',
                            (module_name, name, stmt.arg, stmt.pos))
                    raise NotFound
            else:
                err_add(ctx.errors, pathpos, 'LEAFREF_IDENTIFIER_BAD_NODE',
                        (module_name, name, stmt.arg, stmt.pos,
                         util.keyword_to_str(ptr.keyword)))
                raise NotFound
            path_list.append(('dn', ptr))
            i = i + 1
        return (key_list, keys, ptr, path_list)

    try:
        if path_spec is None: # e.g. invalid path
            return None
        (up, dn, derefup, derefdn) = path_spec
        if derefup > 0:
            # first follow the deref
            (key_list, keys, ptr, _x) = follow_path(stmt, derefup, derefdn)
            if ptr.keyword != 'leaf':
                err_add(ctx.errors, pathpos, 'LEAFREF_DEREF_NOT_LEAFREF',
                        (ptr.arg, ptr.pos))
                return None
            if ptr.i_leafref is None:
                err_add(ctx.errors, pathpos, 'LEAFREF_DEREF_NOT_LEAFREF',
                        (ptr.arg, ptr.pos))
                return None
            stmt.i_derefed_leaf = ptr
            # make sure the referenced leaf is expanded
            if ptr.i_leafref_expanded is False:
                v_reference_leaf_leafref(ctx, ptr)
            if ptr.i_leafref_ptr is None:
                return None
            (derefed_stmt, _pos) = ptr.i_leafref_ptr
            if derefed_stmt is None:
                # FIXME: what is this??
                return None
            if not hasattr(derefed_stmt, 'i_is_key'):
                # it follows from the YANG spec which says that predicates
                # are only used for constraining keys that the derefed stmt
                # must be a key
                err_add(ctx.errors, pathpos, 'LEAFREF_DEREF_NOT_KEY',
                        (ptr.arg, ptr.pos,
                         derefed_stmt.arg, derefed_stmt.pos))
                return None
            # split ptr's leafref path into two parts:
            # '/a/b/c' --> '/a/b', 'c'
            m = re_path.match(ptr.i_leafref.i_expanded_path)
            s1 = m.group(1)
            s2 = m.group(2)
            # split the deref path into two parts:
            # 'deref(../a)/b' --> '../a', 'b'
            m = re_deref.match(path.arg)
            d1 = m.group(1)
            d2 = m.group(2)
            expanded_path = "%s[%s = current()/%s]/%s" % \
                (s1, s2, d1, d2)
            (key_list, keys, ptr, path_list) = follow_path(derefed_stmt, up, dn)
        else:
            (key_list, keys, ptr, path_list) = follow_path(stmt, up, dn)
            expanded_path = path.arg
        # ptr is now the node that the leafref path points to
        # check that it is a leaf
        if (ptr.keyword not in ('leaf', 'leaf-list') and
            not accept_non_leaf_target):
            err_add(ctx.errors, pathpos, 'LEAFREF_NOT_LEAF',
                    (stmt.arg, stmt.pos))
            return None
        if (key_list == ptr.parent and
            (ptr.i_module.i_modulename, ptr.arg) in keys):
            err_add(ctx.errors, pathpos, 'LEAFREF_MULTIPLE_KEYS',
                    (ptr.i_module.i_modulename, ptr.arg, stmt.arg, stmt.pos))
        if ((hasattr(stmt, 'i_config') and stmt.i_config == True) and
            hasattr(ptr, 'i_config') and ptr.i_config == False
            and not accept_non_config_target):
            err_add(ctx.errors, pathpos, 'LEAFREF_BAD_CONFIG',
                    (stmt.arg, ptr.arg, ptr.pos))
        if ptr == stmt:
            err_add(ctx.errors, pathpos, 'CIRCULAR_DEPENDENCY',
                    ('leafref', path.arg))
            return None
        return ptr, expanded_path, path_list
    except NotFound:
        return None
    except Abort:
        return None

### structs used to represent a YANG module

## Each statement in YANG is represented as an instance of Statement.

class Statement(object):
    def __init__(self, top, parent, pos, keyword, arg=None):
        self.top = top
        """pointer to the top-level Statement"""

        self.parent = parent
        """pointer to the parent Statement"""

        self.pos = copy.copy(pos)
        """position in input stream, for error reporting"""
        if self.pos is not None and self.pos.top is None:
            self.pos.top = self

        self.raw_keyword = keyword
        """the name of the statement
        one of: string() | (prefix::string(), string())"""

        self.keyword = keyword
        """the name of the statement
        one of: string() | (modulename::string(), string())"""

        self.ext_mod = None
        """the name of the module where the extension is defined, if any"""

        self.arg = arg
        """the statement's argument;  a string or None"""

        self.substmts = []
        """the statement's substatements; a list of Statements"""

    def search(self, keyword, children=None):
        """Return list of receiver's substmts with `keyword`.
        """
        if children is None:
            children = self.substmts
        return [ ch for ch in children if ch.keyword == keyword ]

    def search_one(self, keyword, arg=None, children=None):
        """Return receiver's substmt with `keyword` and optionally `arg`.
        """
        if children is None:
            children = self.substmts
        for ch in children:
            if ch.keyword == keyword and (arg is None or ch.arg == arg):
                return ch
        return None

    def copy(self, parent=None, uses=None, uses_top=True,
             nocopy=[], ignore=[], copyf=None):
        new = copy.copy(self)
        new.pos = copy.copy(new.pos)
        if uses is not None:
            if hasattr(new, 'i_uses'):
                new.i_uses.insert(0, uses)
            else:
                new.i_uses = [uses]
            new.i_uses_pos = uses.pos
            new.i_uses_top = uses_top
        if parent == None:
            new.parent = self.parent
        else:
            new.parent = parent
        new.substmts = []
        for s in self.substmts:
            if s.keyword in ignore:
                pass
            elif s.keyword in nocopy:
                new.substmts.append(s)
            else:
                new.substmts.append(s.copy(new, uses, False,
                                           nocopy, ignore, copyf))
        if copyf is not None:
            copyf(self, new)
        return new

    def main_module(self):
        """Return the main module to which the receiver belongs."""
        if self.i_module.keyword == "submodule":
            return self.i_module.i_ctx.get_module(
                self.i_module.i_including_modulename)
        return self.i_module

    def pprint(self, indent='', f=None):
        """debug function"""
        if self.arg is not None:
          print(indent + util.keyword_to_str(self.keyword) + " " + self.arg)
        else:
          print(indent + util.keyword_to_str(self.keyword))
        if f is not None:
             f(self, indent)
        for x in self.substmts:
            x.pprint(indent + ' ', f)
        if hasattr(self, 'i_children') and len(self.i_children) > 0:
           print(indent + '--- BEGIN i_children ---')
           for x in self.i_children:
               x.pprint(indent + ' ', f)
           print(indent + '--- END i_children ---')


## FIXME: not used
def validate_status(errors, x, y, defn, ref):
    xstatus = x.status
    if xstatus is None:
        xstatus = 'current'
    ystatus = y.status
    if ystatus is None:
        ystatus = 'current'
    if xstatus == 'current' and ystatus == 'deprecated':
        err_add(errors, x.pos, 'CURRENT_USES_DEPRECATED', (defn, ref))
    elif xstatus == 'current' and ystatus == 'obsolete':
        err_add(errors, x.pos, 'CURRENT_USES_OBSOLETE', (defn, ref))
    elif xstatus == 'deprecated' and ystatus == 'obsolete':
        err_add(errors, x.pos, 'DEPRECATED_USES_OBSOLETE', (defn, ref))

def print_tree(stmt, substmts=True, i_children=True, indent=0):
    istr = "  "
    print("%s%s %s      %s %s" % (indent * istr, stmt.keyword,
                                  stmt.arg, stmt, stmt.parent))
    if substmts and stmt.substmts != []:
        print("%s  substatements:" % (indent * istr))
        for s in stmt.substmts:
            print_tree(s, substmts, i_children, indent+1)
    if i_children and hasattr(stmt, 'i_children'):
        print("%s  i_children:" % (indent * istr))
        for s in stmt.i_children:
            print_tree(s, substmts, i_children, indent+1)

def mk_path_str(s, with_prefixes=False):
    """Returns the XPath path of the node"""
    if s.keyword in ['choice', 'case']:
        return mk_path_str(s.parent)
    def name(s):
        if with_prefixes:
            return s.i_module.i_prefix + ":" + s.arg
        else:
            return s.arg
    if s.parent.keyword in ['module', 'submodule']:
        return "/" + name(s)
    else:
        p = mk_path_str(s.parent, with_prefixes)
        return p + "/" + name(s)
