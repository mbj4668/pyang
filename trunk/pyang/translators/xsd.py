"""XSD output plugin"""

from xml.sax.saxutils import quoteattr
from xml.sax.saxutils import escape

import optparse
import re
import copy
import sys

import pyang
from pyang import plugin
from pyang import util

yang_to_xsd_types = \
  {'int8':'byte',
   'int16':'short',
   'int32':'int',
   'int64':'long',
   'uint8':'unsignedByte',
   'uint16':'unsignedShort',
   'uint32':'unsignedInt',
   'uint64':'unsignedLong',
   'float32':'float',
   'float64':'double',
   'string':'string',
   'boolean':'boolean',
   # enumeration is handled separately
   # bits is handled separately
   'binary':'base64Binary',
   'keyref':'string',
   'instance-identifier':'string',
   # empty is handled separately
   # union is handled separately
   }

    # keyword             argument-name  yin-element xsd-appinfo
yang_keywords = \
    {'anyxml':           ('name',        False,      False),
     'argument':         ('name',        False,      False),
     'augment':          ('target-node', False,      False),
     'belongs-to':       ('module',      False,      True),
     'bit':              ('name',        False,      False),
     'case':             ('name',        False,      False),
     'choice':           ('name',        False,      False),
     'config':           ('value',       False,      True),
     'contact':          ('info',        True,       True),
     'container':        ('name',        False,      False),
     'default':          ('value',       False,      True),
     'description':      ('text',        True,       False),
     'enum':             ('name',        False,      False),
     'error-app-tag':    ('value',       False,      True),
     'error-message':    ('value',       True,       True),
     'extension':        ('name',        False,      False),
     'grouping':         ('name',        False,      False),
     'import':           ('module',      False,      True),
     'include':          ('module',      False,      True),
     'input':            (None,          None,       False),
     'key':              ('value',       False,      False),
     'leaf':             ('name',        False,      False),
     'leaf-list':        ('name',        False,      False),
     'length':           ('value',       False,      False),
     'list':             ('name',        False,      False),
     'mandatory':        ('value',       False,      True),
     'max-elements':     ('value',       False,      True),
     'min-elements':     ('value',       False,      True),
     'module':           ('name',        False,      False),
     'must':             ('condition',   False,      True),
     'namespace':        ('uri',         False,      False),
     'notification':     ('name',        False,      False),
     'ordered-by':       ('value',       False,      True),
     'organization':     ('info',        True,       True),
     'output':           (None,          None,       False),
     'path':             ('value',       False,      False),
     'pattern':          ('value',       False,      False),
     'position':         ('value',       False,      False),
     'presence':         ('value',       False,      False),
     'prefix':           ('value',       False,      True),
     'range':            ('value',       False,      False),
     'reference':        ('info',        False,      True),
     'revision':         ('date',        False,      True),
     'rpc':              ('name',        False,      False),
     'status':           ('value',       False,      True),
     'submodule':        ('name',        False,      False),
     'type':             ('name',        False,      False),
     'typedef':          ('name',        False,      False),
     'unique':           ('tag',         False,      False),
     'units':            ('name',        False,      True),
     'uses':             ('name',        False,      False),
     'value':            ('value',       False,      False),
     'when':             ('condition',   False,      True),
     'yang-version':     ('value',       False,      True),
     'yin-element':      ('value',       False,      False),
     }

def pyang_plugin_init():
    plugin.register_plugin(XSDPlugin())

class XSDPlugin(plugin.PyangPlugin):
    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--xsd-no-appinfo",
                                 dest="xsd_no_appinfo",
                                 action="store_true",
                                 help="Do not print YANG specific appinfo"),
            optparse.make_option("--xsd-no-imports",
                                 dest="xsd_no_imports",
                                 action="store_true",
                                 help="Do not generate any xs:imports"),
            optparse.make_option("--xsd-break-pattern",
                                 dest="xsd_break_pattern",
                                 action="store_true",
                                 help="Break XSD pattern so that they fit "
                                      "into RFCs"),
            optparse.make_option("--xsd-no-lecture",
                                 dest="xsd_no_lecture",
                                 action="store_true",
                                 help="Do not generate the lecture about "
                                      "how the XSD can be used")
            ]
        g = optparser.add_option_group("XSD output specific options")
        g.add_options(optlist)
    def add_output_format(self, fmts):
        fmts['xsd'] = self
    def setup_context(self, ctx):
        ctx.submodule_expansion = False        
    def emit(self, ctx, module, fd):
        # cannot do XSD unless everything is ok for our module
        for (epos, etag, eargs) in ctx.errors:
            if epos.module_name == module.name:
                print >> sys.stderr, "XSD translation needs a valid module"
                sys.exit(1)
        # we also need to have all other modules found
        for pre in module.i_prefixes:
            modname = module.i_prefixes[pre]
            mod = ctx.modules[modname]
            if mod == None:
                print >> sys.stderr, ("cannot find module %s, needed by XSD"
                                      " translation" % modname)
                sys.exit(1)
            
        emit_xsd(ctx, module, fd)

class DummyFD(object):
    def write(self, s):
        pass


def find_locally_defined_typedefs(ctx, module):
    for c in module.typedef:
        c.i_xsd_name = c.name
    for inc in module.include:
        m = ctx.modules[inc.arg]
        for c in m.typedef:
            c.i_xsd_name = c.name

    def gen_name(name, name_list):
        tname = name
        i = 0
        while util.attrsearch(tname, 'i_xsd_name', name_list):
            i = i + 1
            tname = name + '_' + str(i)
        return tname
            
    def add_typedef(obj):
        if 'typedef' in obj.__dict__:
            for t in obj.typedef:
                t.i_xsd_name = gen_name(t.name, module.typedef + \
                                        module.i_local_typedefs)
                module.i_local_typedefs.append(t)
        if 'children' in obj.__dict__:
            for c in obj.children:
                add_typedef(c)
        if 'grouping' in obj.__dict__:
            for c in obj.grouping:
                add_typedef(c)
    for c in module.children + module.augment + module.grouping:
        add_typedef(c)

def emit_xsd(ctx, module, fd):
    if module.i_is_submodule:
        parent_modulename = module.belongs_to.arg
        ctx.search_module(module.belongs_to.pos, modulename=parent_modulename)
        parent_module = ctx.modules[parent_modulename]
        if parent_module != None:
            module.i_namespace = parent_module.namespace.arg
            module.i_prefix = parent_module.prefix.arg
        else:
            print >> sys.stderr, ("cannot find module %s, needed by XSD"
                                  " translation" % parent_modulename)
            sys.exit(1)
    else:
        module.i_namespace = module.namespace.arg
        module.i_prefix = module.prefix.arg

    find_locally_defined_typedefs(ctx, module)

    # first pass, which might generate new imports
    ctx.i_pass = 'first'
    dummyfd = DummyFD()
    xsd_print_children(ctx, module, dummyfd, module.i_expanded_children,
                       '  ', [])
    for c in module.typedef:
        xsd_print_simple_type(ctx, module, dummyfd, '  ', c.type, '', None)

    prefixes = [module.i_prefix] + [p for p in module.i_prefixes]
    if module.i_prefix in ['xs', 'yin', 'nc', 'ncn']:
        i = 0
        pre = "p" + str(i)
        while pre in prefixes:
            i = i + 1
            pre = "p" + str(i)
        prefixes.append(pre)
        module.i_prefix = pre
        
    has_rpc = False
    has_notifications = False
    for c in module.children:
        if c.keyword == 'notification':
            has_notifications = True
        elif c.keyword == 'rpc':
            has_rpc = True

    fd.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    fd.write('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"\n')
    if ctx.opts.xsd_no_appinfo != True:
        fd.write('           ' \
                       'xmlns:yin="urn:ietf:params:xml:schema:yang:yin:1"\n')
    if has_rpc == True:
        fd.write('           ' \
                       'xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"\n')
    if has_notifications == True:
        fd.write('           xmlns:ncn="urn:ietf:params:xml:ns:' \
                       'netconf:notification:1.0"\n')
    fd.write('           targetNamespace="%s"\n' % module.i_namespace)
    fd.write('           xmlns="%s"\n' % module.i_namespace)
    fd.write('           xmlns:%s="%s"\n' % \
                   (module.i_prefix, module.i_namespace))
    fd.write('           elementFormDefault="qualified"\n')
    fd.write('           attributeFormDefault="unqualified"\n')
    if len(module.revision) > 0:
        fd.write('           version="%s"\n' % module.revision[0].date)
    fd.write('           xml:lang="en"')
    for pre in module.i_prefixes:
        modname = module.i_prefixes[pre]
        mod = ctx.modules[modname]
        if pre in ['xs', 'yin', 'nc', 'ncn']:
            # someone uses one of our prefixes
            # generate a new prefix for that module
            i = 0
            pre = "p" + i
            while pre in prefixes:
                i = i + 1
                pre = "p" + i
            prefixes.append(pre)
        mod.i_prefix = pre
        uri = mod.namespace.arg
        fd.write('\n           xmlns:' + pre + '=' + quoteattr(uri))
    fd.write('>\n\n')
    
    if ctx.opts.xsd_no_imports != True:
        imports = module.import_ + module.i_gen_import
        for x in imports:
            mod = ctx.modules[x.modulename]
            uri = mod.namespace.arg
            fd.write('  <xs:import namespace="%s"\n' \
                     '             schemaLocation="%s.xsd"/>\n' %
                       (uri, x.modulename))
        if has_rpc:
            fd.write('  <xs:import\n')
            fd.write('     namespace=' \
                           '"urn:ietf:params:xml:ns:netconf:base:1.0"\n')
            fd.write('     schemaLocation="http://www.iana.org/assignments/' \
                           'xml-registry/schema/netconf.xsd"/>')
        if has_notifications:
            fd.write('  <xs:import\n')
            fd.write('     namespace="urn:ietf:params:xml:ns:netconf:' \
                           'notification:1.0"\n')
# FIME: not yet published!  use a local copy for now.
            fd.write('      schemaLocation="notification.xsd"/>')
#            fd.write('     schemaLocation="http://www.iana.org/assignments/' +
#                   'xml-registry/schema/notification.xsd"/>')
        if len(imports) > 0 or has_rpc or has_notifications:
            fd.write('\n')

    for inc in module.include:
        fd.write('  <xs:include schemaLocation="%s.xsd"/>\n' % inc.modulename)

    if ctx.opts.xsd_no_lecture != True:
        fd.write('  <xs:annotation>\n')
        fd.write('    <xs:documentation>\n')
        fd.write('      This schema was generated from the YANG module %s\n' % \
                     module.name)
        fd.write('      by pyang version %s.\n' % pyang.__version__)
        fd.write('\n')
        fd.write('      The schema describes an instance document consisting\n')
        fd.write('      of the entire configuration data store, operational\n')
        fd.write('      data, rpc operations, and notifications.\n')
        fd.write('      This schema can thus NOT be used as-is to\n')
        fd.write('      validate NETCONF PDUs.\n')
        fd.write('    </xs:documentation>\n')
        fd.write('  </xs:annotation>\n\n')
        
    xsd_print_annotation(ctx, fd, '  ', module)
    ctx.i_pass = 'second'

    # print typedefs
    if len(module.typedef) > 0:
        fd.write('  <!-- YANG typedefs -->\n\n')
    for c in module.typedef:
        xsd_print_simple_type(ctx, module, fd, '  ', c.type,
                              ' name="%s"' % c.i_xsd_name, c.description)
        fd.write('\n')

    # print locally defined typedefs
    if len(module.i_local_typedefs) > 0:
        fd.write('  <!-- local YANG typedefs -->\n\n')
    for c in module.i_local_typedefs:
        xsd_print_simple_type(ctx, module, fd, '  ', c.type,
                              ' name="%s"' % c.i_xsd_name, c.description)
        fd.write('\n')

    # print groups
    if len(module.grouping) > 0:
        fd.write('  <!-- YANG groupings -->\n\n')
    for c in module.grouping:
        xsd_print_grouping(ctx, module, fd, '  ', c)
        fd.write('\n')
    if len(module.grouping) > 0:
        fd.write('\n')

    # print augments
    # filter away local augments; they are printed inline in the XSD
    augment = [a for a in module.augment \
                   if a.i_target_node.i_module.name != module.name]
    if len(augment) > 0:
        fd.write('  <!-- YANG augments -->\n\n')
    for c in augment:
        xsd_print_augment(ctx, module, fd, '  ', c)
        fd.write('\n')
    if len(augment) > 0:
        fd.write('\n')

    # print data definitions
    xsd_print_children(ctx, module, fd, module.i_expanded_children,
                       '  ', [])
    fd.write('\n')

    # then print all generated 'dummy' simpleTypes, if any
    if len(module.i_gen_typedef) > 0:
        fd.write('  <!-- locally generated simpleType helpers -->\n\n')
    for c in module.i_gen_typedef:
        xsd_print_simple_type(ctx, module, fd, '  ', c.type,
                              ' name="%s"' % c.name, None)
        fd.write('\n')

    fd.write('</xs:schema>\n')

def xsd_print_children(ctx, module, fd, children, indent, path,
                       uniq=[''], uindent=''):
    for c in children:
        cn = c.keyword
        if cn in ['container', 'list', 'leaf', 'leaf-list', 'anyxml',
                  'notification', 'rpc']:
            mino = ""
            maxo = ""
            atype = ""
            sgroup = ""
            extbase = None
            if path == []:
                pass
            elif cn in ['leaf']:
                is_key = False
                if ((c.parent.keyword == 'list') and
                    (c in c.parent.i_key)):
                    is_key = True
                if ((is_key == False) and
                    (c.mandatory == None or c.mandatory.arg != 'true')):
                    mino = ' minOccurs="0"'
            elif cn in ['container']:
                if c.presence != None:
                    mino = ' minOccurs="0"'
            elif cn in ['list', 'leaf-list']:
                if c.min_elements != None:
                    mino = ' minOccurs="%s"' % c.min_elements.arg
                else:
                    mino = ' minOccurs="0"'
                if c.max_elements != None:
                    maxo = ' maxOccurs="%s"' % c.max_elements.arg
                else:
                    maxo = ' maxOccurs="unbounded"'
            elif cn in ['anyxml']:
                if (c.mandatory == None or c.mandatory.arg != 'true'):
                    mino = ' minOccurs="0"'

            if cn in ['leaf', 'leaf-list']:
                if c.type.i_is_derived == False:
                    if c.type.name == 'empty':
                        atype = ''
                    elif c.type.name in yang_to_xsd_types:
                        atype = ' type="xs:%s"' % yang_to_xsd_types[c.type.name]
                    elif ((c.type.i_typedef != None) and
                          (":" not in c.type.name)):
                        atype = ' type="%s"' % c.type.i_typedef.i_xsd_name
                    else:
                        atype = ' type="%s"' % c.type.name
            elif cn in ['notification']:
                sgroup = ' substitutionGroup="ncn:notificationContent"'
                extbase = 'ncn:NotificationContentType'
            elif cn in ['rpc']:
                sgroup = ' substitutionGroup="nc:rpcOperation"'
                extbase = 'nc:rpcOperationType'

            fd.write(indent + '<xs:element name="%s"%s%s%s%s>\n' % \
                   (c.name, mino, maxo, atype, sgroup))
            xsd_print_annotation(ctx, fd, indent + '  ', c)
            if cn in ['container', 'list', 'rpc', 'notification']:
                fd.write(indent + '  <xs:complexType>\n')
                extindent = ''
                if extbase != None:
                    fd.write(indent + '    <xs:complexContent>\n')
                    fd.write(indent + '      <xs:extension base="%s">\n' % \
                                   extbase)
                    extindent = '      '
                fd.write(indent + extindent + '    <xs:sequence>\n')
                if cn == 'rpc':
                    if c.input != None:
                        chs = c.input.i_expanded_children
                    else:
                        chs = []
                elif cn == 'list':
                    # sort children so that all keys come first
                    chs = []
                    for k in c.i_key:
                        chs.append(k)
                    for k in c.i_expanded_children:
                        if k not in chs:
                            chs.append(k)
                    if c.i_key != []:
                        # record the key constraints to be used by our
                        # parent element
                        uniq[0] = uniq[0] + uindent + \
                                  '<xs:key name="key_%s">\n' % \
                                  '_'.join(path + [c.name])
                        uniq[0] = uniq[0] + uindent + \
                                  '  <xs:selector xpath="%s:%s"/>\n' % \
                                  (module.i_prefix, c.name)
                        for cc in c.i_key:
                            uniq[0] = uniq[0] + uindent + \
                                      '  <xs:field xpath="%s:%s"/>\n' % \
                                      (module.i_prefix, cc.name)
                        uniq[0] = uniq[0] + uindent + '</xs:key>\n'
                else:
                    chs = c.i_expanded_children
                # allocate a new object for constraint recording
                uniqkey=['']
                xsd_print_children(ctx, module, fd, chs,
                                   indent + extindent + '      ',
                                   [c.name] + path,
                                   uniqkey, indent + extindent + '  ')
                # allow for augments
                fd.write(indent + extindent + '      <xs:any minOccurs="0" '\
                               'maxOccurs="unbounded"\n')
                fd.write(indent + extindent +
                           '              namespace="##other" '\
                               'processContents="lax"/>\n')
                fd.write(indent + extindent + '    </xs:sequence>\n')
                if extbase != None:
                    fd.write(indent + '      </xs:extension>\n')
                    fd.write(indent + '    </xs:complexContent>\n')
                fd.write(indent + '  </xs:complexType>\n')
                # write the recorded key and unique constraints (if any)
                fd.write(uniqkey[0])
            elif cn in ['leaf', 'leaf-list']:
                if c.type.i_is_derived == True:
                    xsd_print_simple_type(ctx, module, fd, indent + '  ',
                                          c.type, '', None)
                elif c.type.name == 'empty':
                    fd.write(indent + '  <xs:complexType/>\n')
            elif cn in ['anyxml']:
                fd.write(indent + '  <xs:complexType>\n')
                fd.write(indent + '    <xs:complexContent>\n')
                fd.write(indent + '      <xs:extension base="xs:anyType">\n')
                fd.write(indent + '    </xs:complexContent>\n')
                fd.write(indent + '  </xs:complexType>\n')
                
            fd.write(indent + '</xs:element>\n')
        elif cn == 'choice':
            fd.write(indent + '<xs:choice>\n')
            xsd_print_description(fd, indent + '  ', c.description)
            for child in c.i_expanded_children:
                fd.write(indent + '  <xs:sequence>\n')
                xsd_print_children(ctx, module, fd,
                                   child.i_expanded_children,
                                   indent + '    ', path)
                # allow for augments
                fd.write(indent + '    <xs:any minOccurs="0" '\
                               'maxOccurs="unbounded"\n')
                fd.write(indent + '            namespace="##other" '\
                               'processContents="lax"/>\n')
                fd.write(indent + '  </xs:sequence>\n')
            # allow for augments
            fd.write(indent + '  <xs:any minOccurs="0"' \
                           ' maxOccurs="unbounded"\n')
            fd.write(indent + '          namespace="##other" '\
                           'processContents="lax"/>\n')
            fd.write(indent + '</xs:choice>\n')
        elif cn == 'uses':
            fd.write(indent + '<xs:group ref="%s"/>\n' % c.name)
            

def xsd_print_grouping(ctx, module, fd, indent, grouping):
    fd.write(indent + '<xs:group name="%s">\n' % grouping.name)
    xsd_print_description(fd, indent + '  ', grouping.description)
    fd.write(indent + '  <xs:sequence>\n')
    xsd_print_children(ctx, module, fd, grouping.i_expanded_children,
                       indent + '    ', [grouping.name])
    fd.write(indent + '  </xs:sequence>\n')
    fd.write(indent + '</xs:group>\n')

def xsd_print_augment(ctx, module, fd, indent, augment):
    i = module.i_gen_augment_idx
    name = "a" + str(i)
    while util.attrsearch(name, 'name', module.grouping) != None:
        i = i + 1
        name = "a" + str(i)
    module.i_gen_augment_idx = i + 1
    fd.write(indent + '<xs:group name="%s">\n' % name)
    xsd_print_description(fd, indent + '  ', augment.description)
    fd.write(indent + '  <xs:sequence>\n')
    xsd_print_children(ctx, module, fd, augment.i_expanded_children,
                       indent + '    ', [])
    fd.write(indent + '  </xs:sequence>\n')
    fd.write(indent + '</xs:group>\n')

def xsd_print_description(fd, indent, descr):
    if descr != None:
        fd.write(indent + '<xs:annotation>\n')
        fd.write(indent + '  <xs:documentation>\n')
        fd.write(fmt_text(indent + '    ', descr.arg) + '\n')
        fd.write(indent + '  </xs:documentation>\n')
        fd.write(indent + '</xs:annotation>\n\n')

def xsd_print_simple_type(ctx, module, fd, indent, type, attrstr, descr):
    if type.bit != []:
        fd.write(indent + '<xs:simpleType%s>\n' % attrstr)
        xsd_print_description(fd, indent + '  ', descr)
        fd.write(indent + '  <xs:list>\n')
        fd.write(indent + '    <xs:simpleType>\n')
        fd.write(indent + '      <xs:restriction base="xs:string">\n')
        for bit in type.bit:
            fd.write(indent + '        <xs:enumeration value=%s/>\n' % \
                   quoteattr(bit.name))
        fd.write(indent + '      </xs:restriction>\n')
        fd.write(indent + '    </xs:simpleType>\n')
        fd.write(indent + '  </xs:list>\n')
        fd.write(indent + '</xs:simpleType>\n')
        return
    fd.write(indent + '<xs:simpleType%s>\n' % attrstr)
    xsd_print_description(fd, indent + '  ', descr)
    if type.name in yang_to_xsd_types:
        base = 'xs:%s' % yang_to_xsd_types[type.name]
    elif type.enum != []:
        base = 'xs:string'
    elif ((type.i_typedef != None) and (":" not in type.name)):
        base = type.i_typedef.i_xsd_name
    else:
        base = type.name
    if ((type.length != None) and (type.pattern != None)):
        # this type has both length and pattern, which isn't allowed
        # in XSD.  we solve this by generating a dummy type with the
        # pattern only, derive from it
        new_type = copy.copy(type)
        new_type.length = None
        if ctx.i_pass == 'first':
            base = ''
        else:
            base = module.gen_new_typedef(new_type)
        # reset type
        new_type = copy.copy(type)
        new_type.pattern = None
        type = new_type
    if (((type.length != None) and (len(type.length.i_lengths) > 1)) or
        ((type.range != None) and (len(type.range.i_ranges)) > 1)):
        if type.i_typedef != None:
            parent = type.i_typedef.type
            if (((parent.length != None) and
                 (len(parent.length.i_lengths) > 1) and
                 type.length != None) or
                ((parent.range != None) and
                 (len(parent.range.i_ranges) > 1) and
                 type.range != None)):
                # the parent type is translated into a union, and we need
                # to use a new length facet - this isn't allowed by XSD.
                # but we make the observation that the length facet in the
                # parent isn't needed anymore, so we use the parent's parent
                # as base type, unless the parent's parent has pattern
                # restrictions also, in which case we generate a new typedef
                # w/o the lengths
                if parent.pattern != None:
                    # we have to generate a new derived type with the
                    # pattern restriction only
                    new_type = copy.copy(parent)
                    new_type.length = None
                    # type might be in another module, so we might need to
                    # a prefix.  further, it's base type might be in yet another
                    # module, so we might need to change it's base type's
                    # name
                    if type.name.find(":") != -1:
                        [prefix, _name] = type.name.split(':', 1)
                        if new_type.name.find(":") == -1:
                            new_type.name = prefix + ":" + new_type.name
                        else:
                            # complex case. the other type has a prefix, i.e.
                            # is imported. we might not even import that module.
                            # we have to add an import in order to cover
                            # this case properly
                            [newprefix, newname] = new_type.name.split(':', 1)
                            newmodname = new_type.i_module.i_prefixes[newprefix]
                            # first, check if we already have the module
                            # imported
                            newprefix = dictsearch(newmodname, module.i_prefixes)
                            if newprefix != None:
                                # it is imported, use our prefix
                                new_type.name = newprefix + ':' + newname
                            else:
                                module.gen_new_import(newmodname)
                                
                    if ctx.i_pass == 'first':
                        base = ''
                    else:
                        base = module.gen_new_typedef(new_type)
                else:
                    base = parent.name
        fd.write(indent + '  <xs:union>\n')
        if type.length != None:
            for (lo,hi) in type.length.i_lengths:
                fd.write(indent + '    <xs:simpleType>\n')
                fd.write(indent + '      <xs:restriction base="%s">\n' % base)
                if hi == None:
                    # FIXME: we don't generate length here currently,
                    # b/c libxml segfaults if base also has min/maxLength...
#                    fd.write(indent +
#                        '        <xs:length value="%s"/>\n' % lo)
                    hi = lo
                if lo not in ['min','max']:
                    fd.write(indent + 
                               '        <xs:minLength value="%s"/>\n' % lo)
                if hi not in ['min','max']:
                    fd.write(indent +
                               '        <xs:maxLength value="%s"/>\n' % hi)
                fd.write(indent + '      </xs:restriction>\n')
                fd.write(indent + '    </xs:simpleType>\n')
        elif type.range != None:
            for (lo,hi) in type.range.i_ranges:
                fd.write(indent + '    <xs:simpleType>\n')
                fd.write(indent + '      <xs:restriction base="%s">\n' % base)
                if lo not in ['min','max']:
                    fd.write(indent +
                               '        <xs:minInclusive value="%s"/>\n' %\
                                   lo)
                if hi == None:
                    hi = lo
                if hi not in ['min', 'max']:
                    fd.write(indent +
                               '        <xs:maxInclusive value="%s"/>\n' %\
                                   hi)
                fd.write(indent + '      </xs:restriction>\n')
                fd.write(indent + '    </xs:simpleType>\n')
        fd.write(indent + '  </xs:union>\n')
    elif type.type != []:
        fd.write(indent + '  <xs:union>\n')
        for t in type.type:
            xsd_print_simple_type(ctx, module, fd, indent+'    ', t, '', None)
        fd.write(indent + '  </xs:union>\n')
    else:
        fd.write(indent + '  <xs:restriction base="%s">\n' % base)
        if len(type.enum) > 0:
            for e in type.enum:
                fd.write(indent + '    <xs:enumeration value=%s/>\n' % \
                    quoteattr(e.name))
        elif type.pattern != None:
            fd.write(indent + '    <xs:pattern value=')
            qstr = quoteattr(type.pattern.expr)
            cnt = 70 - len(indent) - 22
            if ctx.opts.xsd_break_pattern == True and len(qstr) > cnt:
                while (len(qstr) > 0):
                    fd.write(qstr[0:cnt])
                    qstr = qstr[cnt:]
                    if len(qstr):
                        fd.write("\n" + indent + '                       ')
            else:
                fd.write(qstr)
            fd.write('/>\n')
        elif type.length != None:
            [(lo,hi)] = type.length.i_lengths # other cases in union above
            if lo == hi and False:
                # FIXME: we don't generate length here currently,
                # b/c libxml segfaults if base also has min/maxLength
                fd.write(indent + '    <xs:length value="%s"/>\n' % lo)
            else:
                if lo not in ['min','max']:
                    fd.write(indent + '    <xs:minLength value="%s"/>\n' % lo)
                if hi == None:
                    hi = lo
                if hi not in ['min', 'max']:
                    fd.write(indent + '    <xs:maxLength value="%s"/>\n' % hi)
        elif type.range != None:
            [(lo,hi)] = type.range.i_ranges # other cases in union above
            if lo not in ['min','max']:
                fd.write(indent + '    <xs:minInclusive value="%s"/>\n' % lo)
            if hi == None:
                hi = lo
            if hi not in ['min', 'max']:
                fd.write(indent + '    <xs:maxInclusive value="%s"/>\n' % hi)
        fd.write(indent + '  </xs:restriction>\n')
    fd.write(indent + '</xs:simpleType>\n')

def xsd_print_annotation(ctx, fd, indent, obj):
    def is_appinfo(keyword):
        if util.is_prefixed(keyword) == True:
            return False
        (argname, argiselem, argappinfo) = yang_keywords[keyword]
        return argappinfo
    
    def do_print(indent, stmt):
        keyword = stmt.keyword
        (argname, argiselem, argappinfo) = yang_keywords[keyword]
        if argname == None:
            fd.write(indent + '<yin:' + keyword + '/>\n')
        elif argiselem == False:
            # print argument as an attribute
            attrstr = argname + '=' + quoteattr(stmt.arg)
            if len(stmt.substmts) == 0:
                fd.write(indent + '<yin:' + keyword + ' ' + attrstr + '/>\n')
            else:
                fd.write(indent + '<yin:' + keyword + ' ' + attrstr + '>\n')
                for s in stmt.substmts:
                    do_print(indent + '  ', s)
                fd.write(indent + '</yin:' + keyword + '>\n')
        else:
            # print argument as an element
            fd.write(indent + '<yin:' + keyword + '>\n')
            fd.write(indent + '  <yin:' + argname + '>\n')
            fd.write(fmt_text(indent + '    ', stmt.arg))
            fd.write('\n' + indent + '  </yin:' + argname + '>\n')
            for s in stmt.substmts:
                do_print(indent + '  ', s)
            fd.write(indent + '</yin:' + keyword + '>\n')

    stmts = [s for s in obj.substmts if is_appinfo(s.keyword)]
    if ((ctx.opts.xsd_no_appinfo == False and len(stmts) > 0) or
        obj.description != None):
        fd.write(indent + '<xs:annotation>\n')
        if obj.description != None:
            fd.write(indent + '  <xs:documentation>\n')
            fd.write(fmt_text(indent + '    ', obj.description.arg) + '\n')
            fd.write(indent + '  </xs:documentation>\n')
        if ctx.opts.xsd_no_appinfo == False:
            fd.write(indent + '  <xs:appinfo>\n')
            for stmt in stmts:
                do_print(indent + '    ', stmt)
            fd.write(indent + '  </xs:appinfo>\n')
        fd.write(indent + '</xs:annotation>\n')

# FIXME: I don't thik this is strictly correct - we should really just
# print the string as-is, since whitespace in XSD is significant.
def fmt_text(indent, data):
    res = []
    for line in re.split("(\n)", escape(data)):
        if line == '':
            continue
        if line == '\n':
            res.extend(line)
        else:
            res.extend(indent + line)
    return ''.join(res)
