"""Tree output plugin

Status: experimental (not ready - needs prettier formatting)

Idea copied from libsmi.
"""

import optparse

from pyang import plugin

def pyang_plugin_init():
    plugin.register_plugin(TreePlugin())

class TreePlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['tree'] = self
    def emit(self, ctx, modules, fd):
        emit_tree(modules, fd)
        
def emit_tree(modules, fd):
    for module in modules:
        fd.write("%s: %s\n" % (module.keyword, module.arg))
        print_children(module, fd, ' ')

def print_children(s, fd, prefix):
    if hasattr(s, 'i_children'):
        typewidth = 0
        for ch in s.i_children:
            typename = get_typename(ch)
            if len(typename) > typewidth:
                typewidth = len(typename)
        for ch in s.i_children:
            if ch == s.i_children[-1]:
                newprefix = prefix + '   '
            else:
                newprefix = prefix + '  |'
            print_node(ch, fd, newprefix, typewidth)

def print_node(s, fd, prefix, typewidth):
    fd.write("%s%s--" % (prefix[0:-1], get_status_str(s)))

    if s.keyword == 'list':
        fd.write(s.arg)
    elif s.keyword == 'container':
        p = s.search_one('presence')
        if p is None or p.arg == 'false':
            fd.write(s.arg)
        else:
            fd.write(s.arg + '?')
    elif s.keyword  == 'choice':
        fd.write('(' + s.arg + ')?')
    elif s.keyword == 'case':
        fd.write(':(' + s.arg + ')')
    else:
        fd.write(" %s %-*s   %s" % (get_flags_str(s), typewidth,
                                    get_typename(s), s.arg))

    if s.keyword == 'list' and s.search_one('key') is not None:
        fd.write(" [%s]" % s.search_one('key').arg)
    fd.write('\n')
    print_children(s, fd, prefix)

def get_status_str(s):
    status = s.search_one('status')
    if status is None or status.arg == 'current':
        return '+'
    elif status.arg == 'deprecated':
        return 'x'
    elif status.arg == 'obsolete':
        return 'o'

def get_flags_str(s):
    if s.keyword == 'rpc':
        return '-x'
    elif s.keyword == 'notification':
        return '-n'    
    elif s.i_config == True:
        return 'rw'
    else:
        return 'ro'

def get_typename(s):
    t = s.search_one('type')
    if t is not None:
        return t.arg
    else:
        return ''
