"""JS-Tree output plugin
Generates a html/javascript page that presents a tree-navigator
to the YANG module(s). Assumes that an images folder exists
relative to the html file.
The images folder is installed at share/yang/images in the pyang installation folder.
Copy or link to that folder.
"""

import optparse
import sys

from pyang import plugin
from pyang import statements


def pyang_plugin_init():
    plugin.register_plugin(JSTreePlugin())

class JSTreePlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['jstree'] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--jstree-help",
                                 dest="jstree_help",
                                 action="store_true",
                                 help="Print help on JavaScript tree usage and exit"),
            ]
        g = optparser.add_option_group("JSTree output specific options")
        g.add_options(optlist)

    def setup_ctx(self, ctx):
        if ctx.opts.jstree_help:
            print_help()
            sys.exit(0)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        emit_header(modules, fd)
        emit_css(fd)
        emit_js(fd)
        emit_tree(modules, fd)
        emit_footer(fd)

def print_help():
    print("""
Generates a html/javascript page that presents a tree-navigator
to the YANG module(s). Assumes that an images folder exists
relative to the html file. This images folder is installed in
share/yang/images in the  pyang install folder.
""")

def emit_css(fd):
    fd.write("""
<style type="text/css" media="all">

body, h1, h2, h3, h4, h5, h6, p, td, table td, input, select { 
	font-family: Verdana, Helvetica, Arial, sans-serif;
	font-size: 10pt;
}

body, ol, li, h2 { padding:0; margin: 0; }


ol#root {  padding-left: 5px; margin-top: 2px; margin-bottom: 1px; list-style: none;}
#root ol {  padding-left: 5px; margin-top: 2px; margin-bottom: 1px; list-style: none;}
#root li { margin-bottom: 1px; padding-left: 5px;  margin-top: 2px; font-size: x-small; }

.panel { border-bottom: 1px solid #999; margin-bottom: 2px; margin-top: 2px; background: #eee; }

#root ul { margin-bottom: 1px; margin-top: 2px; list-style-position: inside; } 

#root a { text-decoration: none; }


.folder { background: url(images/folder-closed.gif)  no-repeat; float: left; height: 14px; width: 26px; padding-right: 3px }
.doc { background: url(images/file.gif) no-repeat; float: left; height: 14px; width: 12px; padding-right: 3px; margin-left: 20px;}
.leaf { background: url(images/leaf.png) no-repeat; float: left; height: 14px; width: 12px; padding-right: 3px; margin-left: 20px;}
.leaf-list { background: url(images/leaf-plus.png) no-repeat; float: left; height: 14px; width: 12px; padding-right: 3px; margin-left: 20px;}
.action { background: url(images/hammer.png) no-repeat; float: left; height: 14px; width: 12px; padding-right: 3px; margin-left: 20px;}

# .folder { background:url(data:image/gif;base64,R0lGODlhGgAOALMLAJmZmYuLi3p6ev///+zs7MzMzGZmZqqqqrS0tLq6uuHh4f///wAAAAAAAAAAAAAAACH5BAEAAAsALAAAAAAaAA4AAASJcMlJq714qgROKUtxAABBgJkUFMQwFEhyFoFAKini7idSHwGDQXAYYAADxQdBOjiBQqGgYKx4AomCYoYAHqLRVVUCKCBdSthhCgYDKIDuTpnoGgptgxged3FHBgpgU2MTASsmdCM1gkNFGDVaHx91QQQ3KZGSZocHBCEpEgIrCYdxn6EVAnoIGREAOw==)  no-repeat; float: left; padding-right: 3px }

# .doc { background:url(data:image/gif;base64,R0lGODlhDAAOALMJAMzMzODg4P///+np6a+vr+7u7jMzM5mZmYmJif///wAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAAkALAAAAAAMAA4AAARFEEhyCAEjackPCESwBRxwCKD4BSSACCgxrKyJ3B42sK2FSINgsAa4AApI4W5yFCCTywts+txJp9TC4IrFcruwi2FMLgMiADs=) no-repeat; float: left; height: 14px; width: 12px; padding-right: 3px; margin-left: 20px;}

# .leaf { background:url(data:image/png;base64,
# iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAd9JREFUeNqkk09r1EAYxp83/7PsFnbZWhJXtlqk3kSFLUJFL1I/hwePfgB705PgQcQP4TeQ4kHUHqxW8Cr2H0XTpS1u7abJJjuz8e2kbqxUpOwLzySZmfzeZ2beoSzLMEpoGDEM1dw38i9i6UfY/6EJc+KxWDD+MeywZlm3WRdY1SN8EfnKTwQ0McCDKX+yde3S5UZtrFZxLccmIpimBtc1+alj/vmT18Ml/PmzrVtPb16dbTUnmn6SSERdiZi6KJct2LYLKWXuReYeFCDrq3eHNJq/fmWmNV6Z8Pf3I2TZAEQC9foYSiULQkilAWQKgZ+FA6FWeMOvezP1yrgfhhGSpMcZAc87owajqDfcvb1uJ+Ska8cBwJ3z3mTjIIwRHoRwHB3VqscgMZxwGKWSjaXlz9+5a6EA9FU7ZRpWubPXYesCvn8Ocdw7tkGmaWBtvd3++mX9IxtZ/BtQS5PU2t3dwfT0RbacFEfOm+a6NoJgq734bmmZsz/i7rgApKrVt7d30GiczY+ZS1zTCKIv0iiMwk/vV7e+bQYfOPNDmNj4XRWkJt7Sytz56oSaODyeH6wVrsyXnO4tWRTDystKvpBDB/dYb7iMnzEoOPVdyOJsjol3yaGAAacKGvU6/xJgAAaUrPTQ8rsPAAAAAElFTkSuQmCC) no-repeat; float: left; height: 14px; width: 12px; padding-right: 3px; margin-left: 20px;}

# .leaf-list { background:url(data:image/png;base64,
# iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAiFJREFUeNqkUz1v00AYfs6JPxIllRLcVHGDktKFAamCQCpQESBR2oEVGNhY2BgY6T9ADAix8BcY2CskurAgJRIgJpC6EehXnG/H9tnHm7OVtjSIoa/0vL7z3T33vB/HhBA4jSk4pSWle5KMZoyQiGn/R82wRn4z+Y9lg7BCWCWcI+Ri+kOLIp9KUEaIZ4tWpVY9v1TKz+SzKc3QGWNQVQWplErfBDZev9iahHD0sJ7QXt64tFIrz5Ut1w0w7AVwWA+ZjAZdTyEIgkhLEGmQBMKXY4MpbOPqxeXabHbO6naHECIEYxymOYN0WgPngUSIwANH51ABlxFet8zispmdtfr9IVx3RDcCxWJBLg6Ho0n22j27T5duHycA1heKldKg76A/6MMwEsjlikTEJxvGlk7r+FT//JN+bR4S+NIvqkktY7dtks5hWWfhOKNjCaqHP7Bj27ybaWvMx0exYMTV9iXynutp+/t7FLNJkt0JHMeV234PDvi9Ow+SwlT9cDXniIoRK/CkT+zu7qFUmo/KTC2uKAzc597XcDvxyz7wvJAPO0HnDHwxZqxTHRpMbrypZKDi/ZSeGJenJdazV249vF34e3Hr3YeY4JrylOYFauNXRNQ8wXI3+4aoquPxhftL1W9vvzTigjSiPnDEGk0eMYM1iWCajsfgJMYX9VbQApwQUNllJFmcg1A+jKPVOmk7lCguGs3n36l2rDE+jHkdfwQYAGBi2aFI3ki2AAAAAElFTkSuQmCC) no-repeat; float: left; height: 14px; width: 12px; padding-right: 3px; margin-left: 20px;}

# .action { background:url(data:image/png;base64,
# iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAA3UlEQVQ4Eb1Tiw2EIAwtl1sAR3AFZnEGRnAXV3AEV9BVcASur3cl9QKayyU2Afp5fW0FXc6ZnHOZfhDOcQp/qjIMA83zTN57SinRvu8aKue2beLXgiAqBCEEIUBi13W0LAtN0yQJIEU8xihk4zhS3/fvzjECCzZZ1l7XNTO4xICxcdjSATvLTOwESmy0iurWZ3XEHxI92dBqS1DokqCVXPyYqbYYkPlmMEL5NlVczQkfCDQZegv39wj3EOAq9fVhNiv3dGArfuuXHaD92o+lRO5zZWofTjs34w7PXYEvUq2x3ivJZWkAAAAASUVORK5CYII=) no-repeat; float: left; height: 14px; width: 12px; padding-right: 3px; margin-left: 20px;}


.tier1 { margin-left: 0; }
.tier2 { margin-left: 1.5em; }
.tier3 { margin-left: 3em; }
.tier4 { margin-left: 4.5em; }
.tier5 { margin-left: 6em; }
.tier6 { margin-left: 7.5em; }
.tier7 { margin-left: 9em; }
.tier8 { margin-left: 10.5em; }
.tier9 { margin-left: 12em; }
.tier10 { margin-left: 13.5em; }
.tier11 { margin-left: 15em; }
.tier12 { margin-left: 16.5em; }


.level1 { padding-left: 0; }
.level2 { padding-left: 1em; }
.level3 { padding-left: 2em; }
.level4 { padding-left: 3em; }
</style>
""")

def emit_js(fd):
    fd.write("""
<script language="javascript1.2">
// You probably should factor this out to a .js file
function toggleRows(elm) {
 var rows = document.getElementsByTagName("TR");
 elm.style.backgroundImage = "url(images/folder-closed.gif)";
 var newDisplay = "none";
 var thisID = elm.parentNode.parentNode.parentNode.id + "-";
 // Are we expanding or contracting? If the first child is hidden, we expand
  for (var i = 0; i < rows.length; i++) {
   var r = rows[i];
   if (matchStart(r.id, thisID, true)) {
    if (r.style.display == "none") {
     if (document.all) newDisplay = "block"; //IE4+ specific code
     else newDisplay = "table-row"; //Netscape and Mozilla
     elm.style.backgroundImage = "url(images/folder-open.gif)";
     // elm.style.backgroundImage = url(data:image/gif;base64,R0lGODlhGgAOALMLAJmZmYuLi3p6ev///+zs7MzMzGZmZqqqqrS0tLq6uuHh4f///wAAAAAAAAAAAAAAACH5BAEAAAsALAAAAAAaAA4AAASJcMlJq714qgROKUtxAABBgJkUFMQwFEhyFoFAKini7idSHwGDQXAYYAADxQdBOjiBQqGgYKx4AomCYoYAHqLRVVUCKCBdSthhCgYDKIDuTpnoGgptgxged3FHBgpgU2MTASsmdCM1gkNFGDVaHx91QQQ3KZGSZocHBCEpEgIrCYdxn6EVAnoIGREAOw==);
    }
    break;
   }
 }
 
 // When expanding, only expand one level.  Collapse all desendants.
 var matchDirectChildrenOnly = (newDisplay != "none");

 for (var j = 0; j < rows.length; j++) {
   var s = rows[j];
   if (matchStart(s.id, thisID, matchDirectChildrenOnly)) {
     s.style.display = newDisplay;
     var cell = s.getElementsByTagName("TD")[0];
     var tier = cell.getElementsByTagName("DIV")[0];
     var folder = tier.getElementsByTagName("A")[0];
     if (folder.getAttribute("onclick") != null) {
     folder.style.backgroundImage = "url(images/folder-closed.gif)";
     //folder.style.backgroundImage = url(data:image/gif;base64,R0lGODlhGgAOALMLAJmZmYuLi3p6ev///+zs7MzMzGZmZqqqqrS0tLq6uuHh4f///wAAAAAAAAAAAAAAACH5BAEAAAsALAAAAAAaAA4AAASJcMlJq714qgROKUtxAABBgJkUFMQwFEhyFoFAKini7idSHwGDQXAYYAADxQdBOjiBQqGgYKx4AomCYoYAHqLRVVUCKCBdSthhCgYDKIDuTpnoGgptgxged3FHBgpgU2MTASsmdCM1gkNFGDVaHx91QQQ3KZGSZocHBCEpEgIrCYdxn6EVAnoIGREAOw==);
     }
   }
 }
}

function matchStart(target, pattern, matchDirectChildrenOnly) {
 var pos = target.indexOf(pattern);
 if (pos != 0) return false;
 if (!matchDirectChildrenOnly) return true;
 if (target.slice(pos + pattern.length, target.length).indexOf("-") >= 0) return false;
 return true;
}

function collapseAllRows() {
 var rows = document.getElementsByTagName("TR");
 for (var j = 0; j < rows.length; j++) {
   var r = rows[j];
   if (r.id.indexOf("-") >= 0) {
     r.style.display = "none";    
   }
 }
}
</script>
""")
 
def emit_header(modules, fd):
    fd.write("""
 <title>YANG Navigator</title>
</head>

<body onload=\"collapseAllRows();\"> 

<div class=\"app\">
<div style=\"background: #eee; border: dashed 1px #000;\">
""")
    for module in modules:
        bstr = ""
        b = module.search_one('belongs-to')
        if b is not None:
            bstr = " (belongs-to %s)" % b.arg
        ns = module.search_one('namespace')
        if ns is not None:
            nsstr = ns.arg
        pr = module.search_one('prefix')
        if pr is not None:
            prstr = pr.arg

        fd.write("<h1> %s: %s%s, Namespace:%s, Prefix:%s</h1> \n" % (module.keyword.capitalize(), module.arg, bstr, nsstr, prstr))

    fd.write("""
 <table width=\"100%\">


 <tr>
  <!-- specifing one or more widths keeps columns constant despite changes in visible content -->
  <th align=left>Element</th>
  <th align=left>Schema</th>
  <th align=left>Type</th>
  <th align=left>Flags</th>
  <th align=left>Opts</th>
  <th align=left>Status</th>
  <th align=left>Path</th>
</tr>
""")

def emit_footer(fd):
    fd.write("""
</table>
</div>
</body>
</html>

""")

levelcnt = [0]*100


def emit_tree(modules, fd):
    global levelcnt
    for module in modules:
        bstr = ""
        b = module.search_one('belongs-to')
        if b is not None:
            bstr = " (belongs-to %s)" % b.arg
        ns = module.search_one('namespace')
        if ns is not None:
            nsstr = ns.arg
        pr = module.search_one('prefix')
        if pr is not None:
            prstr = pr.arg

        # fd.write("<h1> %s: %s%s ! Namespace %s ! Prefix %s</h1> \n" % (module.keyword, module.arg, bstr, nsstr, prstr))

        levelcnt[1] += 1
        fd.write("<tr id=\"%s\" class=\"a\"> <td id=\"p1\"><div id=\"p2\" class=\"tier1\"><a id=\"p3\" href=\"#\" onclick=\"toggleRows(this)\" class=\"folder\"></a>%s</div></td> \n" %(levelcnt[1], module.arg))
        fd.write("<td> module </td> <td>  </td> <td></td> <td>  </td> <td>  </td> </tr> \n")


        chs = [ch for ch in module.i_children
               if ch.keyword in statements.data_definition_keywords]
        print_children(chs, module, fd, ' ', 2)

        rpcs = module.search('rpc')
        levelcnt[1] += 1
        if len(rpcs) > 0:
            fd.write("<tr id=\"%s\" class=\"a\"> <td id=\"p1000\"><div id=\"p2000\" class=\"tier1\"><a id=\"p3000\" href=\"#\" onclick=\"toggleRows(this)\" class=\"folder\"></a>rpc:s</div></td> \n" %levelcnt[1])
            fd.write("<td> </td> <td>  </td> <td>  </td> <td>  </td> <td>  </td> </tr> \n")

            print_children(rpcs, module, fd, ' ', 2)

        notifs = module.search('notification')
        levelcnt[1] += 1
        if len(notifs) > 0:
            fd.write("<tr id=\"%s\" class=\"a\"> <td id=\"p4000\"><div id=\"p5000\" class=\"tier1\"><a id=\"p6000\" href=\"#\" onclick=\"toggleRows(this)\" class=\"folder\"></a>notifications</div></td> \n" %levelcnt[1])
            fd.write("<td> </td> <td>  </td> <td>  </td> <td>  </td> <td>  </td> </tr> \n")
            print_children(notifs, module, fd, ' ', 2)

def print_children(i_children, module, fd, prefix, level=0):
    
    ## def get_width(w, chs):
    ##     for ch in chs:
    ##         if ch.keyword in ['choice', 'case']:
    ##             w = get_width(w, ch.i_children)
    ##         else:
    ##             if ch.i_module.i_modulename == module.i_modulename:
    ##                 nlen = len(ch.arg)
    ##             else:
    ##                 nlen = len(ch.i_module.i_prefix) + 1 + len(ch.arg)
    ##             if nlen > w:
    ##                 w = nlen
    ##     return w
    
    ## if width == 0:
    ##     width = get_width(0, i_children)
    for ch in i_children:       
    ##     if ch == i_children[-1]:
    ##         newprefix = prefix
    ##         # newprefix = prefix + '   '
    ##     else:
    ##         newprefix = prefix
    ##         # newprefix = prefix + '  |'
        print_node(ch, module, fd, prefix, level)

def print_node(s, module, fd, prefix, level=0):
    global levelcnt
    # fd.write("%s%s--" % (prefix[0:-1], get_status_str(s)))
    status = get_status_str(s)
    nodetype = ''
    options = ''
    folder = False
    if s.i_module.i_modulename == module.i_modulename:
        name = s.arg
    else:
        name = s.i_module.i_prefix + ':' + s.arg
    flags = get_flags_str(s)
    if s.keyword == 'list':
        folder = True
        # fd.write(flags + " " + name)
    elif s.keyword == 'container':
        folder = True
        p = s.search_one('presence')
        if p is not None:
            # name += '?'
            pr_str = p.arg
            options = "<abbr title=\"" + pr_str + "\">Presence</abbr>"
        # fd.write(flags + " " + name)
    elif s.keyword  == 'choice':
        folder = True
        m = s.search_one('mandatory')
        if m is None or m.arg == 'false':
            # fd.write(flags + ' (' + s.arg + ')')
            name = '(' + s.arg + ')'
            options = 'Choice'
        else:
            # fd.write(flags + ' (' + s.arg + ')?')
            name = '(' + s.arg + ')'
    elif s.keyword == 'case':
        folder = True
        # fd.write(':(' + s.arg + ')')
        name = ':(' + s.arg + ')'
    elif s.keyword == 'input':
        folder = True
    elif s.keyword == 'output':
        folder = True
    elif s.keyword == 'rpc':
        folder = True
    else:
        if s.keyword == 'leaf-list':
            # name += '*'
            options = '*'
        elif s.keyword == 'leaf' and not hasattr(s, 'i_is_key'):
            m = s.search_one('mandatory')
            if m is None or m.arg == 'false':
                options = '?'
        nodetype = get_typename(s)
        # fd.write("%s %-*s   %s" % (flags, width+1, name, get_typename(s)))

    if s.keyword == 'list' and s.search_one('key') is not None:
        # fd.write(" [%s]" % s.search_one('key').arg)
        name += '[' + s.search_one('key').arg +  ']'

    descr = s.search_one('description')
    if descr is not None:
        descrstring = ''.join([x for x in descr.arg if ord(x) < 128])
    else:
        descrstring = "";
    levelcnt[level] += 1
    idstring = str(levelcnt[1])

    for i in range(2,level+1):
        idstring += '-' + str(levelcnt[i])

    pathstr = statements.mk_path_str(s, True)
            
    if folder:
        # hypertext link to non-existing YANG HTML....
        #fd.write("<tr id=\"%s\" class=\"a\"> <td id=\"p4000\"><div id=\"p5000\" class=\"tier%s\"><a id=\"p6000\" href=\"#\" onclick=\"toggleRows(this)\" class=\"folder\"></a><a title=\"%s\" target=\"src\" href=\"yang-module.shtml#%s\">%s</a></div></td> \n" %(idstring, level, descrstring, s.arg, name))
        fd.write("<tr id=\"%s\" class=\"a\"> <td id=\"p4000\"><div id=\"p5000\" class=\"tier%s\"><a id=\"p6000\" href=\"#\" onclick=\"toggleRows(this)\" class=\"folder\"></a>%s</div></td> \n" %(idstring, level, name))
        fd.write('<td title="I am a title">%s</td>   <td>%s</td>  <td>%s</td>  <td>%s</td>  <td>%s</td> <td>%s</td> </tr> \n' %(s.keyword, nodetype, flags, options, status, pathstr))
    else:
        if s.keyword == ('tailf-common', 'action'):
            classstring = "action"
            typeinfo = action_params(s)
            typename = "parameters"
        else:
            classstring = s.keyword
            typeinfo = typestring(s)
            typename = nodetype
            # hypertext link to non-existing YANG HTML....
            #fd.write('<tr id=\"%s\" class=\"a\"><td><div id=9999 class=tier%s> <a href =\"#\" class=\"%s\"></a><a title=\"%s\" target=\"src\" href=\"yang-module.shtml#%s\">%s</a></div> </td>   <td>%s</td>  <td><abbr title=\"%s\">%s</abbr></td>  <td>%s</td>  <td>%s</td>  <td>%s</td><td>%s</td</tr> \n' %(idstring, level,classstring, descrstring, s.keyword, name,s.keyword, typeinfo, typename, flags, options, status, pathstr))
        fd.write('<tr id=\"%s\" class=\"a\"><td><div id=9999 class=tier%s> <a href =\"#\" class=\"%s\"></a>%s</div> </td>   <td>%s</td>  <td><abbr title=\"%s\">%s</abbr></td>  <td>%s</td>  <td>%s</td>  <td>%s</td><td>%s</td</tr> \n' %(idstring, level,classstring, name,s.keyword, typeinfo, typename, flags, options, status, pathstr))

    if hasattr(s, 'i_children'):
        level += 1
        if s.keyword in ['choice', 'case']:
            print_children(s.i_children, module, fd, prefix, level)
        else:
            print_children(s.i_children, module, fd, prefix, level)

def get_status_str(s):
    status = s.search_one('status')
    if status is None or status.arg == 'current':
        return 'current'
    else:
        return status

def get_flags_str(s):
    if s.keyword == 'rpc':
        return ''
    elif s.keyword == 'notification':
        return ''    
    elif s.i_config == True:
        return 'config'
    else:
        return 'no config'

def get_typename(s):
    t = s.search_one('type')
    if t is not None:
        return t.arg
    else:
        return ''
    
def typestring(node):
    s = ""
    t = node.search_one('type')
    if t is not None:
        s = t.arg
        if t.arg == 'enumeration':
            s = s + ' : {'
            for enums in t.substmts:
                s = s + enums.arg + ','
            s = s + '}'
        elif t.arg == 'leafref':
            s = s + ' : '
            p = t.search_one('path')
            if p is not None:
                    s = s + p.arg

        elif t.arg == 'identityref':
            b = t.search_one('base')
            if b is not None:
                s = s + ' {' + b.arg + '}'

        elif t.arg == 'union':
            uniontypes = t.search('type')
            s = s + '{' + uniontypes[0].arg 
            for uniontype in uniontypes[1:]:
                s = s + ', ' + uniontype.arg
            s = s + '}' 


        typerange = t.search_one('range')
        if typerange is not None:
            s = s + ' [' + typerange.arg + ']'  
        length = t.search_one('length')
        if length is not None:
            s = s + ' {length = ' + length.arg + '}'  

        pattern = t.search_one('pattern')
        if pattern is not None: # truncate long patterns
            s = s + ' {pattern = ' + pattern.arg + '}'

    return s

def action_params(action):
    s = ""
    for params in action.substmts:

     if params.keyword == 'input':
         inputs = params.search('leaf')
         inputs += params.search('leaf-list')
         inputs += params.search('list')
         inputs += params.search('container')
         inputs += params.search('anyxml')
         inputs += params.search('uses')
         for i in inputs:
            s += ' in: ' + i.arg
            
     if params.keyword == 'output':
         outputs = params.search('leaf')
         outputs += params.search('leaf-list')
         outputs += params.search('list')
         outputs += params.search('container')
         outputs += params.search('anyxml')
         outputs += params.search('uses')
         for o in outputs:
             s += ' out: ' + o.arg
    return s


def full_path(stmt):
    pathsep = "/"
    path = stmt.arg
    exclude =  ['grouping', 'choice', 'case', 'submodule', 'module']
    if (stmt.keyword not in exclude):
        while stmt.parent is not None:
            stmt = stmt.parent
            if (stmt.arg is not None) and (stmt.keyword not in exclude):
                path = stmt.arg + pathsep + path
    return path


def make_keyword(s):
    s = s.replace('-', '_')
    s = s.replace('/', '_')
    s = s.replace(':', '_')
    return s
