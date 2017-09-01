"""YANG usage guidelines plugin
See RFC 6087
Other plugins can derive from this and make it more specific, e.g.,
ietf.py derives from this and sets the namespace and module name prefixes
to IETF-specific values.
"""

import optparse
import sys

from pyang import plugin
from pyang import statements
from pyang import error
from pyang.error import err_add

def pyang_plugin_init():
    plugin.register_plugin(LintPlugin())

class LintPlugin(plugin.PyangPlugin):
    def __init__(self):
        plugin.PyangPlugin.__init__(self)
        ## Other plugins (e.g., ietf.py) can derive from this plugin
        ## and override these variables.

        # Set this to a list of allowed namespace prefixes.
        # The code checks that the namespace is on the form:
        #   <prefix><modulename>
        # If some other convention is used, the derived plugin can
        # define its own checks.
        self.namespace_prefixes = []

        # Set this to a list of allowed module name prefixes.
        # The code checks that the module name is on the form:
        #   <prefix>-...
        # If some other convention is used, the derived plugin can
        # define its own checks.
        self.modulename_prefixes = []

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--lint",
                                 dest="lint",
                                 action="store_true",
                                 help="Validate the module(s) according to " \
                                 "RFC 6087 rules."),
            optparse.make_option("--lint-namespace-prefix",
                                 dest="lint_namespace_prefixes",
                                 default=[],
                                 action="append",
                                 help="Validate that the module's namespace " \
                                     "matches one of the given prefixes."),
            optparse.make_option("--lint-modulename-prefix",
                                 dest="lint_modulename_prefixes",
                                 default=[],
                                 action="append",
                                 help="Validate that the module's name " \
                                     "matches one of the given prefixes."),
            ]
        optparser.add_options(optlist)

    def setup_ctx(self, ctx):
        if not ctx.opts.lint:
            return
        self._setup_ctx(ctx)

    def _setup_ctx(self, ctx):
        "Should be called by any derived plugin's setup_ctx() function."

        ctx.strict = True
        ctx.canonical = True
        ctx.max_identifier_len = 64
        ctx.implicit_errors = False

        # always add additional prefixes given on the command line
        self.namespace_prefixes.extend(ctx.opts.lint_namespace_prefixes)
        self.modulename_prefixes.extend(ctx.opts.lint_modulename_prefixes)

        # register our grammar validation funs

        statements.add_validation_var(
            '$chk_default',
            lambda keyword: keyword in _keyword_with_default)
        statements.add_validation_var(
            '$chk_required',
            lambda keyword: keyword in _required_substatements)

        statements.add_validation_var(
            '$chk_recommended',
            lambda keyword: keyword in _recommended_substatements)

        statements.add_validation_fun(
            'grammar', ['$chk_default'],
            lambda ctx, s: v_chk_default(ctx, s))
        statements.add_validation_fun(
            'grammar', ['$chk_required'],
            lambda ctx, s: v_chk_required_substmt(ctx, s))
        statements.add_validation_fun(
            'grammar', ['$chk_recommended'],
            lambda ctx, s: v_chk_recommended_substmt(ctx, s))

        statements.add_validation_fun(
            'grammar', ['namespace'],
            lambda ctx, s: v_chk_namespace(ctx, s, self.namespace_prefixes))

        statements.add_validation_fun(
            'grammar', ['module', 'submodule'],
            lambda ctx, s: v_chk_module_name(ctx, s, self.modulename_prefixes))

        statements.add_validation_fun(
            'strict', ['include'],
            lambda ctx, s: v_chk_include(ctx, s))

        statements.add_validation_fun(
            'strict', ['module'],
            lambda ctx, s: v_chk_mandatory_top_level(ctx, s))

        # register our error codes
        error.add_error_code(
            'LINT_EXPLICIT_DEFAULT', 4,
            'RFC 6087: 4.3: '
            + 'statement "%s" is given with its default value "%s"')
        error.add_error_code(
            'LINT_MISSING_REQUIRED_SUBSTMT', 3,
            '%s: '
            + 'statement "%s" must have a "%s" substatement')
        error.add_error_code(
            'LINT_MISSING_RECOMMENDED_SUBSTMT', 4,
            '%s: '
            + 'statement "%s" should have a "%s" substatement')
        error.add_error_code(
            'LINT_BAD_NAMESPACE_VALUE', 4,
            'RFC 6087: 4.8: namespace value should be "%s"')
        error.add_error_code(
            'LINT_BAD_MODULENAME_PREFIX_1', 4,
            'RFC 6087: 4.1: '
            + 'the module name should start with the string %s')
        error.add_error_code(
            'LINT_BAD_MODULENAME_PREFIX_N', 4,
            'RFC 6087: 4.1: '
            + 'the module name should start with one of the strings %s')
        error.add_error_code(
            'LINT_NO_MODULENAME_PREFIX', 4,
            'RFC 6087: 4.1: '
            + 'no module name prefix string used')
        error.add_error_code(
            'LINT_BAD_REVISION', 3,
            'RFC 6087: 4.6: '
            + 'the module\'s revision %s is older than '
            + 'submodule %s\'s revision %s')
        error.add_error_code(
            'LINT_TOP_MANDATORY', 3,
            'RFC 6087: 4.9: '
            + 'top-level node %s must not be mandatory')

        # override std error string
        error.add_error_code(
            'LONG_IDENTIFIER', 3,
            'RFC 6087: 4.2: identifier %s exceeds %s characters')

_keyword_with_default = {
    'status': 'current',
    'mandatory': 'false',
    'min-elements': '0',
    'max-elements': 'unbounded',
    'config': 'true',
    'yin-element': 'false',
    }

_required_substatements = {
    'module': (('contact', 'organization', 'description', 'revision'),
               "RFC 6087: 4.7"),
    'submodule': (('contact', 'organization', 'description', 'revision'),
                  "RFC 6087: 4.7"),
    'revision':(('reference',), "RFC 6087: 4.7"),
    'extension':(('description',), "RFC 6087: 4.12"),
    'feature':(('description',), "RFC 6087: 4.12"),
    'identity':(('description',), "RFC 6087: 4.12"),
    'typedef':(('description',), "RFC 6087: 4.11,4.12"),
    'grouping':(('description',), "RFC 6087: 4.12"),
    'augment':(('description',), "RFC 6087: 4.12"),
    'rpc':(('description',), "RFC 6087: 4.12"),
    'notification':(('description',), "RFC 6087: 4.12,4.14"),
    'container':(('description',), "RFC 6087: 4.12"),
    'leaf':(('description',), "RFC 6087: 4.12"),
    'leaf-list':(('description',), "RFC 6087: 4.12"),
    'list':(('description',), "RFC 6087: 4.12"),
    'choice':(('description',), "RFC 6087: 4.12"),
    'anyxml':(('description',), "RFC 6087: 4.12"),
    }

_recommended_substatements = {
    'enum':(('description',), "RFC 6087: 4.10,4.12"),
    'bit':(('description',), "RFC 6087: 4.10,4.12"),
    }

_ietf_namespace_prefix = 'urn:ietf:params:xml:ns:yang:'

def v_chk_default(ctx, stmt):
    if (stmt.arg == _keyword_with_default[stmt.keyword] and
        stmt.parent.keyword != 'refine'):
        err_add(ctx.errors, stmt.pos, 'LINT_EXPLICIT_DEFAULT',
                (stmt.keyword, stmt.arg))

def v_chk_required_substmt(ctx, stmt):
    if stmt.keyword in _required_substatements:
        (required, s) = _required_substatements[stmt.keyword]
        for r in required:
            if stmt.search_one(r) is None:
                err_add(ctx.errors, stmt.pos,
                        'LINT_MISSING_REQUIRED_SUBSTMT',
                        (s, stmt.keyword, r))

def v_chk_recommended_substmt(ctx, stmt):
    if stmt.keyword in _recommended_substatements:
        (recommended, s) = _recommended_substatements[stmt.keyword]
        for r in recommended:
            if stmt.search_one(r) is None:
                err_add(ctx.errors, stmt.pos,
                        'LINT_MISSING_RECOMMENDED_SUBSTMT',
                        (s, stmt.keyword, r))

def v_chk_namespace(ctx, stmt, namespace_prefixes):
    if namespace_prefixes != []:
        for prefix in namespace_prefixes:
            if stmt.arg == prefix + stmt.i_module.arg:
                return
        err_add(ctx.errors, stmt.pos, 'LINT_BAD_NAMESPACE_VALUE',
                namespace_prefixes[0] + stmt.i_module.arg)

def v_chk_module_name(ctx, stmt, modulename_prefixes):
    if modulename_prefixes != []:
        for prefix in modulename_prefixes:
            if stmt.arg.find(prefix + '-') == 0:
                return
        if len(modulename_prefixes) == 1:
            err_add(ctx.errors, stmt.pos, 'LINT_BAD_MODULENAME_PREFIX_1',
                    '"' + modulename_prefixes[0] + '-"')
        elif len(modulename_prefixes) == 2:
            s = " or ".join(['"' + p + '-"' for p in modulename_prefixes])
            err_add(ctx.errors, stmt.pos, 'LINT_BAD_MODULENAME_PREFIX_N', s)
        else:
            s = ", ".join(['"' + p + '-"' for p in modulename_prefixes[:-1]]) +\
            ', or "' + modulename_prefixes[-1] + '-"'
            err_add(ctx.errors, stmt.pos, 'LINT_BAD_MODULENAME_PREFIX_N', s)
    elif stmt.arg.find('-') == -1:
        # can't check much, but we can check that a prefix is used
        err_add(ctx.errors, stmt.pos, 'LINT_NO_MODULENAME_PREFIX', ())

def v_chk_include(ctx, stmt):
    if stmt.i_orig_module.keyword != 'module':
        # the rule applies only to modules
        return
    latest = stmt.i_orig_module.i_latest_revision
    if latest is None:
        return
    submodulename = stmt.arg
    r = stmt.search_one('revision-date')
    if r is not None:
        rev = r.arg
    else:
        rev = None
    subm = ctx.get_module(submodulename, rev)
    if (subm is not None and
        subm.i_latest_revision is not None and
        subm.i_latest_revision > latest):
        err_add(ctx.errors, stmt.pos, 'LINT_BAD_REVISION',
                (latest, submodulename, subm.i_latest_revision))

def v_chk_mandatory_top_level(ctx, stmt):
    for s in stmt.i_children:
        if statements.is_mandatory_node(s):
            err_add(ctx.errors, s.pos, 'LINT_TOP_MANDATORY', s.arg)
