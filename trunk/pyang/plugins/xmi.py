
import optparse
import sys
import re
import string

from pyang import plugin
from pyang import statements

def pyang_plugin_init():
    plugin.register_plugin(XMIPlugin())

class XMIPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['xmi'] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--xmi-path",
                                 dest="xmi_tree_path",
                                 help="Subtree to print"),
            optparse.make_option("--xmi-no-assoc-names",
                                 dest="xmi_no_assoc_names",
                                 action="store_true",
                                 default = False,
                                 help="Do not print names for associations"),

            ]
        g = optparser.add_option_group("XMI output specific options")
        g.add_options(optlist)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        if ctx.opts.xmi_tree_path is not None:
            path = string.split(ctx.opts.xmi_tree_path, '/')
            if path[0] == '':
                path = path[1:]
        else:
            path = None

        print_xmi_header(modules, fd, path, ctx)
        emit_yang_xmi(fd, ctx)
        emit_modules_xmi(modules, fd, path, ctx)
        print_xmi_footer(modules, fd, path, ctx)

def emit_yang_xmi(fd, ctx):
    fd.write("<UML:Model xmi.id = \'yang' name = \'yang\' isSpecification = \'false\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\'>\n")
    fd.write("<UML:Namespace.ownedElement>\n")

    # YANG stereotypes, container, list, ....
    print_stereotypes(fd, ctx)

    # YANG specifics, config, mandatory, ...
    print_tag_definitions(fd, ctx)

    fd.write("</UML:Namespace.ownedElement>\n")
    fd.write("</UML:Model>\n")



def print_xmi_header(modules, fd, path, ctx):
    fd.write("<?xml version = '1.0' encoding = 'UTF-8' ?>")
    fd.write("<XMI xmi.version = '1.2' xmlns:UML = 'org.omg.xmi.namespace.UML' timestamp = 'Tue May 15 07:06:45 CEST 2012'>")
    fd.write("<XMI.header>")
    fd.write("<XMI.documentation>")
    fd.write("<XMI.exporter> pyang -f xmi</XMI.exporter>")
    fd.write("<XMI.exporterVersion> 0.1 </XMI.exporterVersion>")
    fd.write("</XMI.documentation>")
    fd.write("<XMI.metamodel xmi.name=\"UML\" xmi.version=\"1.4\"/>")
    fd.write("</XMI.header>")
    fd.write("<XMI.content>")

def print_xmi_footer(modules, fd, path, ctx):
    fd.write("</XMI.content>")
    fd.write("</XMI>")



def print_module_info(module, fd, ctx):
    authorstring = ""
    if module.search_one('organization'):
        authorstring = module.search_one('organization').arg
        authorstring = fix_xml_string(authorstring, ctx)


    if module.search_one('contact'):
        authorstring = authorstring + ' ' + module.search_one('contact').arg
        authorstring = fix_xml_string(authorstring, ctx)

    print_tag(module, 'author', authorstring, fd, ctx)

    print_description(module, fd, ctx)

    if module.search_one('revision'):
        revstring = module.search_one('revision').arg
        print_tag(module, 'version', revstring, fd, ctx)


def print_stereotypes(fd, ctx):
    # xmi.id, name
    stereotypes = [("yang:container", "container"), ("yang:list", "list"), ("yang:case", "case"), ("yang:choice", "choice"), ("yang:identity", "identity"), ("yang:notification", "notification"), ("yang:rpc", "rpc"), ("yang:input", "input"), ("yang:output", "output"), ("tailf:action", "action")]
    for st in stereotypes:
        fd.write("<UML:Stereotype xmi.id = \'%s\' name=\'%s\' \n" %(st[0], st[1]))
        fd.write("isSpecification = 'false' isRoot = 'false' isLeaf = 'false' isAbstract = 'false'> \n")
        fd.write("<UML:Stereotype.baseClass>Class</UML:Stereotype.baseClass> \n")
        fd.write(" </UML:Stereotype> \n")

def print_tag_definitions(fd, ctx):
   # xmi.id, name
   tags = [('yang:description', 'documentation'), ('yang:config', 'config'), ('yang:mandatory', 'mandatory'), ('yang:status', 'status'), ('yang:path', 'path'), ('yang:presence', 'presence'), ('yang:when', 'when'), ('yang:must', 'must'), ('yang:author', 'author'), ('yang:version', 'version'), ('yang:min-elements', 'min-elements'), ('yang:max-elements', 'max-elements'), ('yang:ordered-by', 'ordered-by'), ('yang:default','default'), ('yang:key', 'key')]
   for t in tags:
       fd.write("<UML:TagDefinition xmi.id = '%s' name = '%s' isSpecification = 'false'> \n" %(t[0], t[1]))
       fd.write("<UML:TagDefinition.multiplicity> \n")
       fd.write("<UML:Multiplicity xmi.id = '%s-multiplicity'> \n" %t[0])
       fd.write("<UML:Multiplicity.range> \n")
       fd.write("<UML:MultiplicityRange xmi.id = '%s-multiplicity-range' lower = '0' upper = '0'/> \n" %t[0])
       fd.write("</UML:Multiplicity.range> \n")
       fd.write("</UML:Multiplicity> \n")
       fd.write("</UML:TagDefinition.multiplicity> \n")
       fd.write("</UML:TagDefinition> \n")

def emit_modules_xmi(modules, fd, path, ctx):

    for module in modules:

        # module
        fd.write("<UML:Model xmi.id = \'%s\' name = \'%s\' isSpecification = \'false\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\'>\n" %(fullpath(module), module.arg))

        print_module_info(module, fd, ctx)
        fd.write("<UML:Namespace.ownedElement>\n")

        print_typedefs(module, fd, ctx)

        chs = [ch for ch in module.i_children]
        if path is not None and len(path) > 0:
            chs = [ch for ch in chs
                   if ch.arg == path[0]]
            path = path[1:]

        print_children(chs, module, fd, path, ctx)

        fd.write("</UML:Namespace.ownedElement>\n")
        fd.write("</UML:Model>\n")

def print_children(i_children, module, fd, path, ctx):
    for ch in i_children:
        print_node(module, ch, module, fd, path, ctx, 'true')

def iterate_children(parent, s, module, fd, path, ctx):
    if hasattr(s, 'i_children'):
       for ch in s.i_children:
           print_node(s, ch, module, fd, path, ctx)

def print_class_stuff(s, fd, ctx):
    print_description(s, fd, ctx)
    print_tags(s, fd, ctx)
    # We need to recurse children here to get closing class tag
    print_attributes(s, fd, ctx)
    print_actions(s,fd, ctx)
    close_class(s, fd, ctx)
    print_associations(s,fd, ctx)

def print_node(parent, s, module, fd, path, ctx, root='false'):

    # We have a UML class
    if (s.keyword == "container"):
        print_container(s, fd, ctx, root)
        print_class_stuff(s, fd, ctx)

        # Do not try to create relationship to module
        if (parent != module):
            presence = s.search_one("presence")
            if presence is not None:
                print_aggregation(parent, s, fd, "0", "1", ctx)
            else:
                print_aggregation(parent, s, fd, "1", "1", ctx)

        # Continue to find classes
        iterate_children(parent, s, module, fd, path, ctx)
    elif s.keyword == "list":
        print_list(s, fd, ctx, root)
        print_class_stuff(s, fd, ctx)

        # Do not try to create relationship to module
        if (parent != module):
            min = "0"
            max = "-1"
            m = s.search_one('min-elements')
            if m is not None:
               min = m.arg
            m = s.search_one('max-elements')
            if m is not None:
               max = m.arg

            # Seems as 1..m is represented as 1..-1 in xmi ?
            print_aggregation(parent, s, fd, min, max, ctx)

        # Continue to find classes
        iterate_children(parent, s, module, fd, path, ctx)

    elif s.keyword == 'choice':
        print_choice(s, fd, ctx)
        print_tags(s, fd, ctx)
        print_description(s, fd, ctx)
        close_class(s, fd, ctx)

        if (parent != module):
           print_aggregation(parent, s, fd, "1", "1", ctx)

        # Continue to find classes
        iterate_children(parent, s, module, fd, path, ctx)

    elif s.keyword == 'case':
        print_case(s,fd, ctx)
        print_class_stuff(s, fd, ctx)

        if (parent != module):
           print_aggregation(parent, s, fd, "0", "1", ctx)

        # Continue to find classes
        iterate_children(parent, s, module, fd, path, ctx)

    elif s.keyword == 'rpc':
        print_rpc(s,fd, ctx)
        print_description(s, fd, ctx)
        print_tags(s, fd, ctx)
        close_class(s, fd, ctx)

        iterate_children(parent, s, module, fd, path, ctx)

    elif s.keyword == 'notification':
        print_notification(s, fd, ctx)
        print_class_stuff(s, fd, ctx)

        iterate_children(parent, s, module, fd, path, ctx)

    elif s.keyword in  ['input','output'] and (len(s.i_children) > 0):
        print_inout(parent, s, fd, ctx)
        print_class_stuff(s, fd, ctx)
        iterate_children(parent, s, module, fd, path, ctx)
        print_aggregation(parent, s, fd, "1", "1", ctx)

        # do not clutter the diagram with action details
        #elif s.keyword == ('tailf-common', 'action'):
        #print_action(s,fd, ctx)
        #close_class(s, fd, ctx)

        # iterate_children(parent, s, module, fd, path, ctx)
        # print_aggregation(parent, s, fd, "1", "1", ctx)

def close_class(s, fd, ctx):
    fd.write("</UML:Class>\n")

def print_attributes(s,fd, ctx):
    if hasattr(s, 'i_children'):
        for ch in s.i_children:
            if ch.keyword == "leaf":
                   print_leaf(ch, fd, ctx)
            elif ch.keyword == "leaf-list":
                   print_leaflist(ch, fd, ctx)

def print_actions(s,fd, ctx):
    if hasattr(s, 'i_children'):
        for ch in s.i_children:
            if ch.keyword == ('tailf-common', 'action'):
                print_action_operation(ch,fd, ctx)

def print_associations(s, fd, ctx):
    # find leafrefs and identityrefs

    if hasattr(s, 'i_children'):
        for ch in s.i_children:
            if hasattr(ch, 'i_leafref_ptr') and (ch.i_leafref_ptr is not None):
                to = ch.i_leafref_ptr[0]
                print_association(s, to.parent, ch, to, "leafref", fd, ctx)

def fix_xml_string(string, ctx):
        fixed = ''.join([x for x in string if ord(x) < 128])
        fixed = fixed.replace('<', '&lt;')
        fixed = fixed.replace('>', '&gt;')
        fixed = fixed.replace('\n', ' \\n')

        return fixed

def print_description(s, fd, ctx):
    descr = s.search_one('description')
    if descr is not None:
        descrstring = fix_xml_string(descr.arg, ctx)
    else:
        descrstring = "No YANG description";
    fd.write("<UML:ModelElement.taggedValue>")
    fd.write("<UML:TaggedValue xmi.id = 'tag-%s-description' isSpecification = 'false'> \n" %fullpath(s))
    fd.write("<UML:TaggedValue.dataValue>%s</UML:TaggedValue.dataValue> \n" %descrstring)
    fd.write("<UML:TaggedValue.type> \n")
    fd.write("<UML:TagDefinition xmi.idref = 'yang:description'/> \n")
    fd.write("</UML:TaggedValue.type> \n")
    fd.write("</UML:TaggedValue> \n")
    fd.write("</UML:ModelElement.taggedValue>")

def print_aggregation(parent, s, fd, lower, upper, ctx):
    fd.write("<UML:Association xmi.id = \'container-%s--%s\' \n" %(fullpath(parent), fullpath(s)))
    if ctx.opts.xmi_no_assoc_names:
        fd.write("isSpecification = \'false\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\'> \n")
    else:
        fd.write("name = \'container-%s-%s\' isSpecification = \'false\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\'> \n" %(parent.arg, s.arg))
    fd.write("<UML:Association.connection> \n")

    fd.write("<UML:AssociationEnd xmi.id = \'container-parent-%s--child-%s\' \n" %(fullpath(parent), fullpath(s)))
    fd.write("visibility = \'public\' isSpecification = \'false\' isNavigable = \'true\' ordering = \'unordered\' \n")
    fd.write("aggregation = \'aggregate\' targetScope = \'instance\' changeability = \'changeable\'> \n")
    fd.write("<UML:AssociationEnd.participant> \n")
    fd.write("<UML:Class xmi.idref = \'%s\'/> \n" %fullpath(parent))
    fd.write("</UML:AssociationEnd.participant> \n")
    fd.write("</UML:AssociationEnd> \n")

    fd.write("<UML:AssociationEnd xmi.id = \'container-child-%s--parent-%s\' \n" %(fullpath(s), fullpath(parent)))
    fd.write("visibility = \'public\' isSpecification = \'false\' isNavigable = \'true\' ordering = \'unordered\' \n")
    fd.write("aggregation = \'none\' targetScope = \'instance\' changeability = \'changeable\'> \n")
    fd.write("<UML:AssociationEnd.multiplicity> \n")
    fd.write("<UML:Multiplicity xmi.id = \'container-child-%s--parent-%s-multiplicity\'> \n" %(fullpath(s), fullpath(parent)))
    fd.write("<UML:Multiplicity.range>")
    fd.write("<UML:MultiplicityRange xmi.id = \'container-child-%s--parent-%s-multiplicity-range' lower = \'%s\' upper = \'%s\'/> \n"  %(fullpath(s), fullpath(parent), lower, upper))
    fd.write("</UML:Multiplicity.range> \n")
    fd.write("</UML:Multiplicity> \n")
    fd.write("</UML:AssociationEnd.multiplicity> \n")

    fd.write("<UML:AssociationEnd.participant> \n")
    fd.write("<UML:Class xmi.idref = \'%s\'/> \n" %fullpath(s))
    fd.write("</UML:AssociationEnd.participant> \n")
    fd.write("</UML:AssociationEnd> \n")

    fd.write("</UML:Association.connection> \n")

    fd.write("</UML:Association> \n")



def print_container(container, fd, ctx, root='false'):
    fd.write("<UML:Class xmi.id = \'%s\' name = \'%s\' " %(fullpath(container), container.arg))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'%s\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n" %root)
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'yang:container'/> \n")
    fd.write("</UML:ModelElement.stereotype> \n")

    #fd.write("</UML:Class>\n")


def print_list(list, fd, ctx, root='false'):
    fd.write("<UML:Class xmi.id = \'%s\' name = \'%s\' " %(fullpath(list), list.arg))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'%s\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n" %root)
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'yang:list'/> \n")
    fd.write("</UML:ModelElement.stereotype> \n")

def print_rpc(rpc, fd, ctx, root='false'):
    fd.write("<UML:Class xmi.id = \'%s\' name = \'%s\' " %(fullpath(rpc), rpc.arg))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'%s\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n" %root)
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'yang:rpc'/> \n")
    fd.write("</UML:ModelElement.stereotype> \n")

def print_action(action, fd, ctx, root='false'):
    fd.write("<UML:Class xmi.id = \'%s-action\' name = \'%s\' " %(fullpath(action), action.arg))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'%s\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n" %root)
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'tailf:action'/> \n")
    fd.write("</UML:ModelElement.stereotype> \n")

def print_notification(notification, fd, ctx, root='false'):
    fd.write("<UML:Class xmi.id = \'%s\' name = \'%s\' " %(fullpath(notification), notification.arg))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'%s\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n" %root)
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'yang:notification'/> \n")
    fd.write("</UML:ModelElement.stereotype> \n")

def print_inout(parent, s, fd, ctx, root='false'):
    fd.write("<UML:Class xmi.id = \'%s\' name = \'%s-%s\' " %(fullpath(s), parent.arg, s.keyword))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'%s\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n" %root)
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'yang:%s'/> \n" %s.keyword)
    fd.write("</UML:ModelElement.stereotype> \n")

def print_choice(choice, fd, ctx):
    fd.write("<UML:Class xmi.id = \'%s\' name = \'%s\' " %(fullpath(choice), choice.arg))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n")
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'yang:choice'/> \n")
    fd.write("</UML:ModelElement.stereotype> \n")

def print_case(case, fd, ctx):
    fd.write("<UML:Class xmi.id = \'%s\' name = \'%s\' " %(fullpath(case), case.arg))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n")
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'yang:case'/> \n")
    fd.write("</UML:ModelElement.stereotype> \n")


def print_leaf(leaf, fd, ctx):
    fd.write("<UML:Classifier.feature>")

    fd.write("<UML:Attribute xmi.id = \'%s\'\n" %fullpath(leaf))
    fd.write("name = \'%s\' visibility = \'public\' isSpecification = \'false\' ownerScope = \'instance\'\n" %leaf.arg)
    fd.write("changeability = \'changeable\' targetScope = \'instance\'>\n")

    fd.write("<UML:StructuralFeature.multiplicity>")
    fd.write("<UML:Multiplicity xmi.id = \'%s-multiplicity\'>\n"  %fullpath(leaf))
    fd.write("<UML:Multiplicity.range>\n")
    fd.write(" <UML:MultiplicityRange xmi.id = \'%s-multiplicity-range\' lower = \'1\' upper = \'1\'/>\n" %fullpath(leaf))
    fd.write("</UML:Multiplicity.range>\n </UML:Multiplicity> \n")
    fd.write("</UML:StructuralFeature.multiplicity>")

    fd.write("<UML:StructuralFeature.type>\n")
    fd.write("<UML:DataType name = \'%s\'/>\n" %get_typename(leaf))


    fd.write("</UML:StructuralFeature.type>")

    print_tags(leaf, fd, ctx)
    print_description(leaf,fd, ctx)

    fd.write("</UML:Attribute>")
    fd.write("</UML:Classifier.feature>")

def print_action_operation(action, fd, ctx):
    fd.write("<UML:Classifier.feature>")

    fd.write("<UML:Operation xmi.id = \'%s-operation\'\n" %fullpath(action))
    fd.write("name = \'%s\' visibility = \'public\' isSpecification = \'false\' ownerScope = \'instance\'\n" %action.arg)
    fd.write(" isQuery = \'false\' concurrency = \'sequential\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\'>\n")

    # fd.write("<UML:BehavioralFeature.parameter>\n")
    # fd.write("<UML:Parameter xmi.id = \'%s-return\' name = 'return' isSpecification = 'false' kind = 'return'/>" %fullpath(action))
    # fd.write("</UML:BehavioralFeature.parameter>")
    fd.write("</UML:Operation>")
    fd.write("</UML:Classifier.feature>")


def print_leaflist(leaf, fd, ctx):
    fd.write("<UML:Classifier.feature>")

    fd.write("<UML:Attribute xmi.id = \'%s\'\n" %fullpath(leaf))
    fd.write("name = \'%s[]\' visibility = \'public\' isSpecification = \'false\' ownerScope = \'instance\'\n" %leaf.arg)
    fd.write("changeability = \'changeable\' targetScope = \'instance\'>\n")

    fd.write("<UML:StructuralFeature.multiplicity>")
    fd.write("<UML:Multiplicity xmi.id = \'%s-multiplicity\'>\n"  %fullpath(leaf))
    fd.write("<UML:Multiplicity.range>\n")
    fd.write(" <UML:MultiplicityRange xmi.id = \'%s-multiplicity-range\' lower = \'0\' upper = \'-1\'/>\n" %fullpath(leaf))
    fd.write("</UML:Multiplicity.range>\n </UML:Multiplicity> \n")
    fd.write("</UML:StructuralFeature.multiplicity>")

    fd.write("<UML:StructuralFeature.type>\n")
    fd.write("<UML:DataType name = \'%s\'/>\n" %get_typename(leaf))
    fd.write("</UML:StructuralFeature.type>")

    print_description(leaf,fd, ctx)
    print_tags(leaf, fd, ctx)

    fd.write("</UML:Attribute>")
    fd.write("</UML:Classifier.feature>")



def print_association(fromclass, toclass, fromleaf, toleaf, association, fd, ctx):
    if ctx.opts.xmi_no_assoc_names:
        fd.write("<UML:Association xmi.id = '%s-from-%s-to-%s' isSpecification = 'false' isRoot = 'false' isLeaf = 'false' isAbstract = 'false'>\n" %(association, fullpath(fromleaf), fullpath(toleaf)))
    else:
        fd.write("<UML:Association xmi.id = '%s-from-%s-to-%s' name = '%s-%s-%s' isSpecification = 'false' isRoot = 'false' isLeaf = 'false' isAbstract = 'false'>\n" %(association, fullpath(fromleaf), fullpath(toleaf), association, fromclass.arg, toclass.arg))
    fd.write("<UML:Association.connection> \n")

    fd.write("<UML:AssociationEnd xmi.id = '%s-from-%s-to-%s-FROMLEAF' " %(association, fullpath(fromleaf), fullpath(toleaf)))
    fd.write("name = 'from' visibility = 'public' isSpecification = 'false' isNavigable = 'false' ")
    fd.write("ordering = 'unordered' aggregation = 'none' targetScope = 'instance' changeability = 'changeable'> \n")
    fd.write("<UML:AssociationEnd.participant> \n")
    fd.write("<UML:Class xmi.idref = '%s'/> \n" %(fullpath(fromclass)))
    fd.write("</UML:AssociationEnd.participant> \n")
    fd.write("</UML:AssociationEnd> \n")

    fd.write("<UML:AssociationEnd xmi.id = '%s-from-%s-to-%s-TOLEAF' "  %(association, fullpath(fromleaf), fullpath(toleaf)))
    fd.write("name = 'to' visibility = 'public' isSpecification = 'false' isNavigable = 'true' ")
    fd.write("ordering = 'unordered' aggregation = 'none' targetScope = 'instance' changeability = 'changeable'> \n")

    fd.write("<UML:AssociationEnd.multiplicity> \n")
    fd.write("<UML:Multiplicity xmi.id = '%s-from-%s-to%s-TO-multiplicity'> \n" %(association, fullpath(fromleaf), fullpath(toleaf)))
    fd.write("<UML:Multiplicity.range>")
    fd.write("<UML:MultiplicityRange xmi.id = '%s-from-%s-to%s-TO-multiplicity-range' lower = '1' upper = '1'/> \n" %(association, fullpath(fromleaf), fullpath(toleaf)))
    fd.write("</UML:Multiplicity.range> \n")
    fd.write("</UML:Multiplicity> \n")
    fd.write("</UML:AssociationEnd.multiplicity> \n")

    fd.write("<UML:AssociationEnd.participant> \n")
    fd.write("<UML:Class xmi.idref = '%s'/> \n " %fullpath(toclass))
    fd.write("</UML:AssociationEnd.participant> \n")
    fd.write("</UML:AssociationEnd> \n")
    fd.write("</UML:Association.connection> \n")
    fd.write("</UML:Association>\n")

def print_typedefs(module, fd, ctx):
    for stmt in module.substmts:
        if stmt.keyword == 'typedef':
            print_typedef(stmt,fd, ctx)
        elif stmt.keyword == 'identity':
            print_identity(stmt, fd, ctx)



def print_typedef(typedef, fd, ctx):
    e = typedef.search_one('type')
    if e.arg == 'enumeration': # We have an enumeration
        fd.write("<UML:Enumeration xmi.id = \'enumeration-%s\' " %typedef.arg)
        fd.write(" name = \'%s\' isSpecification = \'false\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\'> \n"  %typedef.arg)
        for enums in e.substmts:
            fd.write("<UML:Enumeration.literal> \n")
            fd.write("<UML:EnumerationLiteral xmi.id = 'typedef-%s-enum-%s-literal-%s' name = '%s' isSpecification = 'false'/> \n" %(typedef.arg, e.arg, enums.arg, enums.arg))
            fd.write("</UML:Enumeration.literal> \n")
        fd.write("</UML:Enumeration> \n")

    else: # We have a plain typedef
        fd.write("<UML:DataType xmi.id = \'typedef-%s \' \n" %typedef.arg)
        fd.write(" name = '%s' isSpecification = 'false' isRoot = 'false' isLeaf = 'false' isAbstract = 'false'/> \n" %typedef.arg)

def print_identity(s, fd, ctx):
    fd.write("<UML:Class xmi.id = \'%s-identity\' name = \'%s\' " %(s.arg, s.arg))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n")
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'yang:identity'/> \n")
    fd.write("</UML:ModelElement.stereotype> \n")
    fd.write("<UML:GeneralizableElement.generalization> \n")
    fd.write("<UML:Generalization xmi.idref = '%s-identity-generalization'/> \n" %s.arg)
    fd.write("</UML:GeneralizableElement.generalization> \n")
    fd.write("</UML:Class>")
    base = s.search_one('base')
    if base is not None:
            fd.write("<UML:Generalization xmi.id = \'%s-identity-generalization\' isSpecification = \'false\'> \n" %s.arg)
            fd.write("<UML:Generalization.child> \n")
            fd.write("<UML:Class xmi.idref = \'%s-identity\'/> \n" %s.arg)
            fd.write("</UML:Generalization.child> \n")
            fd.write("<UML:Generalization.parent> \n")
            fd.write("<UML:Class xmi.idref = \'%s-identity\'/>" %base.arg)
            fd.write("</UML:Generalization.parent> \n")
            fd.write("</UML:Generalization> \n")


def print_tags(s, fd, ctx):
    # YANG path
    print_tag(s, "path", fullpath(s), fd, ctx)

    simpletags = ['default', 'if-feature', 'when', 'presence', 'must', 'min-elements', 'max-elements', 'ordered-by']

    for tagstring in simpletags:
        tag = s.search_one(tagstring)
        if tag is not None:
            print_tag(s, tagstring, fix_xml_string(tag.arg, ctx), fd, ctx)

    # config ?
    config = "false"
    if s.i_config == True:
        config = "true"

    print_tag(s, "config", config, fd, ctx)

    # mandatory ?
    mandatory = "true"
    m = s.search_one('mandatory')
    if m is None or m.arg == 'false':
        mandatory = 'false'
    print_tag(s, "mandatory", mandatory, fd, ctx)

    # status ?
    stat = ""
    status = s.search_one('status')
    if status is None:
        stat =  "current"
    else:
        stat = status.arg
    print_tag(s, "status", stat, fd, ctx)

def print_tag(s, tagname, tagvalue, fd, ctx):
    fd.write("<UML:ModelElement.taggedValue>")
    fd.write("<UML:TaggedValue xmi.id = 'tag-%s-%s' isSpecification = 'false'> \n" %(fullpath(s), tagname))
    fd.write("<UML:TaggedValue.dataValue>%s</UML:TaggedValue.dataValue> \n" %tagvalue)
    fd.write("<UML:TaggedValue.type> \n")
    fd.write("<UML:TagDefinition xmi.idref = 'yang:%s'/> \n" %tagname)
    fd.write("</UML:TaggedValue.type> \n")
    fd.write("</UML:TaggedValue> \n")
    fd.write("</UML:ModelElement.taggedValue>")

def get_typename(s):
    t = s.search_one('type')
    if t is not None:
      s = t.arg
      # if t.arg == 'enumeration':
      #   s = s + ' : {'
      #   for enums in t.substmts[:10]:
      #       s = s + enums.arg + ','
      #   if len(t.substmts) > 3:
      #       s = s + "..."
      #   s = s + '}'
      # elif t.arg == 'leafref':
      #   s = s + ' : '
      #   p = t.search_one('path')
      #   if p is not None:
      #       s = s + p.arg
      return s


def fullpath(stmt):
        pathsep = "/"
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
