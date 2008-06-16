"""YIN output plugin"""

from xml.sax.saxutils import quoteattr
from xml.sax.saxutils import escape

import optparse
import re

from pyang import plugin
from pyang import util

yin_namespace = "urn:ietf:params:xml:ns:yang:yin:1"

def pyang_plugin_init():
    plugin.register_plugin(YINPlugin())

class YINPlugin(plugin.PyangPlugin):
    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--yin-pretty-strings",
                                 dest="yin_pretty_strings",
                                 action="store_true",
                                 help="Pretty print strings"),
            ]
        g = optparser.add_option_group("YIN specific options")
        g.add_options(optlist)
    def add_output_format(self, fmts):
        fmts['yin'] = self
    def emit(self, ctx, module, fd):
        emit_yin(ctx, module, fd)
        
def emit_yin(ctx, module, fd):
    fd.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    fd.write('<%s name="%s"\n' % (module.keyword, module.arg))
    fd.write(' ' * len(module.keyword) + '  xmlns="%s"' % yin_namespace)

    if module.prefix != None:
        # FIXME: if the prefix really can be used in the submodule
        # then we need to grab it from the module
        # currently if we get here it is a module (not submodule)
        fd.write('\n')
        fd.write(' ' * len(module.keyword))
        fd.write('  xmlns:' + module.prefix.arg + '=' +
               quoteattr(module.namespace.arg))
    fd.write('>\n')
    for s in module.substmts:
        emit_stmt(ctx, module, s, fd, '  ', '  ')
    fd.write('</%s>\n' % module.keyword)
    
def emit_stmt(ctx, module, stmt, fd, indent, indentstep):
    if util.is_prefixed(stmt.keyword):
        # this is an extension.  need to find its definition
        (prefix, identifier) = stmt.keyword
        tag = prefix + ':' + identifier
        extmodule = module.prefix_to_module(prefix, None, [])
        ext = util.attrsearch(identifier, 'name', extmodule.extension)
        if ext.argument != None:
            if ext.argument.yin_element != None:
                argname = prefix + ':' + ext.argument.name
                argiselem = ext.argument.yin_element.arg == 'true'
            else:
                # no yin-element given, default to false
                argiselem = False
                argname = ext.argument.name
        else:
            argiselem = False
            argname = None
    else:
        (argname, argiselem) = yang_keywords[stmt.keyword]
        tag = stmt.keyword
    if argiselem == False or argname == None:
        if argname == None:
            attr = ''
        else:
            attr = ' ' + argname + '=' + quoteattr(stmt.arg)
        if len(stmt.substmts) == 0:
            fd.write(indent + '<' + tag + attr + '/>\n')
        else:
            fd.write(indent + '<' + tag + attr + '>\n')
            for s in stmt.substmts:
                emit_stmt(ctx, module, s, fd, indent + indentstep,
                          indentstep)
            fd.write(indent + '</' + tag + '>\n')
    else:
        fd.write(indent + '<' + tag + '>\n')
        if ctx.opts.yin_pretty_strings:
            # since whitespace is significant in XML, the current
            # code is strictly speaking incorrect.  But w/o the whitespace,
            # it looks too ugly.
            fd.write(indent + indentstep + '<' + argname + '>\n')
            fd.write(fmt_text(indent + indentstep + indentstep, stmt.arg))
            fd.write('\n' + indent + indentstep + '</' + argname + '>\n')
        else:
            fd.write(indent + indentstep + '<' + argname + '>' + \
                       escape(stmt.arg) + \
                       '</' + argname + '>\n')
        for s in stmt.substmts:
            emit_stmt(ctx, module, s, fd, indent + indentstep, indentstep)
        fd.write(indent + '</' + tag + '>\n')

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

    # keyword             argument-name  yin-element
yang_keywords = \
    {'anyxml':           ('name',        False),
     'argument':         ('name',        False),
     'augment':          ('target-node', False),
     'belongs-to':       ('module',      False),
     'bit':              ('name',        False),
     'case':             ('name',        False),
     'choice':           ('name',        False),
     'config':           ('value',       False),
     'contact':          ('info',        True),
     'container':        ('name',        False),
     'default':          ('value',       False),
     'description':      ('text',        True),
     'enum':             ('name',        False),
     'error-app-tag':    ('value',       False),
     'error-message':    ('value',       True),
     'extension':        ('name',        False),
     'grouping':         ('name',        False),
     'import':           ('module',      False),
     'include':          ('module',      False),
     'input':            (None,          None),
     'key':              ('value',       False),
     'leaf':             ('name',        False),
     'leaf-list':        ('name',        False),
     'length':           ('value',       False),
     'list':             ('name',        False),
     'mandatory':        ('value',       False),
     'max-elements':     ('value',       False),
     'min-elements':     ('value',       False),
     'module':           ('name',        False),
     'must':             ('condition',   False),
     'namespace':        ('uri',         False),
     'notification':     ('name',        False),
     'ordered-by':       ('value',       False),
     'organization':     ('info',        True),
     'output':           (None,          None),
     'path':             ('value',       False),
     'pattern':          ('value',       False),
     'position':         ('value',       False),
     'presence':         ('value',       False),
     'prefix':           ('value',       False),
     'range':            ('value',       False),
     'reference':        ('info',        False),
     'revision':         ('date',        False),
     'rpc':              ('name',        False),
     'status':           ('value',       False),
     'submodule':        ('name',        False),
     'type':             ('name',        False),
     'typedef':          ('name',        False),
     'unique':           ('tag',         False),
     'units':            ('name',        False),
     'uses':             ('name',        False),
     'value':            ('value',       False),
     'when':             ('condition',   False),
     'yang-version':     ('value',       False),
     'yin-element':      ('value',       False),
     }
