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
    def __init__(self):
        plugin.PyangPlugin.__init__(self, 'tree')

    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['tree'] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--tree-help",
                                 dest="tree_help",
                                 action="store_true",
                                 help="Print help on tree symbols and exit"),
            optparse.make_option("--tree-depth",
                                 type="int",
                                 dest="tree_depth",
                                 help="Number of levels to print"),
            optparse.make_option("--tree-line-length",
                                 type="int",
                                 dest="tree_line_length",
                                 help="Maximum line length"),
            optparse.make_option("--tree-path",
                                 dest="tree_path",
                                 help="Subtree to print"),
            optparse.make_option("--tree-print-groupings",
                                 dest="tree_print_groupings",
                                 action="store_true",
                                 help="Print groupings"),
            ]
        if plugin.is_plugin_registered('restconf'):
            optlist.append(
                optparse.make_option("--tree-print-yang-data",
                                     dest="tree_print_yang_data",
                                     action="store_true",
                                     help="Print ietf-restconf:yang-data " +
                                     "structures")
            )
        g = optparser.add_option_group("Tree output specific options")
        g.add_options(optlist)

    def setup_ctx(self, ctx):
        if ctx.opts.tree_help:
            print_help()
            sys.exit(0)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        if ctx.opts.tree_path is not None:
            path = ctx.opts.tree_path.split('/')
            if path[0] == '':
                path = path[1:]
        else:
            path = None
        emit_tree(ctx, modules, fd, ctx.opts.tree_depth,
                  ctx.opts.tree_line_length, path)

def print_help():
    print("""
Each node is printed as:

<status> <flags> <name> <opts> <type> <if-features>

  <status> is one of:
    +  for current
    x  for deprecated
    o  for obsolete

  <flags> is one of:
    rw  for configuration data
    ro  for non-configuration data
    -x  for rpcs and actions
    -n  for notifications

  <name> is the name of the node
    (<name>) means that the node is a choice node
   :(<name>) means that the node is a case node

   If the node is augmented into the tree from another module, its
   name is printed as <prefix>:<name>.

  <opts> is one of:
    ?  for an optional leaf, choice, anydata or anyxml
    !  for a presence container
    *  for a leaf-list or list
    [<keys>] for a list's keys

    <type> is the name of the type for leafs and leaf-lists, or
           "<anydata>" or "<anyxml>" for anydata and anyxml, respectively

    If the type is a leafref, the type is printed as "-> TARGET", where
    TARGET is the leafref path, with prefix removed if possible.

  <if-features> is the list of features this node depends on, printed
    within curly brackets and a question mark "{...}?"
""")

def emit_tree(ctx, modules, fd, depth, llen, path):
    for module in modules:
        printed_header = False

        def print_header():
            bstr = ""
            b = module.search_one('belongs-to')
            if b is not None:
                bstr = " (belongs-to %s)" % b.arg
            fd.write("%s: %s%s\n" % (module.keyword, module.arg, bstr))
            printed_header = True

        chs = [ch for ch in module.i_children
               if ch.keyword in statements.data_definition_keywords]
        if path is not None and len(path) > 0:
            chs = [ch for ch in chs if ch.arg == path[0]]
            path = path[1:]

        if len(chs) > 0:
            if not printed_header:
                print_header()
                printed_header = True
            print_children(chs, module, fd, '  ', path, 'data', depth, llen)

        mods = [module]
        for i in module.search('include'):
            subm = ctx.get_module(i.arg)
            if subm is not None:
                mods.append(subm)
        for m in mods:
            for augment in m.search('augment'):
                if (hasattr(augment.i_target_node, 'i_module') and
                    augment.i_target_node.i_module not in modules + mods):
                    # this augment has not been printed; print it
                    if not printed_header:
                        print_header()
                        printed_header = True
                    fd.write("  augment %s:\n" % augment.arg)
                    print_children(augment.i_children, m, fd,
                                   '  ', path, 'augment', depth, llen)

        rpcs = [ch for ch in module.i_children
                if ch.keyword == 'rpc']
        if path is not None:
            if len(path) > 0:
                rpcs = [rpc for rpc in rpcs if rpc.arg == path[0]]
                path = path[1:]
            else:
                rpcs = []
        if len(rpcs) > 0:
            if not printed_header:
                print_header()
                printed_header = True
            fd.write("\n  rpcs:\n")
            print_children(rpcs, module, fd, '  ', path, 'rpc', depth, llen)

        notifs = [ch for ch in module.i_children
                  if ch.keyword == 'notification']
        if path is not None:
            if len(path) > 0:
                notifs = [n for n in notifs if n.arg == path[0]]
                path = path[1:]
            else:
                notifs = []
        if len(notifs) > 0:
            if not printed_header:
                print_header()
                printed_header = True
            fd.write("\n  notifications:\n")
            print_children(notifs, module, fd, '  ', path,
                           'notification', depth, llen)

        if ctx.opts.tree_print_groupings and len(module.i_groupings) > 0:
            if not printed_header:
                print_header()
                printed_header = True
            fd.write("  groupings:\n")
            for gname in module.i_groupings:
                fd.write('  ' + gname + '\n')
                g = module.i_groupings[gname]
                print_children(g.i_children, module, fd, '    ', path,
                               'grouping', depth, llen)
                fd.write('\n')

        if ctx.opts.tree_print_yang_data:
            yds = module.search(('ietf-restconf', 'yang-data'))
            if len(yds) > 0:
                if not printed_header:
                    print_header()
                    printed_header = True
                fd.write("  yang-data:\n")
                for yd in yds:
                    fd.write('  ' + yd.arg + '\n')
                    print_children(yd.i_children, module, fd, '    ', path,
                                   'yang-data', depth, llen)
                    fd.write('\n')


def print_children(i_children, module, fd, prefix, path, mode, depth,
                   llen, width=0):
    if depth == 0:
        if i_children: fd.write(prefix + '     ...\n')
        return
    def get_width(w, chs):
        for ch in chs:
            if ch.keyword in ['choice', 'case']:
                w = get_width(w, ch.i_children)
            else:
                if ch.i_module.i_modulename == module.i_modulename:
                    nlen = len(ch.arg)
                else:
                    nlen = len(ch.i_module.i_prefix) + 1 + len(ch.arg)
                if nlen > w:
                    w = nlen
        return w

    if width == 0:
        width = get_width(0, i_children)

    for ch in i_children:
        if ((ch.keyword == 'input' or ch.keyword == 'output') and
            len(ch.i_children) == 0):
            pass
        else:
            if (ch == i_children[-1] or
                (i_children[-1].keyword == 'output' and
                 len(i_children[-1].i_children) == 0)):
                # the last test is to detect if we print input, and the
                # next node is an empty output node; then don't add the |
                newprefix = prefix + '   '
            else:
                newprefix = prefix + '  |'
            if ch.keyword == 'input':
                mode = 'input'
            elif ch.keyword == 'output':
                mode = 'output'
            print_node(ch, module, fd, newprefix, path, mode, depth, llen,
                       width)

def print_node(s, module, fd, prefix, path, mode, depth, llen, width):
    line = "%s%s--" % (prefix[0:-1], get_status_str(s))

    brcol = len(line) + 4

    if s.i_module.i_modulename == module.i_modulename:
        name = s.arg
    else:
        name = s.i_module.i_prefix + ':' + s.arg
    flags = get_flags_str(s, mode)
    if s.keyword == 'list':
        name += '*'
        line += flags + " " + name
    elif s.keyword == 'container':
        p = s.search_one('presence')
        if p is not None:
            name += '!'
        line += flags + " " + name
    elif s.keyword  == 'choice':
        m = s.search_one('mandatory')
        if m is None or m.arg == 'false':
            line += flags + ' (' + name + ')?'
        else:
            line += flags + ' (' + name + ')'
    elif s.keyword == 'case':
        line += ':(' + name + ')'
        brcol += 1
    else:
        if s.keyword == 'leaf-list':
            name += '*'
        elif (s.keyword == 'leaf' and not hasattr(s, 'i_is_key')
              or s.keyword == 'anydata' or s.keyword == 'anyxml'):
            m = s.search_one('mandatory')
            if m is None or m.arg == 'false':
                name += '?'
        t = get_typename(s)
        if t == '':
            line += "%s %s" % (flags, name)
        elif (llen is not None and
              len(line) + len(flags) + width+1 + len(t) > llen):
            # there's no room for the type name
            if (get_leafref_path(s) is not None and
                len(t) + brcol > llen):
                # it's not even room for the leafref path; skip it
                line += "%s %-*s   leafref" % (flags, width+1, name)
            else:
                line += "%s %s" % (flags, name)
                fd.write(line + '\n')
                line = prefix + ' ' * (brcol - len(prefix)) + ' ' + t
        else:
            line += "%s %-*s   %s" % (flags, width+1, name, t)

    if s.keyword == 'list' and s.search_one('key') is not None:
        keystr = " [%s]" % re.sub('\s+', ' ', s.search_one('key').arg)
        if (llen is not None and
            len(line) + len(keystr) > llen):
            fd.write(line + '\n')
            line = prefix + ' ' * (brcol - len(prefix))
        line += keystr

    features = s.search('if-feature')
    featurenames = [f.arg for f in features]
    if hasattr(s, 'i_augment'):
        afeatures = s.i_augment.search('if-feature')
        featurenames.extend([f.arg for f in afeatures
                             if f.arg not in featurenames])

    if len(featurenames) > 0:
        fstr = " {%s}?" % ",".join(featurenames)
        if (llen is not None and len(line) + len(fstr) > llen):
            fd.write(line + '\n')
            line = prefix + ' ' * (brcol - len(prefix))
        line += fstr

    fd.write(line + '\n')
    if hasattr(s, 'i_children'):
        if depth is not None:
            depth = depth - 1
        chs = s.i_children
        if path is not None and len(path) > 0:
            chs = [ch for ch in chs
                   if ch.arg == path[0]]
            path = path[1:]
        if s.keyword in ['choice', 'case']:
            print_children(chs, module, fd, prefix, path, mode, depth,
                           llen, width)
        else:
            print_children(chs, module, fd, prefix, path, mode, depth, llen)

def get_status_str(s):
    status = s.search_one('status')
    if status is None or status.arg == 'current':
        return '+'
    elif status.arg == 'deprecated':
        return 'x'
    elif status.arg == 'obsolete':
        return 'o'

def get_flags_str(s, mode):
    if mode == 'input':
        return "-w"
    elif s.keyword in ('rpc', 'action', ('tailf-common', 'action')):
        return '-x'
    elif s.keyword == 'notification':
        return '-n'
    elif s.i_config == True:
        return 'rw'
    elif s.i_config == False or mode == 'output' or mode == 'notification':
        return 'ro'
    else:
        return '--'

def get_leafref_path(s):
    t = s.search_one('type')
    if t is not None:
        if t.arg == 'leafref':
            return t.search_one('path')
    else:
        return None

def get_typename(s):
    t = s.search_one('type')
    if t is not None:
        if t.arg == 'leafref':
            p = t.search_one('path')
            if p is not None:
                # Try to make the path as compact as possible.
                # Remove local prefixes, and only use prefix when
                # there is a module change in the path.
                target = []
                curprefix = s.i_module.i_prefix
                for name in p.arg.split('/'):
                    if name.find(":") == -1:
                        prefix = curprefix
                    else:
                        [prefix, name] = name.split(':', 1)
                    if prefix == curprefix:
                        target.append(name)
                    else:
                        target.append(prefix + ':' + name)
                        curprefix = prefix
                return "-> %s" % "/".join(target)
            else:
                return t.arg
        else:
            return t.arg
    elif s.keyword == 'anydata':
        return '<anydata>'
    elif s.keyword == 'anyxml':
        return '<anyxml>'
    else:
        return ''
