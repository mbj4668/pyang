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
    def emit(self, ctx, module, writef):
        emit_yang(module, writef)
        
def emit_yang(module, writef):
    emit_stmt(module, writef, '', '  ')
    
def emit_stmt(stmt, writef, indent, indentstep):
    if util.is_prefixed(stmt.keyword):
        (prefix, identifier) = stmt.keyword
        keywd = prefix + ':' + identifier
    else:
        keywd = stmt.keyword
    writef(indent + keywd)
    if stmt.arg != None:
        emit_arg(stmt.arg, writef, indent, indentstep)
    if len(stmt.substmts) == 0:
        writef(';\n')
    else:
        writef(' {\n')
        for s in stmt.substmts:
            emit_stmt(s, writef, indent + indentstep, indentstep)
        writef(indent + '}\n')

def emit_arg(arg, writef, indent, indentstep):
    """Heuristically pretty print the argument string"""
    # current alg. always print a double quoted string
    arg = arg.replace('\\', r'\\')
    arg = arg.replace('"', r'\"')
    arg = arg.replace('\t', r'\t')
    lines = arg.splitlines()
    if len(lines) == 1:
        writef(' "' + arg + '"')
    else:
        writef('\n')
        writef(indent + indentstep + '"' + lines[0] + '\n')
        for line in lines[1:-1]:
            writef(indent + indentstep + ' ' + line + '\n')
        writef(indent + indentstep + ' ' + lines[-1] + '"')
