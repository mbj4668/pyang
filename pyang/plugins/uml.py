"""uml output plugin
1) download plantuml.sourceforge.net/
2) Invoke with:
>pyang -f uml <file.yang> > <file.uml>
>java -jar plantuml.jar <file.uml>

3) result in img/module.png

For huge models Java might spit out memory exceptions, increase heap with e.g. -Xmx256m flag to java

"""
# TODO:
# -elements with same name at same level, we assume the path is unique
# cleanup choice and case with function

import optparse
import sys
import datetime
import re

from pyang import plugin
from pyang import util
from pyang import grammar
from pyang import error
from pyang import syntax
from pyang import statements
from pyang.error import err_add


def pyang_plugin_init():
    plugin.register_plugin(UMLPlugin())

class UMLPlugin(plugin.PyangPlugin): 
    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--uml-classes-only",
                                 action="store_true",
                                 dest="classes_only",
                                 default = False,
                                 help="Generate UML with classes only, no attributes "),
            optparse.make_option("--uml-split-pages",
                                 dest="pages_layout",
                                 help="Generate UML output split into pages (separate .png files), NxN, example 2x2 "),
            optparse.make_option("--uml-output-directory",
                                 dest="outputdir",
                                 help="Put generated <modulename>.png file(s) in OUTPUTDIR (default img/) "),
            optparse.make_option("--uml-title",
                                 dest="title",
                                 help="Set the title of the generated UML"),
            optparse.make_option("--uml-short-identifiers",
                                 action="store_true",
                                 dest="uniqueelements",
                                 default =False,
                                 help="Do not use the full schema identifier for UML class names."),
            optparse.make_option("--uml-no-uses",
                                 action="store_true",                                 
                                 dest="no_uses",
                                 default = False,                                 
                                 help="Do not render uses associations, this may simplify complex diagrams. The uses is still rendered as an attribute."),
            optparse.make_option("--uml-no-leafrefs",
                                 action="store_true",                               
                                 dest="no_leafrefs",
                                 default = False,                                 
                                 help="Do not render leafref associations, this may simplify complex diagrams"),
            optparse.make_option("--uml-no-annotations",
                                 action="store_true",                               
                                 dest="no_annotations",
                                 default = False,                                 
                                 help="Do not render annotations (must, present-if, ...), this may simplify complex diagrams"),
            optparse.make_option("--uml-filter",
                                 action="store_true",                               
                                 dest="gen_filter_file",
                                 default = False,                                 
                                 help="Generate filter file, comment out lines with '-' and use with option '--filter-file' to filter the UML diagram"),
            optparse.make_option("--uml-filter-file",
                                 dest="filter_file",
                                 help="NOT IMPLEMENTED: Only paths in the filter file will be included in the diagram"),
            ]
        if hasattr(optparser, 'uml_opts'):
            g = optparser.uml_opts
        else:
            g = optparser.add_option_group("UML specific options")
            optparser.uml_opts = g
        g.add_options(optlist)
    
    def add_output_format(self, fmts):
        fmts['uml'] = self

    def pre_validate(self, ctx, modules):
        module = modules[0]
        self.mods = [module.arg] + [i.arg for i in module.search('include')]

    def emit(self, ctx, modules, fd):
        for (epos, etag, eargs) in ctx.errors:
            if (epos.top.arg in self.mods and
                error.is_error(error.err_level(etag))):
                self.fatal("%s contains errors" % epos.top.arg)

  
        if ctx.opts.pages_layout is not None:
            if re.match('[0-9]x[0-9]', ctx.opts.pages_layout) is None:
                fatal("Illegal page split option %s, should be [0-9]x[0-9], example 2x2" %ctx.opts.pages_layout, 2)

        umldoc = uml_emitter(ctx)
        umldoc.emit(modules[0], fd)

    def fatal(s, exitCode=1):
        raise error.EmitError(s, exitCode)


class uml_emitter:
    key = ''
    unique = ''
    ctx_pagelayout = '1x1'
    ctx_outputdir = "img/"
    ctx_title = None
    ctx_fullpath = True
    ctx_classesonly = False
    ctx_leafrefs = True
    ctx_uses = True
    ctx_annotations = True
    ctx_filterfile = False
    ctx_usefilterfile = None
    groupings = dict()
    uses = []
    uses_as_string = dict()
    leafrefs = []
    filterpaths = []
    thismod_prefix = ''
    _ctx = None
    post_strings = [] 

    def __init__(self, ctx):
        self._ctx = ctx
        self.ctx_fullpath = (not ctx.opts.uniqueelements)
        self.ctx_classesonly = ctx.opts.classes_only        
        # output dir from option -D or default img/
        if ctx.opts.outputdir is not None:
            self.ctx_outputdir = ctx.opts.outputdir
            if self.ctx_outputdir[len(self.ctx_outputdir)-1] != '/':
                self.ctx_outputdir += '/'
        else:
            self.ctx_outputdir = 'img/'

        # split into pages ? option -s
        if ctx.opts.pages_layout is not None:
            self.ctx_pagelayout = ctx.opts.pages_layout        

        # Title from option -t 
        self.ctx_title = ctx.opts.title

        self.ctx_leafrefs = (not ctx.opts.no_leafrefs)
        self.ctx_uses = (not ctx.opts.no_uses)
        self.ctx_annotations = (not ctx.opts.no_annotations)
        self.ctx_filterfile = ctx.opts.gen_filter_file
        if ctx.opts.filter_file is not None:
            try:
                self.ctx_usefilterfile = open(ctx.opts.filter_file, "r")
                self.filterpaths = self.ctx_usefilterfile.readlines()
                self.ctx_usefilterfile.close()
            except IOError:
                raise error.EmitError("Filter file %s does not exist" %ctx.opts.filter_file, 2)
            
    def emit(self, module, fd):
        if not self.ctx_filterfile:
            self.emit_module_header(module, fd)

        for s in module.substmts:
             self.emit_stmt(module, s, fd)

        if not self.ctx_filterfile:
            self.post_process(fd)
            self.emit_module_footer(module, fd)


    def emit_stmt(self, mod, stmt, fd):
        # find  good UML roots

        if stmt.keyword == 'container':
            self.emit_container(mod, stmt, fd)
            for s in stmt.substmts:
                self.emit_child_stmt(stmt, s, fd)

        elif stmt.keyword == 'augment' and (not self.ctx_filterfile):
             # ugly, the augmented elemented is suffixed with _ in emit_header
             # simulate full path by prefixing with module name
             fd.write('class \"%s\" as %s <<augment>>\n' %(stmt.arg, self.full_path(stmt)))
             fd.write('_%s <-- %s : augment \n' %(self.full_path(stmt), self.full_path(stmt)))
             # also, since we are the root, add the module as parent
             fd.write('%s *-- \"1\" %s \n' %(self.full_path(mod), self.full_path(stmt)))
             for s in stmt.substmts:
                 self.emit_child_stmt(stmt, s, fd)

        elif stmt.keyword == 'list':
            self.emit_list(mod, stmt, fd)
            for s in stmt.substmts:
                self.emit_child_stmt(stmt, s, fd)

        elif stmt.keyword == 'grouping':
            self.emit_grouping(mod, stmt, fd, True)

        elif stmt.keyword == 'choice':
            if (not self.ctx_filterfile):
                fd.write('class \"%s\" as %s\n' %(self.full__display_path(mod), self.full_path(mod)))
                fd.write('%s .. %s : choice \n' % (self.full_path(mod), self.full_path(stmt)))
            # sys.stderr.write('in choice %s \n', self.full_path(mod))        
            for children in mod.substmts:
                self.emit_child_stmt(mod, stmt, fd)

        elif stmt.keyword == 'case':
            if (not self.ctx_filterfile):
                fd.write('class \"%s\" as %s \n' %(self.full_display_path(stmt), self.full_path(stmt)))
                fd.write('%s ..  %s  : choice\n' % (self.full_path(mod), self.full_path(stmt)))
            # sys.stderr.write('in case %s \n', full_path(mod))
            for children in mod.substmts:
                    self.emit_child_stmt(mod, stmt, fd)

        if (not self.ctx_classesonly) and (not self.ctx_filterfile):
            if stmt.keyword == 'typedef':
                self.emit_typedef(mod, stmt,fd)
            elif stmt.keyword == 'rpc':
                self.emit_action(mod, stmt,fd)
            elif stmt.keyword == 'notification':
                self.emit_notif(mod, stmt,fd)
            elif stmt.keyword == 'feature':
                self.emit_feature(mod,stmt, fd)
            elif stmt.keyword == 'deviation':
                self.emit_feature(mod,stmt, fd)


        # go down one level and search for good UML roots
        # I think we have covered all....
        # else:
            # sys.stderr.write('skipping top level: %s:%s\n' % (stmt.keyword, stmt.arg))
            # for s in stmt.substmts:
              # emit_stmt(mod, s, fd)


    def emit_child_stmt(self, parent, node, fd):
         keysign = ''
         keyprefix = ''
         uniquesign = ''

         if node.keyword == 'container':
             self.emit_container(parent, node, fd)
             for children in node.substmts:
                self.emit_child_stmt(node, children, fd)
         elif node.keyword == 'grouping':
             self.emit_grouping(parent, node, fd)

         elif node.keyword == 'list':
             self.emit_list(parent, node, fd)
             for children in node.substmts:
                self.emit_child_stmt(node, children, fd)

         elif node.keyword == 'choice':
             if (not self.ctx_filterfile):
                 pass
                 # try skipping choice pivot node
                 # fd.write('class \"%s\" as %s \n' % (self.full_path(node, False), self.full_path(node)))
                 # fd.write('%s .. %s : choice \n' % (self.full_path(parent), self.full_path(node)))
             for children in node.substmts:
                 # try pointing to parent
                 # self.emit_child_stmt(node, children, fd)
                 self.emit_child_stmt(parent, children, fd)
         elif node.keyword == 'case':
             # sys.stderr.write('in case \n')
             if (not self.ctx_filterfile):
                fd.write('class \"%s\" as %s <<case>>\n' %(self.full_display_path(node), self.full_path(node)))
                fd.write('%s .. %s  : choice %s\n' % (self.full_path(parent), self.full_path(node), node.parent.arg))
             for children in node.substmts:
                self.emit_child_stmt(node, children, fd)
         elif node.keyword == 'uses':
             if (not self.ctx_filterfile):                          
                 fd.write('%s : %s {uses} \n' %(self.full_path(parent), node.arg))
             self.emit_uses(parent, node)


         if (not self.ctx_classesonly) and (not self.ctx_filterfile):     
             if node.keyword == 'leaf':
                 if node.arg in self.key: # matches previously found key statement
                     keysign = ' {key}'
                     keyprefix = '+'
                 if node.arg in self.unique: # matches previously found unique statement
                     keysign = ' {unique}'
                 # fd.write('%s : %s%s %s %s\n' %(full_path(parent), keysign, make_plantuml_keyword(node.arg), typestring(node), attribs(node) ))
                 fd.write('%s : %s%s%s %s %s\n' %(self.full_path(parent), keyprefix, node.arg + ' : ', self.typestring(node), keysign, self.attribs(node) ))
                 self.emit_must_leaf(parent, node, fd)
             elif node.keyword == 'leaf-list':
                 fd.write('%s : %s %s %s\n' %(self.full_path(parent), node.arg, '[]: ' + self.typestring(node), self.attribs(node)) ) 
                 self.emit_must_leaf(parent, node, fd)
             elif node.keyword == ('tailf-common', 'action'):
                 self.emit_action(parent, node, fd)
             elif node.keyword == ('tailf-common', 'callpoint'):
                 fd.write('%s : callpoint:%s()\n' %(self.full_path(parent), node.arg) )
             elif node.keyword == ('tailf-common', 'cdb-oper'):
                 fd.write('%s : cdboper()\n' %self.full_path(parent))
             elif node.keyword == ('anyxml'):
                 fd.write('%s : %s anyxml \n' %(self.full_path(parent), node.arg))
             elif node.keyword == 'key':
                 self.key = node.arg.split(" ") # multiple keys, make list of every key
             elif node.keyword == 'unique':
                 self.unique = node.arg.split(" ") # multiple keys, make list of every key
             elif node.keyword == 'config':
                 self.annotate_node(parent, "Config = " + node.arg, fd)
             elif node.keyword == 'must':
                 self.emit_must(parent, node, fd)
             elif node.keyword == ('tailf-common', 'hidden'):
                 self.annotate_node(parent, "Hidden " + node.arg, fd)
             elif node.keyword == 'presence':
                 self.annotate_node(parent, "Presence: " + node.arg, fd)         
             elif node.keyword == 'when':
                 self.annotate_node(parent, "When: " + node.arg, fd)         
             elif node.keyword == 'status':
                 self.annotate_node(parent, "Status: " + node.arg, fd)         
             elif node.keyword == 'if-feature':
                 self.annotate_node(parent, "if-feature: " + node.arg, fd)
             # else:  probably unknown extension
                 # fd.write('%s : %s %s' %(self.full_path(parent), node.keyword, node.arg))

         # fd.write('\n')

    def emit_module_header(self, module, fd):
        fd.write('\'Download plantuml from http://plantuml.sourceforge.net/ \n')
        fd.write('\'Generate png with java -jar plantuml.jar <file> \n')
        fd.write('\'Output in img/<module>.png \n')
        fd.write('\'If Java spits out memory error increase heap size with java -Xmx1024m  -jar plantuml.jar <file> \n')


        fd.write('@startuml %s%s.png \n' %(self.ctx_outputdir, module.arg))
        fd.write('hide empty members \n')
        fd.write('hide empty methods \n')
        fd.write('hide <<case>> circle\n')
        fd.write('hide <<augment>> circle\n') 



        # split into pages ? option -s
        fd.write('page %s \n' %self.ctx_pagelayout)        

        # Title from option -t 
        if self.ctx_title is not None:
            fd.write('Title %s \n' %self.ctx_title)
        else:
            fd.write('Title <b>UML Generated by pyang from Module :  %s</b> \n' % module.arg)

        # print module info as note
        fd.write('note as M \n')
        ns = module.search_one('namespace')
        if ns is not None:
            fd.write('  namespace: %s\n' % ns.arg)
        
        pre = module.search_one('prefix')
        if  pre is not None:
            fd.write('  prefix: %s\n' % pre.arg)
            self.thismod_prefix = pre.arg
            
        bt = module.search_one('belongs-to')
        if bt is not None:
            fd.write('  belongs-to: %s\n' % bt.arg)

        if module.search_one('organization'):
            fd.write('  organization :%s\n' % module.search_one('organization').arg)

        if module.search_one('contact'):
            fd.write('  contact :%s\n' % module.search_one('contact').arg)

        if module.search_one('revision'):
            fd.write('  revision :%s\n' % module.search_one('revision').arg)
        now = datetime.datetime.now()
        fd.write('UML generated: %s\n' % now.strftime("%Y-%m-%d %H:%M"))
        fd.write('end note \n')


        # print imported modules as packages
        imports = module.search('import')
        for i in imports:
            #pre = self.make_plantuml_keyword((i.search_one('prefix')).arg)
            #pkg = self.make_plantuml_keyword(i.arg)
            #fd.write('package %s.%s \n' %(pre, pkg))
            pre = i.search_one('prefix').arg
            pkg = i.arg
            fd.write('package \"%s:%s\" as %s_%s \n' %(pre, pkg, self.make_plantuml_keyword(pre), self.make_plantuml_keyword(pkg)))
            
            # search for augments and place them in correct package
            augments = module.search('augment')
            if augments:
                # remove duplicates
                augments = list(set(augments))
            for a in augments:
                a_pre = self.first_component(a.arg)
                a_pkg = ''
                if (pre == a_pre): # augments element in this module, ugly trick use _suffix here
                        fd.write('class \"%s\" as %s \n' %(a.arg, self.make_plantuml_keyword(a.arg)))
            fd.write('end package \n')

        bt = module.search_one('belongs-to')
        if bt is not None:
            fd.write('package %s\n' % bt.arg)
            self.post_strings.append('end package \n')


        # pkg name for this module
        #this_pkg = self.make_plantuml_keyword(module.search_one('prefix').arg) + '.' + self.make_plantuml_keyword(module.arg)
        pkg = module.arg

        # print package for this module and a class to represent module (notifs and rpcs)
        fd.write('package \"%s:%s\" as %s_%s \n' %(self.thismod_prefix, pkg, self.make_plantuml_keyword(self.thismod_prefix), self.make_plantuml_keyword(pkg)))
        imports = module.search('import')
        for i in imports:
            mod = self.make_plantuml_keyword(i.search_one('prefix').arg) + '_' + self.make_plantuml_keyword(i.arg)
            fd.write('%s +-- %s_%s\n' %(mod,self.make_plantuml_keyword(self.thismod_prefix), self.make_plantuml_keyword(pkg)))
        fd.write('class \"%s\" as %s << (M, #33CCFF) module>> \n' %(self.full_display_path(module), self.full_path(module)))

    def emit_module_footer(self, module, fd): 
        fd.write('end package \n')
        fd.write('@enduml \n')

    def annotate_node(self, node, note, fd):
        if self.ctx_annotations:
            fd.write('note bottom of %s\n' %(self.full_path(node)) )
            fd.write('%s\n' %note)
            fd.write('end note \n')


    def emit_container(self, parent, node, fd):
        if (not self.ctx_filterfile):
        # and ((not self.ctx_usefilterfile) or (self.ctx_usefilterfile and (self.full_path(node) in self.filterpaths))):        
            fd.write('class \"%s\" as  %s <<container>> \n' %(self.full_display_path(node), self.full_path(node)))
            fd.write('%s *-- \"1\" %s \n' %(self.full_path(parent), self.full_path(node)))
        else:
            fd.write(self.full_path(node) + '\n')



    def emit_list(self, parent, node, fd):
        if (not self.ctx_filterfile):                
            fd.write('class \"%s\" as %s << (L, #FF7700) list>> \n' %(self.full_display_path(node), self.full_path(node)))         
            minelem = '0'
            maxelem = 'N'
            oby = ''
            mi = node.search_one('min-elements')
            if mi is not None:
               minelem = mi.arg
            ma = node.search_one('max-elements')
            if ma is not None:
               maxelem = ma.arg
            orderedby = node.search_one('ordered-by')
            if orderedby is not None:
                oby = ': ordered-by : ' + orderedby.arg
            fd.write('%s *-- \"%s..%s\" %s %s\n' %(self.full_path(parent), minelem, maxelem, self.full_path(node), oby))
        else:
            fd.write(self.full_path(node) + '\n')

    def emit_feature(self, parent, feature, fd):
             fd.write('%s : %s \n' %(self.full_path(parent), 'feature : ' + self.make_plantuml_keyword(feature.arg)) )

    def emit_deviation(self, parent, feature, fd):
             fd.write('%s : %s \n' %(self.full_path(parent), 'deviation : ' + self.make_plantuml_keyword(feature.arg)) )

    def emit_action(self, parent, action, fd):
             fd.write('%s : %s(' %(self.full_path(parent), action.arg) )
             # pretty ugly, but unlike for rpc and notifs we do not want to unfold a complete UML structure
             # rather a in out param list
             for params in action.substmts:
                 if params.keyword == 'input':
                     inputs = params.search('leaf')
                     inputs += params.search('leaf-list')
                     inputs += params.search('list')
                     inputs += params.search('container')
                     inputs += params.search('anyxml')
                     inputs += params.search('uses')
                     # inputs = root_elems(params)
                     for i in inputs:
                         fd.write(' in: %s' %(self.make_plantuml_keyword(i.arg)) )
                 if params.keyword == 'output':
                     outputs = params.search('leaf')
                     outputs += params.search('leaf-list')
                     outputs += params.search('list')
                     outputs += params.search('container')
                     outputs += params.search('anyxml')
                     outputs += params.search('uses')
                     # outputs = root_elems(params)
                     for o in outputs:
                         fd.write(' out: %s' %(self.make_plantuml_keyword(o.arg)) )
             fd.write(')\n')

             for params in action.substmts:
                 use = params.search('uses')
                 for u in use:
                     self.emit_uses(parent, u)
                    # fd.write('%s --> %s : uses \n' %(full_path(parent), full_path(u)))
                    # p = full_path(parent);
                    # us =  make_plantuml_keyword(u.arg);
                    # uses.append([p,us]);

    def emit_typedef(self, m, t, fd):
        e = t.search_one('type')
        if e.arg == 'enumeration':
                # enum_name = self.full_path(t, False)
                fd.write('enum \"%s\" as %s\n' %(t.arg, self.full_path(t)))
                for enums in e.substmts[:3]:
                     fd.write('%s : %s \n' %(self.full_path(t), enums.arg))
                if (len(e.substmts) > 3):
                     fd.write('%s : %s \n' %(self.full_path(t), "..."))
        else:
                fd.write('class \"%s\" as %s << (T, YellowGreen) typedef>>\n' %(t.arg, self.make_plantuml_keyword(t.arg)))
                fd.write('%s : %s\n' %(self.make_plantuml_keyword(t.arg), self.typestring(t)))


    def emit_notif(self, module, stmt,fd):
        # ALTERNATIVE 1
        # notif as class stereotype, ugly, but easier to layout params
        fd.write('class \"%s\" as %s << (N,#00D1B2) notification>> \n' %(self.full_display_path(stmt), self.full_path(stmt)))
        fd.write('%s -- %s : notification \n' %(self.make_plantuml_keyword(module.arg), self.full_path(stmt)))
        for params in stmt.substmts:
                self.emit_child_stmt(stmt, params, fd)

        # ALTERNATIVE 2
        # notif as oper, better, but hard to layout params
        #fd.write('%s : notif:%s()\n' %(make_plantuml_keyword(module), make_plantuml_keyword(stmt.arg)) )
        #for params in stmt.substmts:
        #        emit_child_stmt(stmt, params, fd)

    def emit_uses(self, parent, node):
        p = self.full_path(parent)
        u =  self.make_plantuml_keyword(node.arg)
        # sys.stderr.write('%s %s \n'%(p,u))
        self.uses.append([p,u])
        self.uses_as_string[u] = node.arg

    def emit_grouping(self, module, stmt, fd, glob = 'False'):
        if (not self.ctx_filterfile):                
            self.groupings[self.make_plantuml_keyword(stmt.arg)] = (self.full_path(stmt));
            if (glob == True): # indicate grouping visible outside module
                fd.write('class \"%s\" as %s <<(G,Lime) grouping>> \n' %(self.full_display_path(stmt), self.full_path(stmt)))
            else:
                fd.write('class \"%s\" as %s <<(G,Red) grouping>> \n' %(self.full_display_path(stmt), self.full_path(stmt)))
            sys.stderr.write('emit grouping : %s\n' %(self.full_path(stmt)))
            # Groupings are not really part of the schema tree
            # fd.write('%s --  %s \n' %(self.full_path(module), self.full_path(stmt)))
        else:
            fd.write(self.full_path(stmt) + '\n')
        for children in stmt.substmts:
                self.emit_child_stmt(stmt, children, fd)

    def attribs(self, node):
        # use UML attribute properties for various YANG leaf elements
        attribs = '';

        default = node.search_one('default')
        if default is not None:
            attribs = attribs + ' = ' + default.arg +' '

        mandatory =  node.search_one('mandatory')
        if mandatory is not None:
            if mandatory.arg == 'true':
                attribs = attribs + ' {mandatory}'

        units = node.search_one('units')
        if units is not None:
            attribs = attribs + ' {' + units.arg + '}'

        orderedby = node.search_one('ordered-by)')
        if orderedby is not None:
            attribs = attribs + ' {ordered-by:' + orderedby.arg + '}' 

        status = node.search_one('status')
        if status is not None:
            attribs = attribs + ' {' + status.arg + '}'

        config = node.search_one('config')
        if config is not None:
            attribs = attribs + ' {Config : ' + config.arg + '}'


        return attribs

    def typestring(self, node):
        t = node.search_one('type')
        s = t.arg
        if t.arg == 'enumeration':
            s = s + ' : {'
            for enums in t.substmts[:3]:
                s = s + enums.arg + ','
            if len(t.substmts) > 3:
                s = s + "..."
            s = s + '}'
        elif t.arg == 'leafref':
            # sys.stderr.write('in leafref \n')
            s = s + ' : '
            p = t.search_one('path')
            if p is not None:
                s = s + p.arg
                inthismodule, n = self.find_target_node(p)
                if (n is not None) and (inthismodule):
                    # sys.stderr.write('leafref %s : target %s \n' %(p.arg, full_path(n)))
                    # sys.stderr.write('in this module %s : \n' %inthismodule)
                    self.leafrefs.append(self.full_path(node.parent) + '-->' + self.full_path(n.parent) + ': ' + node.arg + '\n')
                elif ((n is not None) and (not inthismodule)):
                    # sys.stderr.write('in this module %s : \n' %inthismodule)
                    self.leafrefs.append('class \"%s\" as %s << (L, #FF7700) list>>\n' %(self.full_display_path(n.parent), self.full_path(n.parent)))                        
                    self.leafrefs.append(self.full_path(node.parent) + '-->' + self.full_path(n.parent) + ': ' + node.arg + '\n')
                    
        typerange = t.search_one('range')
        if typerange is not None:
            s = s + ' [' + typerange.arg + ']'  
        length = t.search_one('length')
        if length is not None:
            s = s + ' {length = ' + length.arg + '}'  

        pattern = t.search_one('pattern')
        if pattern is not None: # truncate long patterns
            s = s + ' {pattern = ' + pattern.arg[:20]
            if len(pattern.arg) < 20:
                s = s + '}'
            else:
                s = s + '...}'

        return s

    def emit_must_leaf(self, parent, node, fd):
        annot = ''
        must = node.search('must')
        if len(must) > 0 :
            annot = "Must (" + node.arg + "):\n"
            for m in must:
                annot = annot + m.arg + '\n'

        when = node.search_one('when')
        if when is not None:
            annot = annot +  "When (" + node.arg + "):\n" + when.arg + '\n'

        if annot != '':
            self.annotate_node(parent, annot, fd) 


    def emit_must(self, parent, node, fd):
        self.annotate_node(parent, "Must:\n" + node.arg, fd) 

    def yang_roots(self, stmt):
        global root_elems
        elems = ()
        for r in root_elems:
            elems += stmt.search(r)
        return elems

    def full_display_path(self, stmt):
        pathsep = "/"
        path = stmt.arg
        if stmt.keyword != 'grouping':
            if self.ctx_fullpath:
                while stmt.parent is not None:
                    stmt = stmt.parent
                    if stmt.arg is not None:
                        path = stmt.arg + pathsep + path
        return path

    def full_path(self, stmt):
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
        return self.make_plantuml_keyword(path)

    def last_component(self, s):
        last = s[s.rfind("/")+1:]
        return self.make_plantuml_keyword(last)

    def next_tolast_component(self, s):
        if self.ctx_fullpath:
            return s[0:(s.rfind("_I_"))]
        else:
            return s

    def first_component(self, s):
        first = s[1:s.find(":")]
        return self.make_plantuml_keyword(first)

    def make_plantuml_keyword(self, s):
        #plantuml does not like -/: in identifiers, fixed :)
        s = s.replace('-', '_')
        s = s.replace('/', '_')
        s = s.replace(':', '_')
        return s


    def find_target_node(self, stmt):
        inthismod = True;
        if stmt.arg.startswith('/'):
            is_absolute = True
            arg = stmt.arg
        else:
            is_absolute = False
            arg = "/" + stmt.arg
        # parse the path into a list of two-tuples of (prefix,identifier)
        path = [(m[1], m[2]) for m in syntax.re_schema_node_id_part.findall(arg)]
        # find the module of the first node in the path 
        (prefix, identifier) = path[0]
        if prefix == '':
            inthismod = True
        else:
            inthismod = (prefix == self.thismod_prefix);
        # sys.stderr.write("prefix for %s : %s \n" %(path, prefix))
        module = statements.prefix_to_module(stmt.i_module, prefix,
                                             stmt.pos, self._ctx.errors)
        if module is None:
            # error is reported by prefix_to_module
            return inthismod, None
        if is_absolute:
            # find the first node
            node = statements.search_data_keyword_child(module.i_children,
                                                        module.i_modulename,
                                                        identifier)
            if node is None: 
                # check all our submodules
                for inc in module.search('include'):
                    submod = ctx.get_module(inc.arg)
                    if submod is not None:
                        node = statements.search_data_keyword_child(
                            submod.i_children,
                            submod.i_modulename,
                            identifier)
                        if node is not None:
                            break
                if node is None:
                    err_add(self._ctx.errors, stmt.pos, 'NODE_NOT_FOUND',
                            (module.arg, identifier))
                    return inthismod, None
            path = path[1:]
        else:
            if hasattr(stmt.parent, 'i_annotate_node'):
                node = stmt.parent.i_annotate_node
            else:
                err_add(self._ctx.errors, stmt.pos, 'BAD_ANNOTATE', ())
                return inthismod, None

        # then recurse down the path
        for (prefix, identifier) in path:
            module = statements.prefix_to_module(stmt.i_module, prefix, stmt.pos,
                                                 self._ctx.errors)
            if module is None:
                return None
            if hasattr(node, 'i_children'):
                children = node.i_children
            else:
                children = []
            child = statements.search_data_keyword_child(children,
                                                         module.i_modulename,
                                                         identifier)
            if child is None:
                err_add(self._ctx.errors, stmt.pos, 'NODE_NOT_FOUND',
                        (module.arg, identifier))
                return inthismod, None
            node = child

        stmt.i_annotate_node = node
        return inthismod, node

    def post_process(self, fd):
        if self.ctx_uses:
            for p,u in self.uses:
                try:
                    fd.write('%s --> %s : uses \n' %(p, self.groupings[u]))
                except KeyError: # grouping in imported module, TODO correct paths
                    # sys.stderr.write('key-error %s %s\n' %(p,u))
                    fd.write('class \"%s\" as %s << (G,orchid) grouping>>\n' %(self.uses_as_string[u], self.make_plantuml_keyword(self.uses_as_string[u])))
                    fd.write('%s --> %s : uses \n' %(p, self.make_plantuml_keyword(self.uses_as_string[u])))
        if self.ctx_leafrefs: # TODO correct paths for external leafrefs
            for l in self.leafrefs:
                fd.write(l)
        for s in self.post_strings:
                fd.write(s)
        
