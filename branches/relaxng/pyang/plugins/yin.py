### YIN output

from xml.sax.saxutils import quoteattr
from xml.sax.saxutils import escape

import re

import pyang.plugin
import pyang.main as main
import pyang.tokenizer as ptok
from pyang.util import attrsearch

def pyang_plugin_init():
    pyang.main.register_plugin(YINPlugin())

class YINPlugin(pyang.plugin.PyangPlugin):
    def add_output_format(self, fmts):
        fmts['yin'] = self
    def emit(self, ctx, module, writef):
        emit_yin(ctx, module, writef)
        

## FIXME: rewrite to use Stmt.substmts instead of re-parsing the file

# PRE: the file is syntactically correct
def emit_yin(ctx, module, writef):
    filename = ctx.filename
    pos = main.Position(filename)
    fd = open(filename, "r")
    tokenizer = ptok.YangTokenizer(fd, pos, ctx.errors)
    writef('<?xml version="1.0" encoding="UTF-8"?>\n')
    if module.i_is_submodule:
        mtype = 'submodule'
        xindent = '   '
    else:
        mtype = 'module'
        xindent = ''
    writef('<%s xmlns="urn:ietf:params:xml:ns:yin:1"\n' % mtype)
    for pre in module.i_prefixes:
        modname = module.i_prefixes[pre]
        mod = ctx.modules[modname]
        if mod != None:
            uri = mod.namespace.arg
            writef(xindent + '        xmlns:' + pre + '=' +
                   quoteattr(uri) + '\n')
    writef(xindent + '        name="%s">\n' % module.name)

    # skip the module keywd and name
    tokenizer.get_keyword() # module
    tokenizer.get_string()  # <name>
    tokenizer.get_tok()     # {
    _yang_to_yin(ctx, module, tokenizer, writef, '  ', None)
    writef('</%s>\n' % mtype)

# pre:  { read
# post: } read
def _yang_to_yin(ctx, module, tokenizer, writef, indent, cur_prefix):
    new_prefix = cur_prefix
    keywd = tokenizer.get_keyword()
    argname = None
    argiselem = False
    if keywd == ptok.T_CLOSE_BRACE:
        return;
    elif main.is_prefixed(keywd):
        (prefix, identifier) = keywd
        new_prefix = prefix
        tag = prefix + ':' + identifier
        mod = module.prefix_to_module(prefix, tokenizer.pos, [])
        if mod != None:
            ext = attrsearch(identifier, 'name', mod.extension)
            if ext.argument != None:
                argname = ext.argument.name
                if ext.argument.yin_element != None:
                    argiselem = ext.argument.yin_element.arg == 'true'
    elif cur_prefix != None:
        tag = keywd
        try:
            mod = ctx.modules[module.i_prefixes[cur_prefix]]
            ext = attrsearch(keywd, 'name', mod.extension)
            if ext.argument != None:
                argname = ext.argument.name
                if ext.argument.yin_element != None:
                    argiselem = ext.argument.yin_element.arg == 'true'
        except KeyError:
            pass
    else:
        (argname, argiselem, argappinfo) = main.yang_keywords[keywd]
        tag = keywd
    if argname == None:
        tok = tokenizer.get_tok() # ; or {
        # no argument for this keyword
        if tok == ptok.T_SEMICOLON:
            writef(indent + '<' + tag + '/>\n')
        elif tok == ptok.T_OPEN_BRACE:
            writef(indent + '<' + tag + '>\n')
            _yang_to_yin(ctx, module, tokenizer, writef,
                         indent + '  ', new_prefix)
            writef(indent + '</' + tag + '>\n')
    else:
        arg = tokenizer.get_string()
        tok = tokenizer.get_tok() # ; or {
        if argiselem == False:
            # print argument as an attribute
            argstr = argname + '=' + quoteattr(arg)
            if tok == ptok.T_SEMICOLON:
                writef(indent + '<' + tag + ' ' + argstr + '/>\n')
            elif tok == ptok.T_OPEN_BRACE:
                writef(indent + '<' + tag + ' ' + argstr + '>\n')
                _yang_to_yin(ctx, module, tokenizer, writef,
                             indent + '  ', new_prefix)
                writef(indent + '</' + tag + '>\n')
        else:
            # print argument as an element
            writef(indent + '<' + tag + '>\n')
## FIXME: since whitespace is significant in XML, the current
## code is strictly speaking incorrect.  But w/o the whitespace,
## it looks too ugly.
#            writef(indent + '  <' + argname + '>' + \
#                   escape(arg) + \
#                   '</' + argname + '>\n')
            writef(indent + '  <' + argname + '>\n')
            writef(fmt_text(indent + '    ', arg))
            writef('\n' + indent + '  </' + argname + '>\n')
            if tok == ptok.T_SEMICOLON:
                pass
            elif tok == ptok.T_OPEN_BRACE:
                _yang_to_yin(ctx, module, tokenizer, writef,
                             indent + '  ', new_prefix)
            writef(indent + '</' + tag + '>\n')
    _yang_to_yin(ctx, module, tokenizer, writef, indent, cur_prefix)
            

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
