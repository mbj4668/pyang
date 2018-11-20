"""YANG output plugin"""

import optparse

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
            optparse.make_option("--yang-line-length",
                                 type="int",
                                 dest="yang_line_length",
                                 help="Maximum line length"),
            ]
        g = optparser.add_option_group("YANG output specific options")
        g.add_options(optlist)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        module = modules[0]
        emit_yang(ctx, module, fd)

def emit_yang(ctx, module, fd):
    emit_stmt(ctx, module, fd, 0, None, '', '  ')

# always add newline between keyword and argument
_force_newline_arg = ('description', 'contact', 'organization')

# do not quote these arguments
_non_quote_arg_type = ('identifier', 'identifier-ref', 'boolean', 'integer',
                       'non-negative-integer', 'max-value',
                       'date', 'ordered-by-arg',
                       'fraction-digits-arg', 'deviate-arg', 'version',
                       'status-arg')

_maybe_quote_arg_type = ('enum-arg', )

# add extra blank line after these, when they occur on the top level
_keyword_with_trailing_blank_line_toplevel = (
    'description',
    'identity',
    'feature',
    'extension',
    'rpc',
    )

# always add extra blank line after these
_keyword_with_trailing_blank_line = (
    'typedef',
    'grouping',
    'notification',
    'action',
    )

# use single quote for the arguments to these keywords (if possible)
_keyword_prefer_squote_arg = (
    'must',
    'when',
    'pattern',
    'augment',
    'path',
)

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

_need_quote = (
    " ", "}", "{", ";", '"', "'",
    "\n", "\t", "\r", "//", "/*", "*/",
    )

def emit_stmt(ctx, stmt, fd, level, prev_kwd_class, indent, indentstep):
    if ctx.opts.yang_remove_unused_imports and stmt.keyword == 'import':
        for p in stmt.parent.i_unused_prefixes:
            if stmt.parent.i_unused_prefixes[p] == stmt:
                return

    if util.is_prefixed(stmt.raw_keyword):
        (prefix, identifier) = stmt.raw_keyword
        keywordstr = prefix + ':' + identifier
    else:
        keywordstr = stmt.keyword

    kwd_class = get_kwd_class(stmt.keyword)
    if ((level == 1 and
         kwd_class != prev_kwd_class and kwd_class != 'extension') or
        (level == 1 and stmt.keyword in
         _keyword_with_trailing_blank_line_toplevel) or
        stmt.keyword in _keyword_with_trailing_blank_line):
        fd.write('\n')

    if stmt.keyword == '_comment':
        emit_comment(stmt.arg, fd, indent)
        return

    fd.write(indent + keywordstr)
    if stmt.arg is not None:
        forcenlarg = _force_newline_arg
        if '\n' in stmt.arg:
            emit_arg(stmt, fd, indent, indentstep, forcenlarg)
        elif stmt.keyword in _keyword_prefer_squote_arg:
            # FIXME: separate line break alg from single quote preference
            emit_arg_squote(stmt.keyword, stmt.arg, fd, indent,
                            ctx.opts.yang_line_length)
        elif stmt.keyword in grammar.stmt_map:
            (arg_type, _subspec) = grammar.stmt_map[stmt.keyword]
            if arg_type in _non_quote_arg_type:
                fd.write(' ' + stmt.arg)
            elif (arg_type in _maybe_quote_arg_type and
                  not need_quote(stmt.arg)):
                fd.write(' ' + stmt.arg)
            else:
                emit_arg(stmt, fd, indent, indentstep, forcenlarg)
        else:
            emit_arg(stmt, fd, indent, indentstep, forcenlarg)
    if len(stmt.substmts) == 0:
        fd.write(';\n')
    else:
        fd.write(' {\n')
        if ctx.opts.yang_canonical:
            substmts = grammar.sort_canonical(stmt.keyword, stmt.substmts)
        else:
            substmts = stmt.substmts
        if level == 0:
            kwd_class = 'header'
        for s in substmts:
            emit_stmt(ctx, s, fd, level + 1, kwd_class,
                      indent + indentstep, indentstep)
            kwd_class = get_kwd_class(s.keyword)
        fd.write(indent + '}\n')


def emit_arg_squote(keyword, arg, fd, indent, max_line_len):
    """Heuristically pretty print the argument with smart quotes"""

    # use single quotes unless the arg contains a single quote
    quote = "'" if arg.find("'") == -1 else '"'

    # if using double quotes, replace special characters
    if quote == '"':
        arg = arg.replace('\\', r'\\')
        arg = arg.replace('"', r'\"')
        arg = arg.replace('\t', r'\t')

    # allow for " {" even though the statement might not have sub-statements
    term = " {"

    line_len = len(
        "%s%s %s%s%s%s" % (indent, keyword, quote, arg, quote, term))
    if max_line_len is None or line_len <= max_line_len:
        fd.write(" " + quote + arg + quote)
        return

    # strictly num_chars could be negative, e.g. if max_line_len is VERY
    # small; should check for this
    num_chars = len(arg) - (line_len - max_line_len)
    while num_chars > 2 and arg[num_chars - 1:num_chars].isalnum():
        num_chars -= 1
    fd.write(" " + quote + arg[:num_chars] + quote)
    arg = arg[num_chars:]
    while arg != '':
        keyword_cont = ((len(keyword) - 1) * ' ') + '+'
        line_len = len(
            "%s%s %s%s%s%s" % (indent, keyword_cont, quote, arg, quote, term))
        num_chars = len(arg) - (line_len - max_line_len)
        while num_chars > 2 and arg[num_chars - 1:num_chars].isalnum():
            num_chars -= 1
        fd.write('\n' + indent + keyword_cont + " " +
                 quote + arg[:num_chars] + quote)
        arg = arg[num_chars:]

def emit_arg(stmt, fd, indent, indentstep, forcenlarg):
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
        if stmt.keyword in forcenlarg:
            fd.write('\n' + indent + indentstep + '"' + arg + '"')
        else:
            fd.write(' "' + arg + '"')
    else:
        fd.write('\n')
        fd.write(indent + indentstep + '"' + lines[0])
        for line in lines[1:-1]:
            if line[0] == '\n':
                fd.write('\n')
            else:
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
    fd.write('\n')

def need_quote(arg):
    for ch in _need_quote:
        if arg.find(ch) != -1:
            return True
    return False
