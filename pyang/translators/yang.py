"""YANG output plugin"""

import optparse
import re

from .. import plugin
from .. import util
from .. import grammar

def pyang_plugin_init():
    plugin.register_plugin(YANGPlugin())

class YANGPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        fmts['yang'] = self
        self.handle_comments = True

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--yang-canonical",
                                 dest="yang_canonical",
                                 action="store_true",
                                 help="Print in canonical order"),
            optparse.make_option("--yang-remove-unused-imports",
                                 dest="yang_remove_unused_imports",
                                 action="store_true"),
            optparse.make_option("--yang-keep-blank-lines",
                                 dest="yang_keep_blank_lines",
                                 action="store_true",
                                 help="Keep blank lines and trailing comments")
            ]
        g = optparser.add_option_group("YANG output specific options")
        g.add_options(optlist)

    def emit(self, ctx, modules, fd):
        module = modules[0]
        emit_yang(ctx, module, fd)

def emit_yang(ctx, module, fd):
    stmts = module.real_parent.substmts if module.real_parent else [module]
    for (i, stmt) in enumerate(stmts):
        next_stmt = stmts[i+1] if (i < len(stmts) - 1) else None
        emit_stmt(ctx, stmt, fd, 0, None, next_stmt, False, '', '  ')

_force_newline_arg = ('description', 'contact', 'organization')
_non_quote_arg_type = ('identifier', 'identifier-ref', 'boolean', 'integer',
                       'non-negative-integer', 'date', 'ordered-by-arg',
                       'fraction-digits-arg', 'deviate-arg', 'version',
                       'status-arg')

_kwd_class = {
    'yang-version': 'header',
    'namespace': 'header',
    'prefix': 'header',
    'belongs-to': 'header',
    'organization': 'meta',
    'contact': 'meta',
    'description': 'meta',
    'reference': 'meta',
    'import': 'linkage',
    'include': 'linkage',
    'revision': 'revision',
    'typedef': 'defs',
    'grouping': 'defs',
    'identity': 'defs',
    'feature': 'defs',
    'extension': 'defs',
    '_comment': 'comment',
    'module': None,
    'submodule': None,
}
def get_kwd_class(keyword):
    if util.is_prefixed(keyword):
        return 'extension'
    else:
        try:
            return _kwd_class[keyword]
        except KeyError:
            return 'body'

_keyword_with_trailing_newline = (
    'typedef',
    'grouping',
    'identity',
    'feature',
    'extension',
    )

def emit_stmt(ctx, stmt, fd, level, prev_kwd_class, next_stmt,
              no_indent, indent, indentstep):
    if ctx.opts.yang_remove_unused_imports and stmt.keyword == 'import':
        for p in stmt.parent.i_unused_prefixes:
            if stmt.parent.i_unused_prefixes[p] == stmt:
                return

    if util.is_prefixed(stmt.raw_keyword):
        (prefix, identifier) = stmt.raw_keyword
        keyword = prefix + ':' + identifier
    else:
        keyword = stmt.keyword

    kwd_class = get_kwd_class(stmt.keyword)
    if ((level == 1 and not ctx.opts.yang_keep_blank_lines and
         kwd_class != prev_kwd_class and kwd_class != 'extension') or
        stmt.keyword in _keyword_with_trailing_newline):
        fd.write('\n')

    newlines_after = get_newlines_after(stmt, next_stmt) \
                     if ctx.opts.yang_keep_blank_lines else 1
    stmt_term = newlines_after * '\n' if newlines_after > 0 else ' '

    if keyword == '_comment':
        emit_comment(stmt.arg, fd, '' if no_indent else indent)
        fd.write(stmt_term)
        return

    fd.write(indent + keyword)
    if stmt.arg != None:
        if keyword in grammar.stmt_map:
            (arg_type, _subspec) = grammar.stmt_map[keyword]
            if arg_type in _non_quote_arg_type:
                fd.write(' ' + stmt.arg)
            else:
                emit_arg(stmt, fd, indent, indentstep)
        else:
            emit_arg(stmt, fd, indent, indentstep)

    # XXX see statements.py
    substmts = [s for s in stmt.substmts
                if not hasattr(s, "_ignored_by_output_format_")]
    
    if len(substmts) == 0:
        fd.write(';' + stmt_term)
    else:
        fd.write(' {\n')
        if ctx.opts.yang_canonical:
            substmts = grammar.sort_canonical(stmt.keyword, substmts)
        #else:
        #    substmts = stmt.substmts
        if level == 0:
            kwd_class = 'header'
        for (i, s) in enumerate(substmts):
            n = substmts[i+1] if (i < len(substmts) - 1) else None
            no_indent = emit_stmt(ctx, s, fd, level + 1, kwd_class, n,
                                  no_indent, indent + indentstep, indentstep)
            kwd_class = get_kwd_class(s.keyword)
        fd.write(indent + '}' + stmt_term)
    return (newlines_after == 0)

def emit_arg(stmt, fd, indent, indentstep):
    """Heuristically pretty print the argument string"""
    # current alg. always print a double quoted string
    arg = stmt.arg
    arg = arg.replace('\\', r'\\')
    arg = arg.replace('"', r'\"')
    arg = arg.replace('\t', r'\t')
    lines = arg.splitlines(True)
    if len(lines) <= 1:
        if len(arg) > 0 and arg[-1] == '\n':
            arg = arg[:-1] + r'\n'
        if stmt.keyword in _force_newline_arg:
            fd.write('\n' + indent + indentstep + '"' + arg + '"')
        else:
            fd.write(' "' + arg + '"')
    else:
        fd.write('\n')
        fd.write(indent + indentstep + '"' + lines[0])
        for line in lines[1:-1]:
            fd.write(indent + indentstep + ' ' + line)
        # write last line
        fd.write(indent + indentstep + ' ' + lines[-1])
        if lines[-1][-1] == '\n':
            # last line ends with a newline, indent the ending quote
            fd.write(indent + indentstep + '"')
        else:
            fd.write('"')

def emit_comment(comment, fd, indent):
    lines = comment.splitlines(True)
    for x in lines:
        if x[0] == '*':
            fd.write(indent + ' ' + x)
        else:
            fd.write(indent + x)

def get_newlines_after(this_stmt, next_stmt):
    newlines_after = 1
    if this_stmt.pos_end and next_stmt and next_stmt.pos_begin:
        this_stmt_end_line = this_stmt.pos_end.line
        next_stmt_begin_line = next_stmt.pos_begin.line
        newlines_after = next_stmt_begin_line - this_stmt_end_line
    return newlines_after

# FIXME: tmp debug
def pos_range(stmt):
    s = "[%s" % stmt.pos_begin
    if stmt.pos.line > stmt.pos_begin.line:
        s += "-%d" % stmt.pos.line
    if stmt.pos_end.line > stmt.pos.line:
        s += "->%d" % stmt.pos_end.line
    s += "]"
    return s
