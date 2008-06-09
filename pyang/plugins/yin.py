### YIN output

from xml.sax.saxutils import quoteattr
from xml.sax.saxutils import escape

import optparse
import re

from pyang import main
from pyang import plugin
from pyang import error
from pyang import statements
from pyang import util
from pyang.util import attrsearch

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
    def emit(self, ctx, module, writef):
        emit_yin(ctx, module, writef)
        

## FIXME: rewrite to use Stmt.substmts instead of re-parsing the file



T_SEMICOLON   = 1
T_OPEN_BRACE  = 2
T_CLOSE_BRACE = 3

def is_tok(tok):
    return type(tok) == type(T_SEMICOLON)

def tok_to_str(tok):
    if type(tok) == type(''):
        return tok
    elif util.is_prefixed(tok):
        return tok[0] + ':' + tok[1]
    elif tok == T_SEMICOLON:
        return ';'
    elif tok == T_OPEN_BRACE:
        return '{'
    elif tok == T_CLOSE_BRACE:
        return '}'

class YangTokenizer(object):
    def __init__(self, fd, pos, errors):
        self.fd = fd
        self.pos = pos
        self.buf = ''
        self.linepos = 0  # used to remove leading whitespace from strings
        self.errors = errors

    def readline(self):
        self.buf = file.readline(self.fd)
        if self.buf == '':
            raise error.Eof
        self.pos.line = self.pos.line + 1
        self.linepos = 0

    def set_buf(self, i, pos=None):
        if pos == None:
            pos = i
        self.linepos = self.linepos + pos
        self.buf = self.buf[i:]

    def skip(self):
        # skip whitespace and count position
        i = 0
        pos = 0
        buflen = len(self.buf)
        while i < buflen and self.buf[i].isspace():
            if self.buf[i] == '\t':
                pos = pos + 8
            else:
                pos = pos + 1
            i = i + 1
        if i == buflen:
            self.readline()
            return self.skip()
        else:
            self.set_buf(i, pos)
        # skip line comment
        if self.buf.startswith('//'):
            self.readline()
            return self.skip()
        # skip block comment
        elif self.buf.startswith('/*'):
            i = self.buf.find('*/')
            while i == -1:
                self.readline()
                i = self.buf.find('*/')
            self.set_buf(i+2)
            return self.skip()

    # ret: token() | identifier | (prefix, identifier)
    def get_keyword(self):
        self.skip()
        try:
            return self.get_tok()
        except ValueError:
            pass

        m = statements.re_keyword.match(self.buf)
        if m == None:
            error.err_add(self.errors, self.pos,
                         'UNEXPECTED_KEYWORD', self.buf)
            raise error.Abort
        else:
            self.set_buf(m.end())
            if m.group(2) == None: # no prefix
                return m.group(4)
            else:
                return (m.group(2), m.group(4))

    # ret: token()
    def get_tok(self):
        self.skip()
        if self.buf[0] == ';':
            self.set_buf(1)
            return T_SEMICOLON
        elif self.buf[0] == '{':
            self.set_buf(1)
            return T_OPEN_BRACE;
        elif self.buf[0] == '}':
            self.set_buf(1)
            return T_CLOSE_BRACE;
        raise ValueError
    
    # ret: token() | string
    def get_string(self, need_quote=False):
        self.skip()
        try:
            return self.get_tok()
        except ValueError:
            pass
        
        if self.buf[0] == '"' or self.buf[0] == "'":
            # for double-quoted string,  loop over string and translate
            # escaped characters.  also strip leading whitespace as
            # necessary.
            # for single-quoted string, keep going until end quote is found.
            quote_char = self.buf[0]
            # collect output in strs (list of strings)
            strs = [] 
            # remember position of " character
            indentpos = self.linepos
            i = 1
            while True:
                buflen = len(self.buf)
                start = i
                while i < buflen:
                    if self.buf[i] == quote_char:
                        # end-of-string; copy the buf to output
                        strs.append(self.buf[start:i])
                        # and trim buf
                        self.set_buf(i+1)
                        # check for '+' operator
                        self.skip()
                        if self.buf[0] == '+':
                            self.set_buf(1)
                            self.skip()
                            nstr = self.get_string(need_quote=True)
                            if (type(nstr) != type('')):
                                error.err_add(self.errors, self.pos,
                                              'EXPECTED_QUOTED_STRING', ())
                                raise error.Abort
                            strs.append(nstr)
                        return ''.join(strs)
                    elif (quote_char == '"' and
                          self.buf[i] == '\\' and i < (buflen-1)):
                        # check for special characters
                        special = None
                        if self.buf[i+1] == 'n':
                            special = '\n'
                        elif self.buf[i+1] == 't':
                            special = '\t'
                        elif self.buf[i+1] == '\"':
                            special = '\"'
                        elif self.buf[i+1] == '\\':
                            special = '\\'
                        if special != None:
                            strs.append(self.buf[start:i])
                            strs.append(special)
                            i = i + 1
                            start = i + 1
                    i = i + 1
                # end-of-line, keep going
                strs.append(self.buf[start:i])
                self.readline()
                i = 0
                if quote_char == '"':
                    # skip whitespace used for indentation
                    buflen = len(self.buf)
                    while (i < buflen and self.buf[i].isspace() and
                           i <= indentpos):
                        i = i + 1
                    if i == buflen:
                        # whitespace only on this line; keep it as is
                        i = 0
        elif need_quote == True:
            error.err_add(self.errors, self.pos, 'EXPECTED_QUOTED_STRING', ())
            raise error.Abort
        else:
            # unquoted string
            buflen = len(self.buf)
            i = 0
            while i < buflen:
                if (self.buf[i].isspace() or self.buf[i] == ';' or
                    self.buf[i] == '{' or self.buf[i] == '}' or
                    self.buf[i:i+2] == '//' or self.buf[i:i+2] == '/*' or
                    self.buf[i:i+2] == '*/'):
                    res = self.buf[:i]
                    self.set_buf(i)
                    return res
                i = i + 1



# PRE: the file is syntactically correct
def emit_yin(ctx, module, writef):
    filename = ctx.filename
    pos = error.Position(filename)
    fd = open(filename, "r")
    tokenizer = YangTokenizer(fd, pos, ctx.errors)
    writef('<?xml version="1.0" encoding="UTF-8"?>\n')
    if module.i_is_submodule:
        mtype = 'submodule'
        xindent = '   '
    else:
        mtype = 'module'
        xindent = ''
    writef('<%s xmlns="urn:ietf:params:xml:ns:yang:yin:1"\n' % mtype)
    writef(xindent + '        xmlns:' + module.prefix.arg + '=' +
                   quoteattr(module.namespace.arg) + '\n')
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
    if keywd == T_CLOSE_BRACE:
        return;
    elif util.is_prefixed(keywd):
        (prefix, identifier) = keywd
        new_prefix = prefix
        tag = prefix + ':' + identifier
        mod = module.prefix_to_module(prefix, tokenizer.pos, [])
        if mod != None:
            ext = attrsearch(identifier, 'name', mod.extension)
            if ext.argument != None:
                if ext.argument.yin_element != None:
                    argname = prefix + ':' + ext.argument.name
                    argiselem = ext.argument.yin_element.arg == 'true'
                else:
                    argname = ext.argument.name
    elif cur_prefix != None:
        tag = keywd
        try:
            mod = ctx.modules[module.i_prefixes[cur_prefix]]
            ext = attrsearch(keywd, 'name', mod.extension)
            if ext.argument != None:
                if ext.argument.yin_element != None:
                    argname = cur_prefix + ':' + ext.argument.name
                    argiselem = ext.argument.yin_element.arg == 'true'
                else:
                    argname = ext.argument.name
        except KeyError:
            pass
    else:
        (argname, argiselem, argappinfo) = main.yang_keywords[keywd]
        tag = keywd
    if argname == None:
        tok = tokenizer.get_tok() # ; or {
        # no argument for this keyword
        if tok == T_SEMICOLON:
            writef(indent + '<' + tag + '/>\n')
        elif tok == T_OPEN_BRACE:
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
            if tok == T_SEMICOLON:
                writef(indent + '<' + tag + ' ' + argstr + '/>\n')
            elif tok == T_OPEN_BRACE:
                writef(indent + '<' + tag + ' ' + argstr + '>\n')
                _yang_to_yin(ctx, module, tokenizer, writef,
                             indent + '  ', new_prefix)
                writef(indent + '</' + tag + '>\n')
        else:
            # print argument as an element
            writef(indent + '<' + tag + '>\n')
            if ctx.opts.yin_pretty_strings:
                # since whitespace is significant in XML, the current
                # code is strictly speaking incorrect.  But w/o the whitespace,
                # it looks too ugly.
                writef(indent + '  <' + argname + '>\n')
                writef(fmt_text(indent + '    ', arg))
                writef('\n' + indent + '  </' + argname + '>\n')
            else:
                writef(indent + '  <' + argname + '>' + \
                           escape(arg) + \
                           '</' + argname + '>\n')

            if tok == T_SEMICOLON:
                pass
            elif tok == T_OPEN_BRACE:
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
