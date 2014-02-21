"""JS-Tree output plugin
Generates a html/javascript page that presents a tree-navigator
to the YANG module(s).
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
        emit_bodystart(modules,fd)
        emit_tree(modules, fd)
        emit_footer(fd)

def print_help():
    print """
Generates a html/javascript page that presents a tree-navigator
to the YANG module(s).
"""

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



.folder { background:url(data:image/gif;base64,R0lGODlhGgAOALMLAJmZmYuLi3p6ev///+zs7MzMzGZmZqqqqrS0tLq6uuHh4f///wAAAAAAAAAAAAAAACH5BAEAAAsALAAAAAAaAA4AAASJcMlJq714qgROKUtxAABBgJkUFMQwFEhyFoFAKini7idSHwGDQXAYYAADxQdBOjiBQqGgYKx4AomCYoYAHqLRVVUCKCBdSthhCgYDKIDuTpnoGgptgxged3FHBgpgU2MTASsmdCM1gkNFGDVaHx91QQQ3KZGSZocHBCEpEgIrCYdxn6EVAnoIGREAOw==)  no-repeat; float: left; padding-right: 30px;margin-left: 3px;
}

.doc {
background:url(data:image/gif;base64,R0lGODlhDAAOALMJAMzMzODg4P///+np6a+vr+7u7jMzM5mZmYmJif///wAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAAkALAAAAAAMAA4AAARFEEhyCAEjackPCESwBRxwCKD4BSSACCgxrKyJ3B42sK2FSINgsAa4AApI4W5yFCCTywts+txJp9TC4IrFcruwi2FMLgMiADs=)
no-repeat; float: left; padding-right: 10px; margin-left: 3px;
}

.leaf {
background:url(data:image/gif;base64,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)
no-repeat; float: left; padding-right: 10px;margin-left: 3px;
}

.leaf-list {
background:url(data:image/gif;base64,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)
no-repeat; float: left; padding-right: 10px; margin-left: 3px;
}

.action {
background:url(data:image/gif;base64,R0lGODlhEAAQALMAAAAAABERETMzM1VVVWZmZnd3d4iIiJmZmaqqqru7u8zMzO7u7v///wAAAAAAAAAAACH5BAkKAA0AIf8LSUNDUkdCRzEwMTL/AAAHqGFwcGwCIAAAbW50clJHQiBYWVogB9kAAgAZAAsAGgALYWNzcEFQUEwAAAAAYXBwbAAAAAAAAAAAAAAAAAAAAAAAAPbWAAEAAAAA0y1hcHBsAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALZGVzYwAAAQgAAABvZHNjbQAAAXgAAAVsY3BydAAABuQAAAA4d3RwdAAABxwAAAAUclhZWgAABzAAAAAUZ1hZWgAAB0QAAAAUYlhZWgAAB1gAAAAUclRSQwAAB2wAAAAOY2hhZAAAB3wAAAAsYlRSQwAAB2wAAAAOZ1RS/0MAAAdsAAAADmRlc2MAAAAAAAAAFEdlbmVyaWMgUkdCIFByb2ZpbGUAAAAAAAAAAAAAABRHZW5lcmljIFJHQiBQcm9maWxlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABtbHVjAAAAAAAAAB4AAAAMc2tTSwAAACgAAAF4aHJIUgAAACgAAAGgY2FFUwAAACQAAAHIcHRCUgAAACYAAAHsdWtVQQAAACoAAAISZnJGVQAAACgAAAI8emhUVwAAABYAAAJkaXRJVAAAACgAAAJ6bmJOTwAAACYAAAKia29LUgAAABYAAP8CyGNzQ1oAAAAiAAAC3mhlSUwAAAAeAAADAGRlREUAAAAsAAADHmh1SFUAAAAoAAADSnN2U0UAAAAmAAAConpoQ04AAAAWAAADcmphSlAAAAAaAAADiHJvUk8AAAAkAAADomVsR1IAAAAiAAADxnB0UE8AAAAmAAAD6G5sTkwAAAAoAAAEDmVzRVMAAAAmAAAD6HRoVEgAAAAkAAAENnRyVFIAAAAiAAAEWmZpRkkAAAAoAAAEfHBsUEwAAAAsAAAEpHJ1UlUAAAAiAAAE0GFyRUcAAAAmAAAE8mVuVVMAAAAmAAAFGGRhREsAAAAuAAAFPgBWAWEAZQBvAGIAZQD/YwBuAP0AIABSAEcAQgAgAHAAcgBvAGYAaQBsAEcAZQBuAGUAcgBpAQ0AawBpACAAUgBHAEIAIABwAHIAbwBmAGkAbABQAGUAcgBmAGkAbAAgAFIARwBCACAAZwBlAG4A6AByAGkAYwBQAGUAcgBmAGkAbAAgAFIARwBCACAARwBlAG4A6QByAGkAYwBvBBcEMAQzBDAEOwRMBD0EOAQ5ACAEPwRABD4ERAQwBDkEOwAgAFIARwBCAFAAcgBvAGYAaQBsACAAZwDpAG4A6QByAGkAcQB1AGUAIABSAFYAQpAadSgAIABSAEcAQgAggnJfaWPPj/AAUAByAG8AZgBp/wBsAG8AIABSAEcAQgAgAGcAZQBuAGUAcgBpAGMAbwBHAGUAbgBlAHIAaQBzAGsAIABSAEcAQgAtAHAAcgBvAGYAaQBsx3y8GAAgAFIARwBCACDVBLhc0wzHfABPAGIAZQBjAG4A/QAgAFIARwBCACAAcAByAG8AZgBpAGwF5AXoBdUF5AXZBdwAIABSAEcAQgAgBdsF3AXcBdkAQQBsAGwAZwBlAG0AZQBpAG4AZQBzACAAUgBHAEIALQBQAHIAbwBmAGkAbADBAGwAdABhAGwA4QBuAG8AcwAgAFIARwBCACAAcAByAG8AZgBpAGxmbpAaACAAUgBHAEIAIGPPj//wZYdO9k4AgiwAIABSAEcAQgAgMNcw7TDVMKEwpDDrAFAAcgBvAGYAaQBsACAAUgBHAEIAIABnAGUAbgBlAHIAaQBjA5MDtQO9A7kDugPMACADwAPBA78DxgOvA7sAIABSAEcAQgBQAGUAcgBmAGkAbAAgAFIARwBCACAAZwBlAG4A6QByAGkAYwBvAEEAbABnAGUAbQBlAGUAbgAgAFIARwBCAC0AcAByAG8AZgBpAGUAbA5CDhsOIw5EDh8OJQ5MACAAUgBHAEIAIA4XDjEOSA4nDkQOGwBHAGUAbgBlAGwAIABSAEcAQgAgAFAAcgBvAGYAaQBsAGkAWQBsAGX/AGkAbgBlAG4AIABSAEcAQgAtAHAAcgBvAGYAaQBpAGwAaQBVAG4AaQB3AGUAcgBzAGEAbABuAHkAIABwAHIAbwBmAGkAbAAgAFIARwBCBB4EMQRJBDgEOQAgBD8EQAQ+BEQEOAQ7BEwAIABSAEcAQgZFBkQGQQAgBioGOQYxBkoGQQAgAFIARwBCACAGJwZEBjkGJwZFAEcAZQBuAGUAcgBpAGMAIABSAEcAQgAgAFAAcgBvAGYAaQBsAGUARwBlAG4AZQByAGUAbAAgAFIARwBCAC0AYgBlAHMAawByAGkAdgBlAGwAcwBldGV4dAAAAABDb3B5cmlnaHQgMjAwrzcgQXBwbGUgSW5jLiwgYWxsIHJpZ2h0cyByZXNlcnZlZC4AWFlaIAAAAAAAAPNSAAEAAAABFs9YWVogAAAAAAAAdE0AAD3uAAAD0FhZWiAAAAAAAABadQAArHMAABc0WFlaIAAAAAAAACgaAAAVnwAAuDZjdXJ2AAAAAAAAAAEBzQAAc2YzMgAAAAAAAQxCAAAF3v//8yYAAAeSAAD9kf//+6L///2jAAAD3AAAwGwALAAAAAAQABAAAARDsIFJ62xYDhDY+l+CXJIxBQoxEMdUtNI1KQUVA1nO4XqeAQKebwgUDn+DgPEoUS6PuyfRydQplVXMDpvdSq3U7G0YAQA7)
no-repeat; float: left; height: 14px; width: 12px; padding-right: 10px; margin-left: 3px;}



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
function toggleRows(elm) {
 var rows = document.getElementsByTagName("TR");
 elm.style.backgroundImage = "url(data:image/gif;base64,R0lGODlhGgAOALMLAJmZmYuLi3p6ev///+zs7MzMzGZmZqqqqrS0tLq6uuHh4f///wAAAAAAAAAAAAAAACH5BAEAAAsALAAAAAAaAA4AAASJcMlJq714qgROKUtxAABBgJkUFMQwFEhyFoFAKini7idSHwGDQXAYYAADxQdBOjiBQqGgYKx4AomCYoYAHqLRVVUCKCBdSthhCgYDKIDuTpnoGgptgxged3FHBgpgU2MTASsmdCM1gkNFGDVaHx91QQQ3KZGSZocHBCEpEgIrCYdxn6EVAnoIGREAOw==)";
 var newDisplay = "none";
 var thisID = elm.parentNode.parentNode.parentNode.id + "-";
 // Are we expanding or contracting? If the first child is hidden, we expand
  for (var i = 0; i < rows.length; i++) {
   var r = rows[i];
   if (matchStart(r.id, thisID, true)) {
    if (r.style.display == "none") {
     if (document.all) newDisplay = "block"; //IE4+ specific code
     else newDisplay = "table-row"; //Netscape and Mozilla
     // elm.style.backgroundImage = "url(images/folder-open.gif)";
     elm.style.backgroundImage = "url(data:image/gif;base64,R0lGODlhGgAOALMLAJmZmYqKiv///+zs7MzMzGZmZrOzs7q6uqqqqnZ2duHh4f///wAAAAAAAAAAAAAAACH5BAEAAAsALAAAAAAaAA4AAASScMlJq714qgMMIQuBAMAwZBRADIJAGMfwBQE6GW0uGzRS2wuAQPHhABAIAyBAABSe0IJKgiAEDgSF7OVDBKNQwEQlbBG5CZAiAA4oxsoc8WBAFEALe9SQ6rS2dU5vCwJsTwECKUwmcyMBCYMhUHgTj1kfRTwFJxKFBYgVlpdNNCUVBHcWCUwHpQacFgJCqp98GBEAOw==)";
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
     folder.style.backgroundImage = "url(data:image/gif;base64,R0lGODlhGgAOALMLAJmZmYuLi3p6ev///+zs7MzMzGZmZqqqqrS0tLq6uuHh4f///wAAAAAAAAAAAAAAACH5BAEAAAsALAAAAAAaAA4AAASJcMlJq714qgROKUtxAABBgJkUFMQwFEhyFoFAKini7idSHwGDQXAYYAADxQdBOjiBQqGgYKx4AomCYoYAHqLRVVUCKCBdSthhCgYDKIDuTpnoGgptgxged3FHBgpgU2MTASsmdCM1gkNFGDVaHx91QQQ3KZGSZocHBCEpEgIrCYdxn6EVAnoIGREAOw==)";
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
<head>
 <title>YANG Navigator</title>
</head>
""")

def emit_footer(fd):
    fd.write("""
</table>
</div>
</body>
</html>

""")

levelcnt = [0]*100

def emit_bodystart(modules, fd):
    fd.write("""
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
        fd.write("""
<a href="http://www.tail-f.com">
<img src="data:image/gif;base64,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" >
</a>
""")
        fd.write("<h1> %s: <font color=blue>%s%s</font>, Namespace: <font color=blue>%s</font>, Prefix: <font color=blue>%s</font></h1> \n" % (module.keyword.capitalize(), module.arg, bstr, nsstr, prstr))

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


        levelcnt[1] += 1
        fd.write("<tr id=\"%s\" class=\"a\"> <td id=\"p1\"><div id=\"p2\" class=\"tier1\"><a id=\"p3\"  onclick=\"toggleRows(this)\" class=\"folder\">&nbsp;</a>%s</div></td> \n" %(levelcnt[1], module.arg))
        fd.write("<td> module </td> <td>  </td> <td></td> <td>  </td> <td>  </td> </tr> \n")


        chs = [ch for ch in module.i_children
               if ch.keyword in statements.data_definition_keywords]
        print_children(chs, module, fd, ' ', 2)

        rpcs = module.search('rpc')
        levelcnt[1] += 1
        if len(rpcs) > 0:
            fd.write("<tr id=\"%s\" class=\"a\"> <td id=\"p1000\"><div id=\"p2000\" class=\"tier1\"><a id=\"p3000\"  onclick=\"toggleRows(this)\" class=\"folder\">&nbsp;</a>rpc:s</div></td> \n" %levelcnt[1])
            fd.write("<td> </td> <td>  </td> <td>  </td> <td>  </td> <td>  </td> </tr> \n")

            print_children(rpcs, module, fd, ' ', 2)

        notifs = module.search('notification')
        levelcnt[1] += 1
        if len(notifs) > 0:
            fd.write("<tr id=\"%s\" class=\"a\"> <td id=\"p4000\"><div id=\"p5000\" class=\"tier1\"><a id=\"p6000\"  onclick=\"toggleRows(this)\" class=\"folder\">&nbsp;</a>notifications</div></td> \n" %levelcnt[1])
            fd.write("<td> </td> <td>  </td> <td>  </td> <td>  </td> <td>  </td> </tr> \n")
            print_children(notifs, module, fd, ' ', 2)

def print_children(i_children, module, fd, prefix, level=0):
    for ch in i_children:       
        print_node(ch, module, fd, prefix, level)

def print_node(s, module, fd, prefix, level=0):
    global levelcnt
    status = get_status_str(s)
    nodetype = ''
    options = ''
    folder = False
    if s.i_module.i_modulename == module.i_modulename:
        name = s.arg
    else:
        name = s.i_module.i_prefix + ':' + s.arg

    descr = s.search_one('description')
    descrstring = "No description"
    if descr is not None:
        descrstring = descr.arg
    flags = get_flags_str(s)
    if s.keyword == 'list':
        folder = True
    elif s.keyword == 'container':
        folder = True
        p = s.search_one('presence')
        if p is not None:
            pr_str = p.arg
            options = "<abbr title=\"" + pr_str + "\">Presence</abbr>"
    elif s.keyword  == 'choice':
        folder = True
        m = s.search_one('mandatory')
        if m is None or m.arg == 'false':
            name = '(' + s.arg + ')'
            options = 'Choice'
        else:
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
    elif s.keyword == 'notification':
        folder = True
    else:
        if s.keyword == 'leaf-list':
            options = '*'
        elif s.keyword == 'leaf' and not hasattr(s, 'i_is_key'):
            m = s.search_one('mandatory')
            if m is None or m.arg == 'false':
                options = '?'
        nodetype = get_typename(s)

    if s.keyword == 'list' and s.search_one('key') is not None:
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
        fd.write("<tr id=\"%s\" class=\"a\"> <td id=\"p4000\"><div id=\"p5000\" class=\"tier%s\"><a id=\"p6000\"  onclick=\"toggleRows(this)\" class=\"folder\">&nbsp;</a>%s</div></td> \n" %(idstring, level, name))
        fd.write('<td><abbr title=\"DESCRIPTION\">%s</abbr></td>   <td>%s</td>  <td>%s</td>  <td>%s</td>  <td>%s</td> <td>%s</td> </tr> \n' %(s.keyword, nodetype, flags, options, status, pathstr))
    else:
        if s.keyword == ('tailf-common', 'action'):
            classstring = "action"
            typeinfo = action_params(s)
            typename = "parameters"
        elif s.keyword == 'rpc' or s.keyword == 'notification':
            classstring = "folder"
            typeinfo = action_params(s)
            typename = "parameters"            
        else:
            classstring = s.keyword
            typeinfo = typestring(s)
            typename = nodetype
        fd.write('<tr id=\"%s\" class=\"a\"><td><div id=9999 class=tier%s> <a href =\"#\" class=\"%s\">&nbsp;</a><abbr title=\"%s\">%s</abbr></div> </td>   <td>%s</td>  <td><abbr title=\"%s\">%s</abbr></td>  <td>%s</td>  <td>%s</td>  <td>%s</td><td>%s</td</tr> \n' %(idstring, level,classstring, descrstring, name,s.keyword, typeinfo, typename, flags, options, status, pathstr))

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

    def get_nontypedefstring(node):
        s = ""
        found  = False
        t = node.search_one('type')
        if t is not None:
            s = t.arg + '\n'
            if t.arg == 'enumeration':
                found = True
                s = s + ' : {'
                for enums in t.substmts:
                    s = s + enums.arg + ','
                s = s + '}'
            elif t.arg == 'leafref':
                found = True
                s = s + ' : '
                p = t.search_one('path')
                if p is not None:
                    s = s + p.arg

            elif t.arg == 'identityref':
                found = True                
                b = t.search_one('base')
                if b is not None:
                    s = s + ' {' + b.arg + '}'

            elif t.arg == 'union':
                found = True                
                uniontypes = t.search('type')
                s = s + '{' + uniontypes[0].arg 
                for uniontype in uniontypes[1:]:
                    s = s + ', ' + uniontype.arg
                s = s + '}' 


            typerange = t.search_one('range')
            if typerange is not None:
                found = True
                s = s + ' [' + typerange.arg + ']'  
            length = t.search_one('length')
            if length is not None:
                found = True
                s = s + ' {length = ' + length.arg + '}'  

            pattern = t.search_one('pattern')
            if pattern is not None: # truncate long patterns
                found = True
                s = s + ' {pattern = ' + pattern.arg + '}'
        return s
    
    s = get_nontypedefstring(node)

    if s != "":
        t = node.search_one('type')
        # chase typedef
        type_namespace = None
        i_type_name = None
        name = t.arg
        if name.find(":") == -1:
            prefix = None
        else:
            [prefix, name] = name.split(':', 1)
        if prefix is None or t.i_module.i_prefix == prefix:
            # check local typedefs
            pmodule = node.i_module
            typedef = statements.search_typedef(t, name)
        else:
            # this is a prefixed name, check the imported modules
            err = []
            pmodule = statements.prefix_to_module(t.i_module, prefix, t.pos, err)
            if pmodule is None:
                return
            typedef = statements.search_typedef(pmodule, name)
        if typedef != None:
            s = s + get_nontypedefstring(typedef)

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
            s += ' in: ' + i.arg + "\n"
            
     if params.keyword == 'output':
         outputs = params.search('leaf')
         outputs += params.search('leaf-list')
         outputs += params.search('list')
         outputs += params.search('container')
         outputs += params.search('anyxml')
         outputs += params.search('uses')
         for o in outputs:
             s += ' out: ' + o.arg + "\n"
    return s
