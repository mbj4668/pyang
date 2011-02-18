"""YANG output plugin"""

import optparse
import re

from pyang import plugin
from pyang import util
from pyang import grammar

def pyang_plugin_init():
    plugin.register_plugin(YANGPlugin())

class YANGPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        fmts['yang'] = self
    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--yang-canonical",
                                 dest="yang_canonical",
                                 action="store_true",
                                 help="Print in canonical order"),
            optparse.make_option("--yang-remove-unused-imports",
                                 dest="yang_remove_unused_imports",
                                 action="store_true"),
            ]
        g = optparser.add_option_group("YANG output specific options")
        g.add_options(optlist)
    def emit(self, ctx, modules, fd):
        module = modules[0]
        emit_yang(ctx, module, fd)
        
def emit_yang(ctx, module, fd):
    emit_stmt(ctx, module, fd, '', '  ')
    
def emit_stmt(ctx, stmt, fd, indent, indentstep):
    if ctx.opts.yang_remove_unused_imports and stmt.keyword == 'import':
        for p in stmt.parent.i_unused_prefixes:
            if stmt.parent.i_unused_prefixes[p] == stmt:
                return
        
    if util.is_prefixed(stmt.raw_keyword):
        (prefix, identifier) = stmt.raw_keyword
        keyword = prefix + ':' + identifier
    else:
        keyword = stmt.keyword
    fd.write(indent + keyword)
    if stmt.arg != None:
        if keyword in grammar.stmt_map:
            (arg_type, _subspec) = grammar.stmt_map[keyword]
            if arg_type in ['identifier', 'identifier-ref', 'boolean']:
                fd.write(' ' + stmt.arg)
            else:
                emit_arg(stmt.arg, fd, indent, indentstep)
        else:
            emit_arg(stmt.arg, fd, indent, indentstep)
    if len(stmt.substmts) == 0:
        fd.write(';\n')
    else:
        fd.write(' {\n')
        if ctx.opts.yang_canonical:
            substmts = grammar.sort_canonical(stmt.keyword, stmt.substmts)
        else:
            substmts = stmt.substmts
        for s in substmts:
            emit_stmt(ctx, s, fd, indent + indentstep, indentstep)
        fd.write(indent + '}\n')

def emit_arg(arg, fd, indent, indentstep):
    """Heuristically pretty print the argument string"""
    # current alg. always print a double quoted string
    arg = arg.replace('\\', r'\\')
    arg = arg.replace('"', r'\"')
    arg = arg.replace('\t', r'\t')
    lines = arg.splitlines()
    if len(lines) <= 1:
        fd.write(' "' + arg + '"')
    else:
        fd.write('\n')
        fd.write(indent + indentstep + '"' + lines[0] + '\n')
        for line in lines[1:-1]:
            fd.write(indent + indentstep + ' ' + line + '\n')
        fd.write(indent + indentstep + ' ' + lines[-1] + '"')

