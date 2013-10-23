
import optparse
import sys
import re
import string

from pyang import plugin
from pyang import statements

def pyang_plugin_init():
    plugin.register_plugin(HyperTreePlugin())

class HyperTreePlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['hypertree'] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--hypertree-help",
                                 dest="ht_tree_help",
                                 action="store_true",
                                 help="Print help on hypertree usage and exit"),
            optparse.make_option("--hypertree-path",
                                 dest="ht_tree_path",
                                 help="Subtree to print"),
            ]
        g = optparser.add_option_group("Hypertree output specific options")
        g.add_options(optlist)

    def setup_ctx(self, ctx):
        if ctx.opts.ht_tree_help:
            print_help()
            sys.exit(0)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        if ctx.opts.ht_tree_path is not None:
            path = string.split(ctx.opts.tree_path, '/')
            if path[0] == '':
                path = path[1:]
        else:
            path = None
        emit_tree(modules, fd, path)

def print_help():
    print("""
Prints an XML file that can be loaded to
http://treebolic.sourceforge.net/

Colors:
* Light green node background : config = True
* Light yellow node background : config = False
* Red node foreground : mandatory = True
* White leaf node background : index
* Orange foreground : presence container

For example in order to use the applet version embed the following
into a web page:

<applet code="treebolic.applet.Treebolic.class"
        archive="TreebolicAppletDom.jar"
        id="Treebolic" width="100%" height="100%">
  <param name="doc" value="ietf-netconf-monitoring.xml">
</applet>

The browser references an images folder which is installed at
share/yang/images in the pyang installation folder.
Copy or link to that folder.
""")


keyword2icon = {'container':'container.png',
                'list':'list.png',
                'leaf':'leaf.png',
                'leaflist':'leaf-list.png',
                'leafref':'leafref.png',
                'choice':'choice.png',
                'case':'case.png',
                'module':'module.png',
                'rpc':'hammer.png',
                'action':'hammer.png',
                'notificattion':'notification.png'}
keyword2color = {'container':'container.png',
                 'leaf':'leaf.png',
                 'leaflist':'leaf-list.png',
                 'leafref':'leafref.png',
                 'choice':'choice.png',
                 'case':'case.png',
                 'module':'module.png'}
fgcolors = {'index':'00cc00',     # green
            'mandatory':'ff0000', # red
            'presence':'f79d5f',  # orange
            }
bgcolors = {'config':'e1f4b2',    # lightgreen
            'noconfig':'fafbb7',  # lightyellow
            }
leafrefs = []

def emit_tree(modules, fd, path):
    fd.write("<treebolic  focus=\"ROOT\" focus-on-hover=\"false\" popupmenu=\"true\" statusbar=\"true\" toolbar=\"true\" tooltip=\"true\" xmoveto=\"0.0\" ymoveto=\"0.0\">\n")
    fd.write("<tree  backcolor=\"f8f8ff\" expansion=\"0.9\" fontface=\"Arial\" fontsize=\"22\" fontsizestep=\"2\" forecolor=\"000000\" orientation=\"radial\" preserve-orientation=\"true\" sweep=\"1.1\">\n")
    fd.write("<nodes backcolor=\"ffffff\" forecolor=\"000080\">\n")
    fd.write("<node id=\"ROOT\">\n")
    fd.write("<label> YANG Modules </label>")
    for module in modules:

        # module
        fd.write("<node id = \"%s\">\n" %fullpath(module))
        fd.write("<label> %s </label>\n" %module.arg)
        fd.write("<img src=\"%s\"/>\n" %keyword2icon['module'])


        chs = [ch for ch in module.i_children
               if ch.keyword in statements.data_definition_keywords]
        if path is not None and len(path) > 0:
            chs = [ch for ch in chs
                   if ch.arg == path[0]]
            path = path[1:]

        print_children(chs, module, fd, path)
        fd.write("</node>\n")

    fd.write("</node>\n")
    fd.write("</nodes>\n")

    fd.write("<edges hyperbolic=\"true\">")
    print_edges(fd)
    fd.write("</edges>")

    fd.write("</tree>\n")
    fd.write("<tools>\n")
    fd.write("<menu>\n")
    fd.write("<menuitem action=\"focus\" match-mode=\"includes\" match-scope=\"id\">\n")
    fd.write("<label>Focus</label>\n")
    fd.write("</menuitem>\n")
    fd.write("<menuitem action=\"search\" match-mode=\"includes\" match-scope=\"label\" match-target=\"%e\">\n")
    fd.write("<label>Search (name includes %e)</label>\n")
    fd.write("</menuitem>\n")
    fd.write("<menuitem action=\"search\" match-mode=\"equals\" match-scope=\"id\" match-target=\"%e\">\n")
    fd.write("<label>Search (id equals %e)</label>\n")
    fd.write("</menuitem>\n")
    fd.write("<menuitem action=\"search\" match-mode=\"includes\" match-scope=\"content\" match-target=\"%e\">\n")
    fd.write("<label>Search (content includes %e)</label>\n")
    fd.write("</menuitem>\n")
    for module in modules:
        fd.write("<menuitem action=\"goto\" match-mode=\"includes\" match-scope=\"id\">\n")
        fd.write("<label>Go to %s</label>\n" %module.arg)
        fd.write("<a href=\"%s\"/>\n" %module.arg)
        fd.write("</menuitem>\n")
    fd.write("</menu>\n")
    fd.write("</tools>\n")
    fd.write("</treebolic>\n")

def print_children(i_children, module, fd, path):
    for ch in i_children:
        print_node(ch, module, fd, path)

def print_node(s, module, fd, path):
    name = s.arg
    colorstring = ""
    bgcolorstring ="backcolor=\"" + bgcolors['noconfig'] + "\""
    if s.i_config == True:
        bgcolorstring = "backcolor=\"" + bgcolors['config'] + "\""

    if s.keyword == 'leaf' and hasattr(s, 'i_is_key'):
        fd.write("<node id=\"%s\" forecolor=\"%s\">\n" %(fullpath(s), fgcolors['index']))
    else:
        m = s.search_one('mandatory')
        if m is not None and m.arg == 'true':
            colorstring = "forecolor=\"" + fgcolors['mandatory'] + "\""
        elif s.keyword == "container":
            p = s.search_one('presence')
            if p is not None:
                colorstring = "forecolor=\"" + fgcolors['presence'] + "\""

        fd.write("<node id=\"%s\" %s %s>\n" %(fullpath(s), colorstring, bgcolorstring))

    fd.write("<label> %s </label>\n" %name)
    if s.keyword == ('tailf-common', 'action'):
        kw = 'action'
    else:
        kw = s.keyword
    if kw in keyword2icon:
        fd.write("<img src=\"%s\"/>\n" %keyword2icon[kw])

    descr = s.search_one("description")
    if descr is not None:
        content = descr.arg
    else:
        content = "";
    fd.write(" <content><![CDATA[%s \n Type : %s]]></content>\n" %(content, get_typename(s)))

    if  hasattr(s, 'i_leafref_ptr') and s.i_leafref_ptr is not None:
        n = s.i_leafref_ptr[0]

        leafrefs.append("<edge from=\"" + fullpath(s) + "\" " + " to=\"" + fullpath(n) + "\" toterminator=\"df\" stroke=\"dash\" color=\"a9a9a9\">" + "\n<label>" + s.arg + "</label>\n" + " </edge>\n" )
    if hasattr(s, 'i_children'):
        chs = s.i_children
        if path is not None and len(path) > 0:
            chs = [ch for ch in chs
                   if ch.arg == path[0]]
            path = path[1:]
        if s.keyword in ['choice', 'case']:
            print_children(chs, module, fd, path)
        else:
            print_children(chs, module, fd, path)

    fd.write("</node>\n")


def print_edges(fd):
    for e in leafrefs:
        fd.write(e)

def get_status_str(s):
    status = s.search_one('status')
    if status is None or status.arg == 'current':
        return '+'
    elif status.arg == 'deprecated':
        return 'x'
    elif status.arg == 'obsolete':
        return 'o'

def get_flags_str(s):
    if s.keyword == 'rpc' or s.keyword == ('tailf-common', 'action'):
        return '-x'
    elif s.keyword == 'notification':
        return '-n'
    elif hasattr(s, 'i_tree_flags_str'):
        return s.i_tree_flags_str
    elif s.i_config == True:
        return 'rw'
    else:
        return 'ro'

def get_typename(s):
    t = s.search_one('type')
    if t is not None:
      s = t.arg
      if t.arg == 'enumeration':
        s = s + ' : {'
        for enums in t.substmts[:10]:
            s = s + enums.arg + ','
        if len(t.substmts) > 3:
            s = s + "..."
        s = s + '}'
      elif t.arg == 'leafref':
        s = s + ' : '
        p = t.search_one('path')
        if p is not None:
            s = s + p.arg
      return s

def fullpath(stmt):
        pathsep = "_I_"
        path = stmt.arg
        # for augment paths we need to remove initial /
        if path.find("/") == 0:
            path = path[1:len(path)]
        else:
            if stmt.keyword == 'case':
                path = path + '-case'
            elif stmt.keyword == 'grouping':
                path = path + '-grouping'

            while stmt.parent is not None:
                stmt = stmt.parent
                if stmt.arg is not None:
                    path = stmt.arg + pathsep + path
        return path
