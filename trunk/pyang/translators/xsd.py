"""XSD output plugin"""

from xml.sax.saxutils import quoteattr
from xml.sax.saxutils import escape

import optparse
import re

from .. import plugin
from .. import util
from .. import statements
from .. import error

yang_to_xsd_types = \
  {'int8':'byte',
   'int16':'short',
   'int32':'int',
   'int64':'long',
   'uint8':'unsignedByte',
   'uint16':'unsignedShort',
   'uint32':'unsignedInt',
   'uint64':'unsignedLong',
   'decimal64':'decimal',
   'string':'string',
   'boolean':'boolean',
   # enumeration is handled separately
   # bits is handled separately
   'binary':'base64Binary',
   # leafref is handled separately
   'instance-identifier':'string',
   'identityref':'QName',
   # empty is handled separately
   # union is handled separately
   }

    # keyword             argument-name  yin-element xsd-appinfo
yang_keywords = \
    {'anyxml':           ('name',        False,      False),
     'argument':         ('name',        False,      False),
     'augment':          ('target-node', False,      False),
     'base':             ('name',        False,      False),
     'belongs-to':       ('module',      False,      True),
     'bit':              ('name',        False,      False),
     'case':             ('name',        False,      False),
     'choice':           ('name',        False,      False),
     'config':           ('value',       False,      True),
     'contact':          ('text',        True,       True),
     'container':        ('name',        False,      False),
     'default':          ('value',       False,      True),
     'description':      ('text',        True,       False),
     'deviate':          ('value',       False,      False),
     'deviation':        ('target-node', False,      False),
     'enum':             ('name',        False,      False),
     'error-app-tag':    ('value',       False,      True),
     'error-message':    ('value',       True,       True),
     'extension':        ('name',        False,      False),
     'feature':          ('name',        False,      False),
     'fraction-digits':  ('value',       False,      False),
     'grouping':         ('name',        False,      False),
     'identity':         ('name',        False,      False),
     'if-feature':       ('name',        False,      False),
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
     'organization':     ('text',        True,       True),
     'output':           (None,          None,       False),
     'path':             ('value',       False,      False),
     'pattern':          ('value',       False,      False),
     'position':         ('value',       False,      False),
     'presence':         ('value',       False,      False),
     'prefix':           ('value',       False,      True),
     'range':            ('value',       False,      False),
     'reference':        ('text',        True,       True),
     'refine':           ('target-node', False,      False),
     'require-instance': ('value',       False,      True),
     'revision':         ('date',        False,      True),
     'revision-date':    ('date',        False,      True),
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
            optparse.make_option("--xsd-global-complex-types",
                                 dest="xsd_global_complex_types",
                                 action="store_true",
                                 help="Make all complex types global instead" +
                                      " of inline"),
            optparse.make_option("--xsd-groups",
                                 dest="xsd_groups",
                                 action="store_true",
                                 help="EXPERIMENTAL: does not work correctly"),
            optparse.make_option("--xsd-no-appinfo",
                                 dest="xsd_no_appinfo",
                                 action="store_true",
                                 help="Do not print YANG specific appinfo"),
            optparse.make_option("--xsd-no-imports",
                                 dest="xsd_no_imports",
                                 action="store_true",
                                 help="Do not generate xs:import elements"),
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
        g = optparser.add_option_group(
            "DEPRECATED: XSD output specific options")
        g.add_options(optlist)
    def add_output_format(self, fmts):
        fmts['xsd'] = self
    def emit(self, ctx, modules, fd):
        module = modules[0]
        # cannot do XSD unless everything is ok for our module
        for (epos, etag, eargs) in ctx.errors:
            if (epos.top == module and
                error.is_error(error.err_level(etag))):
                raise error.EmitError("XSD translation needs a valid module")
        # we also need to have all other modules found
        for pre in module.i_prefixes:
            (modname, revision) = module.i_prefixes[pre]
            mod = statements.modulename_to_module(module, modname, revision)
            if mod == None:
                raise error.EmitError("cannot find module %s, needed by XSD"
                                      " translation" % modname)
            
        emit_xsd(ctx, module, fd)

class DummyFD(object):
    def write(self, s):
        pass


def expand_locally_defined_typedefs(ctx, module, m):
    """Create top-level typedefs for all locally defined typedefs."""
    for c in m.search('typedef'):
        c.i_xsd_name = c.arg
    for inc in module.search('include'):
        rev = None
        r = inc.search_one('revision-date')
        if r is not None:
            rev = r.arg
        m = ctx.get_module(inc.arg, rev)
        for c in m.search('typedef'):
            c.i_xsd_name = c.arg

    def gen_name(name, name_list):
        i = 0
        tname = name + '_' + str(i)
        while util.attrsearch(tname, 'i_xsd_name', name_list):
            i = i + 1
            tname = name + '_' + str(i)
        return tname
            
    def add_typedef(obj):
        for t in obj.search('typedef'):
            t.i_xsd_name = gen_name(t.arg, module.search('typedef') + \
                                        module.i_local_typedefs)
            module.i_local_typedefs.append(t)
        if 'i_children' in obj.__dict__:
            for c in obj.i_children:
                add_typedef(c)
        for c in obj.search('grouping'):
            add_typedef(c)
    for c in (m.i_children +
              m.search('augment') +
              m.search('grouping')):
        add_typedef(c)

def emit_xsd(ctx, module, fd):
    if module.keyword == 'submodule':
        belongs_to = module.search_one('belongs-to')
        parent_modulename = belongs_to.arg
        parent_module = ctx.read_module(parent_modulename)
        if parent_module is not None:
            i_namespace = parent_module.search_one('namespace').arg
            i_prefix = parent_module.search_one('prefix').arg
        else:
            raise error.EmitError("cannot find module %s, needed by XSD"
                                  " translation" % parent_modulename)
    else:
        i_namespace = module.search_one('namespace').arg
        i_prefix = module.search_one('prefix').arg

    # initialize some XSD specific variables
    module.i_xsd_namespace = i_namespace
    module.i_xsd_prefix = i_prefix
    module.i_gen_typedef = []
    module.i_gen_import = []
    module.i_gen_augment_idx = 0
    module.i_local_typedefs = []

    mods = [module]
    for i in module.search('include'):
        subm = ctx.get_module(i.arg)
        if subm is not None:
            mods.append(subm)
            # make sure the top module imports all modules imported by the
            # submodule
            for subimp in subm.search('import'):
                p = subimp.search_one('prefix').arg
                (othermodname, otherrevision) = subm.i_prefixes[p]
                ourprefix = util.dictsearch((othermodname,otherrevision),
                                            module.i_prefixes)
                if ourprefix is None:
                    # we don't have a prefix for this module
                    newprefix = gen_new_import(module, othermodname,
                                               otherrevision)
                    newmod = ctx.get_module(othermodname, otherrevision)
                    newmod.i_xsd_prefix = newprefix

    # make sure we "import" all modules imported by our modules,
    # recursively.  the reason for this is that we might generate a
    # type reference for leafreafs, and for this the module must be
    # imported.  unused imports are ignored by confdc.
    handled = []
    def add_import(othermodname, otherrevision):
        if (othermodname, otherrevision) not in handled:
            # new module
            handled.append((othermodname, otherrevision))
            ourprefix = util.dictsearch((othermodname,otherrevision),
                                        module.i_prefixes)
            if ourprefix is None:
                # we don't have a prefix for this module
                newprefix = gen_new_import(module, othermodname,
                                           otherrevision)
                newmod = ctx.get_module(othermodname, otherrevision)
                newmod.i_xsd_prefix = newprefix
            else:
                newmod = ctx.get_module(othermodname, otherrevision)

            for i in newmod.search('include'):
                subm = ctx.get_module(i.arg)
                if subm is not None:
                    for imp in subm.search('import'):
                        r = imp.search_one('revision-date')
                        if r is not None:
                            r = r.arg
                        add_import(imp.arg, r)

            for imp in newmod.search('import'):
                r = imp.search_one('revision-date')
                if r is not None:
                    r = r.arg
                add_import(imp.arg, r)
    for imp in module.search('import'):
        r = imp.search_one('revision-date')
        if r is not None:
            r = r.arg
        add_import(imp.arg, r)

    # first, create top-level typedefs of local typedefs
    for m in mods:
        expand_locally_defined_typedefs(ctx, module, m)

    prefixes = [module.i_xsd_prefix] + [p for p in module.i_prefixes]
    if module.i_xsd_prefix in ['xs', 'yin', 'nc', 'ncn']:
        i = 0
        pre = "p" + str(i)
        while pre in prefixes:
            i = i + 1
            pre = "p" + str(i)
        prefixes.append(pre)
        module.i_xsd_prefix = pre
        
    has_rpc = False
    has_notifications = False
    for c in module.substmts:
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
    fd.write('           targetNamespace="%s"\n' % module.i_xsd_namespace)
    fd.write('           xmlns="%s"\n' % module.i_xsd_namespace)
    fd.write('           elementFormDefault="qualified"\n')
    fd.write('           attributeFormDefault="unqualified"\n')
    if len(module.search('revision')) > 0:
        fd.write('           version="%s"\n' % 
                 module.search('revision')[0].arg)
    fd.write('           xml:lang="en"')

    handled_modules = []
    for m in mods:
        for pre in m.i_prefixes:
            (modname, revision) = m.i_prefixes[pre]
            mod = statements.modulename_to_module(m, modname, revision)
            if mod in handled_modules or mod.keyword == 'submodule':
                continue
            handled_modules.append(mod)
            if pre in ['xs', 'yin', 'nc', 'ncn']:
                # someone uses one of our prefixes
                # generate a new prefix for that module
                i = 0
                pre = "p" + str(i)
                while pre in prefixes:
                    i = i + 1
                    pre = "p" + str(i)
                prefixes.append(pre)
            mod.i_xsd_prefix = pre
            if mod == module:
                uri = mod.i_xsd_namespace
            else:
                uri = mod.search_one('namespace').arg
            fd.write('\n          xmlns:' + pre + '=' + quoteattr(uri))
    fd.write('>\n\n')
    
    if ctx.opts.xsd_no_imports != True:
        imports = module.search('import') + module.i_gen_import
        for inc in module.search('include'):
            rev = None
            r = inc.search_one('revision-date')
            if r is not None:
                rev = r.arg
            m = ctx.get_module(inc.arg, rev)
            imports.extend(m.search('import'))
        imported = []
        for x in imports:
            rev = None
            r = x.search_one('revision-date')
            if r is not None:
                rev = r.arg
            mod = ctx.get_module(x.arg, rev)
            if mod not in imported:
                imported.append(mod)
                uri = mod.search_one('namespace').arg
                fd.write('  <xs:import namespace="%s"\n' \
                         '             schemaLocation="%s.xsd"/>\n' %
                         (uri, x.arg))
        if has_rpc and module.arg == 'ietf-netconf':
            # this is the YANG mdoule for the NETCONF operations
            # FIXME: when 4741bis has been published, change
            # the schema location to a http uri
            fd.write('  <xs:include\n')
            fd.write('    schemaLocation="netconf.xsd"/>')
        elif has_rpc:
            fd.write('  <xs:import\n')
            fd.write('     namespace=' \
                           '"urn:ietf:params:xml:ns:netconf:base:1.0"\n')
            fd.write('     schemaLocation="http://www.iana.org/assignments/' \
                         'xml-registry/schema/netconf.xsd"/>')
        if has_notifications:
            fd.write('  <xs:import\n')
            fd.write('     namespace="urn:ietf:params:xml:ns:netconf:' \
                           'notification:1.0"\n')
            fd.write('     schemaLocation="http://www.iana.org/assignments/' \
                         'xml-registry/schema/notification.xsd"/>')
        if len(imports) > 0 or has_rpc or has_notifications:
            fd.write('\n')

    if ctx.opts.xsd_no_lecture != True:
        fd.write('  <xs:annotation>\n')
        fd.write('    <xs:documentation>\n')
        fd.write('      This schema was generated from the YANG module %s\n' % \
                     module.arg)
## FIXME: how do I import pyang?
#        fd.write('      by pyang version %s.\n' % pyang.__version__)
        fd.write('\n')
        fd.write('      The schema describes an instance document consisting\n')
        fd.write('      of the entire configuration data store, operational\n')
        fd.write('      data, rpc operations, and notifications.\n')
        fd.write('      This schema can thus NOT be used as-is to\n')
        fd.write('      validate NETCONF PDUs.\n')
        fd.write('    </xs:documentation>\n')
        fd.write('  </xs:annotation>\n\n')
        
    print_annotation(ctx, fd, '  ', module)
    ctx.i_pass = 'second'

    # print typedefs
    got_typedefs = False
    for m in mods:
        if m.search_one('typedef') is not None:
            got_typedefs = True
    if got_typedefs:
        fd.write('\n  <!-- YANG typedefs -->\n')
        for m in mods:
            for c in m.search('typedef'):
                print_simple_type(ctx, module, fd, '  ', c.search_one('type'), c,
                                  ' name="%s"' % c.i_xsd_name,
                                  c.search_one('description'))

    # print locally defined typedefs
    if len(module.i_local_typedefs) > 0:
        fd.write('\n  <!-- local YANG typedefs -->\n')
    for c in module.i_local_typedefs:
        fd.write('\n')
        print_simple_type(ctx, module, fd, '  ', c.search_one('type'), c,
                          ' name="%s"' % c.i_xsd_name,
                          c.search_one('description'))

    # print augments
    # filter away local augments; they are printed inline in the XSD
    augment = [a for a in module.search('augment') \
                   if a.i_target_node.i_module.arg != module.arg]
    if len(augment) > 0:
        fd.write('\n  <!-- YANG augments -->\n')
    for c in augment:
        fd.write('\n')
        print_augment(ctx, module, fd, '  ', c)

    # print groupings
    if ctx.opts.xsd_groups and len(module.i_groupings) > 0:
        fd.write('\n  <!-- YANG groupings -->\n')
        for c in module.i_groupings:
            fd.write('\n')
            print_grouping(ctx, module, fd, '  ', module.i_groupings[c])
    
    fd.write('\n')

    # print data definitions
    ctx.xsd_ct_names = {}
    ctx.xsd_ct_queue = []
    print_children(ctx, module, fd, module.i_children, '  ', [])
    while ctx.xsd_ct_queue:
        (path, uindent, extbase, cn, c, aname) = ctx.xsd_ct_queue.pop()
        print_complex_type(ctx, module, fd, '  ', path,
                           [], uindent, extbase, cn, c, aname)

    # then print all generated 'dummy' simpleTypes, if any
    if len(module.i_gen_typedef) > 0:
        fd.write('\n  <!-- locally generated simpleType helpers -->\n')
    for c in module.i_gen_typedef:
        fd.write('\n')
        print_simple_type(ctx, module, fd, '  ', c.search_one('type'), c,
                          ' name="%s"' % c.arg, None)

    fd.write('\n</xs:schema>\n')

def print_children(ctx, module, fd, children, indent, path,
                   uniq=[], uindent=''):
    uses_list = []
    for c in children:
        if (ctx.opts.xsd_groups and
            hasattr(c, 'i_uses') and
            c.i_uses[0].i_grouping.parent.parent == None and
            c.i_uses[0].search_one('refine') is None):
            # do not inline this child; print a reference to the grouping
            # instead - only for top-level groupings
            if c.i_uses[0] not in uses_list:
                uses_list.append(c.i_uses[0])
                fd.write(indent + '<xs:group ref="%s"/>\n' % c.i_uses[0].arg)
            continue
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
                    (c.parent.search_one('key') is not None) and
                    (c.arg in c.parent.search_one('key').arg.split())):
                    is_key = True
                if ((is_key == False) and
                    (c.search_one('mandatory') == None or 
                     c.search_one('mandatory').arg != 'true')):
                    mino = ' minOccurs="0"'
            elif cn in ['container']:
                # both presence and organizational containers gets
                # a minOccurs 0, b/c empty organizational containers
                # don't have to appear in the XML
                mino = ' minOccurs="0"'
            elif cn in ['list', 'leaf-list']:
                if c.search_one('min-elements') != None:
                    mino = ' minOccurs="%s"' % c.search_one('min-elements').arg
                else:
                    mino = ' minOccurs="0"'
                if c.search_one('max-elements') != None:
                    maxo = ' maxOccurs="%s"' % c.search_one('max-elements').arg
                else:
                    maxo = ' maxOccurs="unbounded"'
            elif cn in ['anyxml']:
                if (c.search_one('mandatory') == None or
                    c.search_one('mandatory').arg != 'true'):
                    mino = ' minOccurs="0"'

            if cn in ['leaf', 'leaf-list']:
                type = c.search_one('type')
                if type.i_is_derived == False:
                    if type.arg == 'empty':
                        atype = ''
                    else:
                        atype = '  type="%s"' % xsd_type_name(ctx, type, c)
            elif cn in ['notification']:
                sgroup = ' substitutionGroup="ncn:notificationContent"'
                extbase = 'ncn:NotificationContentType'
            elif cn in ['rpc']:
                sgroup = ' substitutionGroup="nc:rpcOperation"'
                extbase = 'nc:rpcOperationType'

            if (cn in ['container', 'list', 'rpc', 'notification'] and
                ctx.opts.xsd_global_complex_types):
                ctype_name = c.arg
                x = c.parent
                idx = 0
                while ctype_name in ctx.xsd_ct_names:
                    # already taken; generate a new name
                    # not ideal...
                    if x is not None:
                        ctype_name = '%s_%s' % (x.arg, ctype_name)
                    else:
                        ctype_name = '%s_%d' % (ctype_name, idx)
                        idx = idx + 1
                ctx.xsd_ct_names[ctype_name] = True
                atype = ' type="%s"' % ctype_name
            else:
                ctype_name = None

            fd.write(indent + '<xs:element name="%s"%s%s%s%s' % \
                   (c.arg, mino, maxo, atype, sgroup))
            has_body = print_annotation(ctx, fd, indent + '  ', c, '>\n')
            inline_end = False
            if (cn in ['container', 'list', 'rpc', 'notification'] and
                not ctx.opts.xsd_global_complex_types):
                if not has_body:
                    fd.write('>\n')
                print_complex_type(ctx, module, fd, indent + '  ', path,
                                   uniq, uindent, extbase, cn, c, '')
            elif cn in ['leaf', 'leaf-list']:
                if c.search_one('type').i_is_derived == True:
                    if not has_body:
                        fd.write('>\n')
                    print_simple_type(ctx, module, fd, indent + '  ',
                                      c.search_one('type'), c, '', None)
                elif c.search_one('type').arg == 'empty':
                    if not has_body:
                        fd.write('>\n')
                    fd.write(indent + '  <xs:complexType/>\n')
                elif not has_body:
                    inline_end = True
            elif cn in ['anyxml']:
                if not has_body:
                    fd.write('>\n')
                # FIXME: make one such global type, if needed
                fd.write(indent + '  <xs:complexType>\n')
                fd.write(indent + '    <xs:complexContent>\n')
                fd.write(indent + '      <xs:extension base="xs:anyType"/>\n')
                fd.write(indent + '    </xs:complexContent>\n')
                fd.write(indent + '  </xs:complexType>\n')
                
            if (cn in ['container', 'list', 'rpc', 'notification'] and
                ctx.opts.xsd_global_complex_types):
                ustr = ""
                for child in c.i_children:
                    ustr += mk_ustr(module, path + [c.arg], indent+"  ",
                                    child)
                if ustr != "":
                    if not has_body:
                        has_body = True
                        fd.write('>\n')
                    fd.write(ustr)
                if not has_body:
                    fd.write('/>\n')
                else:
                    fd.write(indent + '</xs:element>\n')
                # add to queue
                ctx.xsd_ct_queue.insert(0, (path, uindent, extbase, cn, c,
                                         ' name="%s"' % ctype_name))
            elif inline_end:
                fd.write('/>\n')
            else:
                fd.write(indent + '</xs:element>\n')

        elif cn == 'choice':
            fd.write(indent + '<xs:choice>\n')
            print_description(fd, indent + '  ', c.search_one('description'))
            for child in c.i_children:
                fd.write(indent + '  <xs:sequence>\n')
                print_children(ctx, module, fd,
                               child.i_children,
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
            
def xsd_type_name(ctx, type, parent):
    if type.arg in yang_to_xsd_types:
        return "xs:%s" % yang_to_xsd_types[type.arg]
    elif type.arg == 'leafref':
        (ref, _pos) = parent.i_leafref_ptr
        return xsd_type_name(ctx, ref.search_one('type'), ref)
    elif ((type.i_typedef != None) and (":" not in type.arg)):
        return type.i_typedef.i_xsd_name
    elif type.i_typedef is not None:
        if hasattr(type.i_typedef, 'i_xsd_name'):
            # the type is in our own module
            return "%s" % type.i_typedef.i_xsd_name
        elif type.i_typedef.parent.keyword == 'module':
            # top-level (exported) typedef
            return "%s:%s" % (type.i_typedef.i_module.i_xsd_prefix,
                              type.i_typedef.arg)
        elif type.i_typedef.parent.keyword == 'submodule':
            if (type.i_typedef.parent.i_modulename == type.i_module.arg):
                # top-level in our own module
                return type.i_typedef.arg
            else:
                # top-level (exported) in submodule
                othermod = ctx.get_module(type.i_typedef.parent.i_modulename)
                return "%s:%s" % (othermod.i_xsd_prefix, type.i_typedef.arg)
        else:
            # cannot happen
            print(type.arg)
            assert False
    else:
        return type.arg
    

def print_augment(ctx, module, fd, indent, augment):
    i = module.i_gen_augment_idx
    name = "a" + str(i)
    while util.attrsearch(name, 'arg', module.search('grouping')) != None:
        i = i + 1
        name = "a" + str(i)
    module.i_gen_augment_idx = i + 1
    fd.write(indent + '<xs:group name="%s">\n' % name)
    print_description(fd, indent + '  ', augment.search_one('description'))
    fd.write(indent + '  <xs:sequence>\n')
    print_children(ctx, module, fd, augment.i_children,
                   indent + '    ', [])
    fd.write(indent + '  </xs:sequence>\n')
    fd.write(indent + '</xs:group>\n')

def print_grouping(ctx, module, fd, indent, grouping):
    fd.write(indent + '<xs:group name="%s">\n' % grouping.arg)
    print_description(fd, indent + '  ', grouping.search_one('description'))
    fd.write(indent + '  <xs:sequence>\n')
    print_children(ctx, module, fd, grouping.i_children,
                   indent + '    ', [])
    fd.write(indent + '  </xs:sequence>\n')
    fd.write(indent + '</xs:group>\n')

def print_description(fd, indent, descr):
    if descr != None:
        fd.write(indent + '<xs:annotation>\n')
        fd.write(indent + '  <xs:documentation>\n')
        fd.write(fmt_text(indent + '    ', descr.arg) + '\n')
        fd.write(indent + '  </xs:documentation>\n')
        fd.write(indent + '</xs:annotation>\n\n')

def gen_new_import(module, modname, revision):
    i = 0
    pre = "p" + str(i)
    while pre in module.i_prefixes:
        i = i + 1
        pre = "p" + str(i)
    module.i_prefixes[pre] = (modname, revision)
    imp = statements.Statement(module, module, None, 'import', modname)
    if revision is not None:
        rev = statements.Statement(module, imp, None, 'revision-date',
                                   revision)
        imp.substmts.append(rev)
    module.i_gen_import.append(imp)
    return pre


def print_complex_type(ctx, module, fd, indent, path, uniq, uindent, extbase,
                       cn, c, aname):
    fd.write(indent + '<xs:complexType%s>\n' % aname)
    extindent = ''
    if extbase != None:
        fd.write(indent + '  <xs:complexContent>\n')
        fd.write(indent + '    <xs:extension base="%s">\n' % \
                       extbase)
        extindent = '    '
    fd.write(indent + extindent + '  <xs:sequence>\n')
    if cn == 'rpc':
        if c.search_one('input') != None:
            chs = c.search_one('input').i_children
        else:
            chs = []
    elif cn == 'list':
        # sort children so that all keys come first
        k = c.search_one('key')
        if k is not None:
            kchs = []
            chs = []
            keynames = k.arg.split()
            for ch in c.i_children:
                if ch.arg in keynames:
                    kchs.append(ch)
                else:
                    chs.append(ch)
            chs = kchs + chs
        else:
            chs = c.i_children
        ustr = mk_ustr(module, path, uindent, c)
        uniq.append(ustr)
    else:
        chs = c.i_children
    # allocate a new object for constraint recording
    uniqes=[]
    print_children(ctx, module, fd, chs,
                   indent + extindent + '    ',
                   [c.arg] + path,
                   uniqes, indent + extindent)
    # allow for augments
    fd.write(indent + extindent + '    <xs:any minOccurs="0" '\
                   'maxOccurs="unbounded"\n')
    fd.write(indent + extindent +
               '            namespace="##other" '\
                   'processContents="lax"/>\n')
    fd.write(indent + extindent + '  </xs:sequence>\n')
    if extbase != None:
        fd.write(indent + '    </xs:extension>\n')
        fd.write(indent + '  </xs:complexContent>\n')
    fd.write(indent + '</xs:complexType>\n')
    # write the recorded key and unique constraints (if any)
    for u in uniqes:
        fd.write(u)
    
def mk_ustr(module, path, uindent, c):
    k = c.search_one('key')
    ustr = ""
    if k is not None:
        # record the key constraints to be used by our
        # parent element
        ustr += uindent + \
                  '<xs:key name="key_%s">\n' % \
                  '_'.join(path + [c.arg])
        ustr += uindent + \
                  '  <xs:selector xpath="%s:%s"/>\n' % \
                  (module.i_xsd_prefix, c.arg)
        for expr in k.arg.split():
            f = '/'.join([module.i_xsd_prefix + ':' + x
                          for x in expr.split('/')])
            ustr += uindent + \
                      '  <xs:field xpath="%s"/>\n' % f
        ustr += uindent + '</xs:key>\n'
    i = 0
    for u in c.search('unique'):
        ustr = uindent + \
                 '<xs:unique name="unique_%s_%s">\n' % \
                 ('_'.join(path + [c.arg]), i)
        ustr += uindent + \
                  '  <xs:selector xpath="%s:%s"/>\n' % \
                  (module.i_xsd_prefix, c.arg)
        for expr in u.arg.split():
            f = '/'.join([module.i_xsd_prefix + ':' + x
                          for x in expr.split('/')])
            ustr += uindent + \
                      '  <xs:field xpath="%s"/>\n' % f
        ustr += uindent + '</xs:unique>\n'
        i += 1                        
    return ustr


def print_simple_type(ctx, module, fd, indent, type, parent, attrstr, descr):

    def gen_new_typedef(module, new_type):
        i = 0
        name = "t" + str(i)
        all_typedefs = module.search('typedef') + module.i_local_typedefs + \
            module.i_gen_typedef
        while util.attrsearch(name, 'arg', all_typedefs):
            i = i + 1
            name = "t" + str(i)
        typedef = statements.Statement(module, module, new_type.pos,
                                       'typedef', name)
        typedef.substmts.append(new_type)
        module.i_gen_typedef.append(typedef)
        return name

    if type.search('bit') != []:
        fd.write(indent + '<xs:simpleType%s>\n' % attrstr)
        print_description(fd, indent + '  ', descr)
        fd.write(indent + '  <xs:list>\n')
        fd.write(indent + '    <xs:simpleType>\n')
        fd.write(indent + '      <xs:restriction base="xs:string">\n')
        for bit in type.search('bit'):
            fd.write(indent + '        <xs:enumeration value=%s/>\n' % \
                   quoteattr(bit.arg))
        fd.write(indent + '      </xs:restriction>\n')
        fd.write(indent + '    </xs:simpleType>\n')
        fd.write(indent + '  </xs:list>\n')
        fd.write(indent + '</xs:simpleType>\n')
        return
    fd.write(indent + '<xs:simpleType%s>\n' % attrstr)
    print_description(fd, indent + '  ', descr)
    if type.arg in yang_to_xsd_types:
        base = xsd_type_name(ctx, type, parent)
    elif type.arg == 'leafref':
        base = xsd_type_name(ctx, type, parent)
    elif type.search('enum') != []:
        base = 'xs:string'
    else:
        base = xsd_type_name(ctx, type, parent)

    if ((type.search_one('length') != None) and (type.search('pattern') != [])):
        # this type has both length and pattern, which isn't allowed
        # in XSD.  we solve this by generating a dummy type with the
        # pattern only, derive from it
        new_type = type.copy()
        # remove length and generate the base type with pattern restriction
        length_stmt = new_type.search_one('length')
        new_type.substmts.remove(length_stmt)
        new_type.i_lengths = []
        if ctx.i_pass == 'first':
            base = ''
        else:
            base = gen_new_typedef(module, new_type)
        # reset type
        new_type = type.copy()
        # remove patterns and keep the length restriction
        for p in new_type.search('pattern'):
            new_type.substmts.remove(p)
        type = new_type
    if (len(type.i_lengths) > 1 or len(type.i_ranges) > 1):
        if type.i_typedef != None:
            parent = type.i_typedef.search_one('type')
            if (len(parent.i_lengths) > 1 or len(parent.i_ranges) > 1):
                # the parent type is translated into a union, and we need
                # to use a new length facet - this isn't allowed by XSD.
                # but we make the observation that the length facet in the
                # parent isn't needed anymore, so we use the parent's parent
                # as base type, unless the parent's parent has pattern
                # restrictions also, in which case we generate a new typedef
                # w/o the lengths
                if parent.search('pattern') != []:
                    # we have to generate a new derived type with the
                    # pattern restriction only
                    new_type = parent.copy()
                    # remove length
                    length_stmt = new_type.search_one('length')
                    new_type.substmts.remove(length_stmt)
                    new_type.i_lengths = []
                    # type might be in another module, so we might need to add
                    # a prefix.  further, its base type might be in yet another
                    # module, so we might need to change its base type's
                    # name
                    if type.arg.find(":") != -1:
                        [prefix, _name] = type.arg.split(':', 1)
                        if new_type.arg.find(":") == -1:
                            new_type.arg = prefix + ":" + new_type.arg
                        else:
                            # complex case. the other type has a prefix, i.e.
                            # is imported. we might not even import that module.
                            # we have to add an import in order to cover
                            # this case properly
                            [newprefix, newname] = new_type.arg.split(':', 1)
                            (newmodname, newrevision) = \
                                new_type.i_module.i_prefixes[newprefix]
                            # first, check if we already have the module
                            # imported
                            newprefix = util.dictsearch((newmodname,newrevision),
                                                        module.i_prefixes)
                            if newprefix != None:
                                # it is imported, use our prefix
                                new_type.arg = newprefix + ':' + newname
                            else:
                                newprefix = gen_new_import(module, newmodname,
                                                           newrevision)
                                newmod = ctx.get_module(newmodname, newrevision)
                                newmod.i_xsd_prefix = newprefix
                                
                    if ctx.i_pass == 'first':
                        base = ''
                    else:
                        base = gen_new_typedef(module, new_type)
                else:
                    base = parent.arg
        fd.write(indent + '  <xs:union>\n')
        if type.search_one('length') != None:
            for (lo,hi) in type.i_lengths:
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
        elif type.search_one('range') != None:
            for (lo,hi) in type.i_ranges:
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
    elif type.search('type') != []:
        fd.write(indent + '  <xs:union>\n')
        for t in type.search('type'):
            print_simple_type(ctx, module, fd, indent+'    ', t, type, '', None)
        fd.write(indent + '  </xs:union>\n')
    elif type.search('pattern') != []:
        def print_pattern(indent, patstr):
            fd.write(indent + '  <xs:pattern value=')
            qstr = quoteattr(patstr)
            cnt = 70 - len(indent) - 22
            if ctx.opts.xsd_break_pattern == True and len(qstr) > cnt:
                while (len(qstr) > 0):
                    fd.write(qstr[0:cnt])
                    qstr = qstr[cnt:]
                    if len(qstr):
                        fd.write("\n" + indent + '                     ')
            else:
                fd.write(qstr)
            fd.write('/>\n')
            
        def print_ored_patterns(patterns, indent):
            if len(patterns) == 1:
                patstr = patterns[0].arg
            else:
                patstr = ''
                for p in patterns[:-1]:
                    patstr += '(' + p.arg + ')|'
                patstr += '(' + patterns[-1].arg + ')'

            fd.write(indent + '  <xs:restriction base="%s">\n' % base)
            print_pattern(indent, patstr)
            fd.write(indent + '  </xs:restriction>\n')

        print_ored_patterns(type.search('pattern'), indent)
    else:
        fd.write(indent + '  <xs:restriction base="%s">\n' % base)
        if len(type.search('enum')) > 0:
            for e in type.search('enum'):
                fd.write(indent + '    <xs:enumeration value=%s/>\n' % \
                             quoteattr(e.arg))
        elif type.search_one('length') != None:
            # other cases in union above
            [(lo,hi)] = type.i_lengths
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
        elif type.search_one('range') != None:
            [(lo,hi)] = type.i_ranges # other cases in union above
            if lo not in ['min','max']:
                fd.write(indent + '    <xs:minInclusive value="%s"/>\n' % lo)
            if hi == None:
                hi = lo
            if hi not in ['min', 'max']:
                fd.write(indent + '    <xs:maxInclusive value="%s"/>\n' % hi)
        elif type.search_one('fraction-digits') is not None:
            fd.write(indent + '    <xs:fractionDigits value="%s"/>\n' % 
                     type.search_one('fraction-digits').arg)
        fd.write(indent + '  </xs:restriction>\n')
    fd.write(indent + '</xs:simpleType>\n')

def print_annotation(ctx, fd, indent, obj, prestr=''):
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
        obj.search_one('description') != None):
        fd.write(prestr)
        fd.write(indent + '<xs:annotation>\n')
        if obj.search_one('description') != None:
            fd.write(indent + '  <xs:documentation>\n')
            fd.write(fmt_text(indent + '    ',
                              obj.search_one('description').arg) + '\n')
            fd.write(indent + '  </xs:documentation>\n')
        if ctx.opts.xsd_no_appinfo == False:
            fd.write(indent + '  <xs:appinfo>\n')
            for stmt in stmts:
                do_print(indent + '    ', stmt)
            fd.write(indent + '  </xs:appinfo>\n')
        fd.write(indent + '</xs:annotation>\n')
        return True
    else:
        return False
    
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
