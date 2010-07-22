"""Tree output plugin

Idea copied from libsmi.
"""

import optparse
import sys
import re

from pyang import plugin
from pyang import statements

def pyang_plugin_init():
    plugin.register_plugin(TreePlugin())

class TreePlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['tree'] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--tree-help",
                                 dest="tree_help",
                                 action="store_true",
                                 help="Print help on tree symbols and exit"),
            ]
        g = optparser.add_option_group("Tree output specific options")
        g.add_options(optlist)

    def setup_ctx(self, ctx):
        if ctx.opts.tree_help:
            print_help()
            sys.exit(0)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        emit_tree(modules, fd)

def print_help():
    print """
Each node is printed as:

<status> <flags> <name> <opts>   <type>

  <status> is one of:
    +  for current
    x  for deprecated
    o  for obsolete

  <flags> is one of:
    rw  for configuration data
    ro  for non-configuration data
    -x  for rpcs
    -n  for notifications

  <name> is the name of the node
    (<name>) means that the node is a choice node
   :(<name>) means that the node is a case node

   If the node is augmented into the tree from another module, its
   name is printed as <prefix>:<name>.

  <opts> is one of:
    ?  for an optional leaf or presence container
    *  for a leaf-list
    [<keys>] for a list's keys

  <type> is the name of the type for leafs and leaf-lists
"""    

def emit_tree(modules, fd):
    for module in modules:
        bstr = ""
        b = module.search_one('belongs-to')
        if b is not None:
            bstr = " (belongs-to %s)" % b.arg
        fd.write("%s: %s%s\n" % (module.keyword, module.arg, bstr))
        chs = [ch for ch in module.i_children
               if ch.keyword in statements.data_definition_keywords]
        print_children(chs, module, fd, ' ')

        rpcs = module.search('rpc')
        if len(rpcs) > 0:
            fd.write("rpcs:\n")
            print_children(rpcs, module, fd, ' ')

        notifs = module.search('notification')
        if len(notifs) > 0:
            fd.write("notifications:\n")
            print_children(notifs, module, fd, ' ')

def print_children(i_children, module, fd, prefix, width=0):
    def get_width(w, chs):
        for ch in i_children:
            if ch.keyword in ['choice', 'case']:
                w = get_width(w, ch.i_children)
            else:
                if ch.i_module == module:
                    nlen = len(ch.arg)
                else:
                    nlen = len(ch.i_module.i_prefix) + 1 + len(ch.arg)
                if nlen > w:
                    w = nlen
        return w
    
    if width == 0:
        width = get_width(0, i_children)

    for ch in i_children:
        if ch == i_children[-1]:
            newprefix = prefix + '   '
        else:
            newprefix = prefix + '  |'
        print_node(ch, module, fd, newprefix, width)

def print_node(s, module, fd, prefix, width):
    fd.write("%s%s--" % (prefix[0:-1], get_status_str(s)))

    if s.i_module == module:
        name = s.arg
    else:
        name = s.i_module.i_prefix + ':' + s.arg
    flags = get_flags_str(s)
    if s.keyword == 'list':
        fd.write(flags + " " + name)
    elif s.keyword == 'container':
        p = s.search_one('presence')
        if p is not None:
            name += '?'
        fd.write(flags + " " + name)
    elif s.keyword  == 'choice':
        m = s.search_one('mandatory')
        if m is None or m.arg == 'false':
            fd.write(flags + ' (' + s.arg + ')')
        else:
            fd.write(flags + ' (' + s.arg + ')?')
    elif s.keyword == 'case':
        fd.write(':(' + s.arg + ')')
    else:
        if s.keyword == 'leaf-list':
            name += '*'
        elif s.keyword == 'leaf':
            m = s.search_one('mandatory')
            if m is None or m.arg == 'false':
                name += '?'
        fd.write("%s %-*s   %s" % (flags, width+1, name, get_typename(s)))

    if s.keyword == 'list' and s.search_one('key') is not None:
        fd.write(" [%s]" % re.sub('\s+', ' ', s.search_one('key').arg))
    fd.write('\n')
    if hasattr(s, 'i_children'):
        if s.keyword in ['choice', 'case']:
            print_children(s.i_children, module, fd, prefix, width)
        else:
            print_children(s.i_children, module, fd, prefix)

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
