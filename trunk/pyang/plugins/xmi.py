
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
            optparse.make_option("--xmi-help",
                                 dest="tree_help",
                                 action="store_true",
                                 help="Print help on tree symbols and exit"),
            optparse.make_option("--xmi-path",
                                 dest="tree_path",
                                 help="Subtree to print"),
            ]
        g = optparser.add_option_group("XMI output specific options")
        g.add_options(optlist)

    def setup_ctx(self, ctx):
        if ctx.opts.tree_help:
            print_help()
            sys.exit(0)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        if ctx.opts.tree_path is not None:
            path = string.split(ctx.opts.tree_path, '/')
            if path[0] == '':
                path = path[1:]
        else:
            path = None

        print_xmi_header(modules, fd, path)
        emit_yang_xmi(fd)
        emit_modules_xmi(modules, fd, path)
        print_xmi_footer(modules, fd, path)
        

def print_help():
    print """
Prints a xmi file that can be imported to ArgoUML
"""


def emit_yang_xmi(fd):
    fd.write("<UML:Model xmi.id = \'yang' name = \'yang\' isSpecification = \'false\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\'>\n")
    fd.write("<UML:Namespace.ownedElement>\n")

    # YANG stereotypes, container, list, ....
    print_stereotypes(fd)

    # YANG specifics, config, mandatory, ...
    print_tag_definitions(fd)

    fd.write("</UML:Namespace.ownedElement>\n")
    fd.write("</UML:Model>\n")



def print_xmi_header(modules, fd, path):
    print """<?xml version = '1.0' encoding = 'UTF-8' ?>
<XMI xmi.version = '1.2' xmlns:UML = 'org.omg.xmi.namespace.UML' timestamp = 'Tue May 15 07:06:45 CEST 2012'>
  <XMI.header>
    <XMI.documentation>
      <XMI.exporter> pyang -f xmi</XMI.exporter>
      <XMI.exporterVersion> 0.1 </XMI.exporterVersion>
    </XMI.documentation>
    <XMI.metamodel xmi.name="UML" xmi.version="1.4"/>
  </XMI.header>
  <XMI.content>
""" 

def print_xmi_footer(modules, fd, path):
    print """
  </XMI.content>
</XMI>
"""


def print_module_info(module, fd):
    authorstring = ""
    if module.search_one('organization'):
        authorstring = module.search_one('organization').arg
        authorstring = fix_xml_string(authorstring)


    if module.search_one('contact'):
        authorstring = authorstring + ' ' + module.search_one('contact').arg
        authorstring = fix_xml_string(authorstring)

    print_tag(module, 'author', authorstring, fd)

    print_description(module, fd)        

    if module.search_one('revision'):
        revstring = module.search_one('revision').arg
        print_tag(module, 'version', revstring, fd)


def print_stereotypes(fd):
    # xmi.id, name
    stereotypes = [("yang:container", "container"), ("yang:list", "list"), ("yang:case", "case"), ("yang:choice", "choice"), ("yang:identity", "identity")]
    for st in stereotypes:
        fd.write("<UML:Stereotype xmi.id = \'%s\' name=\'%s\' \n" %(st[0], st[1]))
        fd.write("isSpecification = 'false' isRoot = 'false' isLeaf = 'false' isAbstract = 'false'> \n")
        fd.write("<UML:Stereotype.baseClass>Class</UML:Stereotype.baseClass> \n")
        fd.write(" </UML:Stereotype> \n")
        
def print_tag_definitions(fd):
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

def emit_modules_xmi(modules, fd, path):

    for module in modules:

        # module
        fd.write("<UML:Model xmi.id = \'%s\' name = \'%s\' isSpecification = \'false\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\'>\n" %(fullpath(module), module.arg))

        print_module_info(module, fd)
        fd.write("<UML:Namespace.ownedElement>\n")

        print_typedefs(module, fd)

        chs = [ch for ch in module.i_children
               if ch.keyword in statements.data_definition_keywords]
        if path is not None and len(path) > 0:
            chs = [ch for ch in chs
                   if ch.arg == path[0]]
            path = path[1:]

        print_children(chs, module, fd, path)
        fd.write("</UML:Namespace.ownedElement>\n")
        fd.write("</UML:Model>\n")

def print_children(i_children, module, fd, path):
    for ch in i_children:
        print_node(module, ch, module, fd, path, 'true')

def iterate_children(parent, s, module, fd, path):
    if hasattr(s, 'i_children'):
       for ch in s.i_children:
           print_node(s, ch, module, fd, path)

def print_class_stuff(s, fd):
        print_description(s, fd)            
        print_tags(s, fd)
        # We need to recurse children here to get closing class tag
        print_attributes(s, fd)
        close_class(s, fd)
        print_associations(s,fd)

    
def print_node(parent, s, module, fd, path, root='false'):

    # We have a UML class
    if (s.keyword == "container"):
        print_container(s, fd, root)
        print_class_stuff(s, fd)            

        # Do not try to create relationship to module
        if (parent != module):
            presence = s.search_one("presence")
            if presence is not None:
                print_aggregation(parent, s, fd, "0", "1")
            else:
                print_aggregation(parent, s, fd, "1", "1")                

        # Continue to find classes
        iterate_children(parent, s, module, fd, path)
        
    elif s.keyword == "list":
        print_list(s, fd, root)
        print_class_stuff(s, fd)            

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
            print_aggregation(parent, s, fd, min, max)

        # Continue to find classes
        iterate_children(parent, s, module, fd, path)

    elif s.keyword == 'choice':
        print_choice(s, fd)
        print_tags(s, fd)
        print_description(s, fd)
        close_class(s, fd)

        if (parent != module):
           print_aggregation(parent, s, fd, "1", "1")

        # Continue to find classes
        iterate_children(parent, s, module, fd, path)
        
    elif s.keyword == 'case':
        print_case(s,fd)
        print_class_stuff(s, fd)

        if (parent != module):
           print_aggregation(parent, s, fd, "0", "1")

        # Continue to find classes
        iterate_children(parent, s, module, fd, path)


def close_class(s, fd):
    fd.write("</UML:Class>\n")


def print_attributes(s,fd):
    if hasattr(s, 'i_children'):
        for ch in s.i_children:
            if ch.keyword == "leaf":
                   print_leaf(ch, fd)
            elif ch.keyword == "leaf-list":
                   print_leaflist(ch, fd)                   

def print_associations(s, fd):
    # find leafrefs and identityrefs

    if hasattr(s, 'i_children'):
        for ch in s.i_children:
            if hasattr(ch, 'i_leafref_ptr') and (ch.i_leafref_ptr is not None):
                to = ch.i_leafref_ptr[0]
                print_association(s, to.parent, "leafref", fd)
            elif hasattr(ch, 'i_identity') and (ch.i_identity is not None):
                print_association(s, to, "identityref", fd)

def fix_xml_string(string):
        fixed = ''.join([x for x in string if ord(x) < 128])
        fixed = fixed.replace('<', '&lt;')
        fixed = fixed.replace('>', '&gt;')
        fixed = fixed.replace('\n', ' \\n')

        return fixed

def print_description(s, fd):
    descr = s.search_one('description')
    if descr is not None:
        descrstring = fix_xml_string(descr.arg)
    else:
        descrstring = "No YANG description";
    fd.write("<UML:ModelElement.taggedValue>")
    fd.write("<UML:TaggedValue xmi.id = '%s-description' isSpecification = 'false'> \n" %fullpath(s))
    fd.write("<UML:TaggedValue.dataValue>%s</UML:TaggedValue.dataValue> \n" %descrstring)
    fd.write("<UML:TaggedValue.type> \n")
    fd.write("<UML:TagDefinition xmi.idref = 'yang:description'/> \n")
    fd.write("</UML:TaggedValue.type> \n")
    fd.write("</UML:TaggedValue> \n")
    fd.write("</UML:ModelElement.taggedValue>")

def print_aggregation(parent, s, fd, lower, upper):
    fd.write("<UML:Association xmi.id = \'container-%s--%s\' \n" %(fullpath(parent), fullpath(s)))
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



def print_container(container, fd, root='false'):
    fd.write("<UML:Class xmi.id = \'%s\' name = \'%s\' " %(fullpath(container), container.arg))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'%s\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n" %root)
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'yang:container'/> \n")
    fd.write("</UML:ModelElement.stereotype> \n")

    #fd.write("</UML:Class>\n")


def print_list(list, fd, root='false'):
    fd.write("<UML:Class xmi.id = \'%s\' name = \'%s\' " %(fullpath(list), list.arg))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'%s\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n" %root)
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'yang:list'/> \n")
    fd.write("</UML:ModelElement.stereotype> \n")

    #fd.write("</UML:Class>\n")

def print_choice(choice, fd):
    fd.write("<UML:Class xmi.id = \'%s\' name = \'%s\' " %(fullpath(choice), choice.arg))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n")
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'yang:choice'/> \n")
    fd.write("</UML:ModelElement.stereotype> \n")

def print_case(case, fd):
    fd.write("<UML:Class xmi.id = \'%s\' name = \'%s\' " %(fullpath(case), case.arg))
    fd.write("visibility = \'public\' isSpecification = \'false\' isRoot = \'false\' isLeaf = \'false\' isAbstract = \'false\' isActive = \'false\'>\n")
    fd.write("<UML:ModelElement.stereotype> \n")
    fd.write("<UML:Stereotype xmi.idref = 'yang:case'/> \n")
    fd.write("</UML:ModelElement.stereotype> \n")


def print_leaf(leaf, fd):
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

    print_tags(leaf, fd)

    fd.write("</UML:Attribute>")
    fd.write("</UML:Classifier.feature>")

def print_leaflist(leaf, fd):
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

    print_tags(leaf, fd)

    fd.write("</UML:Attribute>")
    fd.write("</UML:Classifier.feature>")



def print_association(fromclass, toclass, association, fd):
    fd.write("<UML:Association xmi.id = '%s-from-%s-to%s' name = '%s-%s-%s' isSpecification = 'false' isRoot = 'false' isLeaf = 'false' isAbstract = 'false'>\n" %(association, fullpath(fromclass), fullpath(toclass), association, fromclass.arg, toclass.arg))
    fd.write("<UML:Association.connection> \n")

    fd.write("<UML:AssociationEnd xmi.id = '%s-from-%s-to%s-FROM' " %(association, fullpath(fromclass), fullpath(toclass)))
    fd.write("name = 'from' visibility = 'public' isSpecification = 'false' isNavigable = 'false' ")
    fd.write("ordering = 'unordered' aggregation = 'none' targetScope = 'instance' changeability = 'changeable'> \n")
    fd.write("<UML:AssociationEnd.participant> \n")
    fd.write("<UML:Class xmi.idref = '%s'/> \n" %(fullpath(fromclass)))
    fd.write("</UML:AssociationEnd.participant> \n")
    fd.write("</UML:AssociationEnd> \n")

    fd.write("<UML:AssociationEnd xmi.id = '%s-from-%s-to%s-TO' "  %(association, fullpath(fromclass), fullpath(toclass)))
    fd.write("name = 'to' visibility = 'public' isSpecification = 'false' isNavigable = 'true' ")
    fd.write("ordering = 'unordered' aggregation = 'none' targetScope = 'instance' changeability = 'changeable'> \n")

    fd.write("<UML:AssociationEnd.multiplicity> \n")
    fd.write("<UML:Multiplicity xmi.id = '%s-from-%s-to%s-TO-multiplicity'> \n" %(association, fullpath(fromclass), fullpath(toclass)))
    fd.write("<UML:Multiplicity.range>")
    fd.write("<UML:MultiplicityRange xmi.id = '%s-from-%s-to%s-TO-multiplicity-range' lower = '1' upper = '1'/> \n" %(association, fullpath(fromclass), fullpath(toclass)))
    fd.write("</UML:Multiplicity.range> \n")
    fd.write("</UML:Multiplicity> \n")
    fd.write("</UML:AssociationEnd.multiplicity> \n")
              


    
    fd.write("<UML:AssociationEnd.participant> \n")
    fd.write("<UML:Class xmi.idref = '%s'/> \n " %fullpath(toclass))
    fd.write("</UML:AssociationEnd.participant> \n")
    fd.write("</UML:AssociationEnd> \n")
    fd.write("</UML:Association.connection> \n")
    fd.write("</UML:Association>\n")


def print_typedefs(module, fd):
    for stmt in module.substmts:
        if stmt.keyword == 'typedef':
            print_typedef(stmt,fd)
        elif stmt.keyword == 'identity':
            print_identity(stmt, fd)



def print_typedef(typedef, fd):
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

def print_identity(s, fd):
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


def print_tags(s, fd):
    # YANG path
    print_tag(s, "path", fullpath(s), fd)

    simpletags = ['default', 'if-feature', 'when', 'presence', 'must', 'min-elements', 'max-elements', 'ordered-by']

    for tagstring in simpletags:
        tag = s.search_one(tagstring)
        if tag is not None:
            print_tag(s, tagstring, fix_xml_string(tag.arg), fd)
        
    # default = s.search_one("default")
    # if default is not None:
    #     print_tag(s, "default", default.arg, fd)

    # feature = s.search_one("if-feature")
    # if feature is not None:
    #     print_tag(s, "feature", fix_xml_string(feature.arg), fd)

    # when = s.search_one("when")
    # if when is not None:
    #     print_tag(s, "when", when.arg, fd)

    # presence = s.search_one("presence")
    # if presence is not None:
    #     print_tag(s, "presence", presence.arg, fd)

    # must = s.search_one("must")
    # if must is not None:
    #     print_tag(s, "must", fix_xml_string(must.arg), fd)

    # m = s.search_one('min-elements')
    # if m is not None:
    #     print_tag(s, "min-elements", m.arg, fd)

    # m = s.search_one('max-elements')
    # if m is not None:
    #     print_tag(s, "max-elements", m.arg, fd)

    # o = s.search_one('ordered-by')
    # if o is not None:
    #     print_tag(s, "ordered-by", o.arg, fd)


    # config ?
    config = "false"
    if s.i_config == True:
        config = "true"

    print_tag(s, "config", config, fd)
    
    # mandatory ?
    mandatory = "true"
    m = s.search_one('mandatory')
    if m is None or m.arg == 'false':
        mandatory = 'false'
    print_tag(s, "mandatory", mandatory, fd)

    # status ?
    stat = ""
    status = s.search_one('status')
    if status is None:
        stat =  "current"
    else:
        stat = status.arg
    print_tag(s, "status", stat, fd)

def print_tag(s, tagname, tagvalue, fd):
    fd.write("<UML:ModelElement.taggedValue>")
    fd.write("<UML:TaggedValue xmi.id = '%s-%s' isSpecification = 'false'> \n" %(fullpath(s), tagname))
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
