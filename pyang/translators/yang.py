"""YANG output plugin"""

import optparse
import re

from pyang import plugin
from pyang import util

def pyang_plugin_init():
    plugin.register_plugin(YANGPlugin())

class YANGPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        fmts['yang'] = self
    def emit(self, ctx, module, fd):
        emit_yang(module, fd)
        
def emit_yang(module, fd):
    emit_stmt(module, fd, '', '  ')
    
def emit_stmt(stmt, fd, indent, indentstep):
    if util.is_prefixed(stmt.keyword):
        (prefix, identifier) = stmt.keyword
        keywd = prefix + ':' + identifier
    else:
        keywd = stmt.keyword
    fd.write(indent + keywd)
    if stmt.arg != None:
        emit_arg(stmt.arg, fd, indent, indentstep)
    if len(stmt.substmts) == 0:
        fd.write(';\n')
    else:
        fd.write(' {\n')
        for s in stmt.substmts:
            emit_stmt(s, fd, indent + indentstep, indentstep)
        fd.write(indent + '}\n')

def emit_arg(arg, fd, indent, indentstep):
    """Heuristically pretty print the argument string"""
    # current alg. always print a double quoted string
    arg = arg.replace('\\', r'\\')
    arg = arg.replace('"', r'\"')
    arg = arg.replace('\t', r'\t')
    lines = arg.splitlines()
    if len(lines) == 1:
        fd.write(' "' + arg + '"')
    else:
        fd.write('\n')
        fd.write(indent + indentstep + '"' + lines[0] + '\n')
        for line in lines[1:-1]:
            fd.write(indent + indentstep + ' ' + line + '\n')
        fd.write(indent + indentstep + ' ' + lines[-1] + '"')
