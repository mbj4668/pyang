import syntax
import grammar
from pyang import main

## FIXME: tmp test code
class Context(object):
    def __init__(self):
        self.errors = []

## FIXME: move to util
def is_prefixed(identifier):
    return type(identifier) == type(()) and len(identifier) == 2


class Abort(Exception):
    """Signal a non-recoverable errors to abort parsing."""
    pass

class Eof(Exception):
    """Signal that end of file is detected."""
    pass

class YangTokenizer(object):
    def __init__(self, fd, pos, errors):
        self.fd = fd
        self.pos = pos
        self.buf = ''
        self.offset = 0
        """Position on line.  Used to remove leading whitespace from strings."""
        
        self.errors = errors

    def readline(self):
        self.buf = file.readline(self.fd)
        if self.buf == '':
            raise Eof
        self.pos.line = self.pos.line + 1
        self.offset = 0

    def set_buf(self, i, pos=None):
        if pos == None:
            pos = i
        self.offset = self.offset + pos
        self.buf = self.buf[i:]

    def skip(self):
        """Skip whitespace and count position"""
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

    def get_keyword(self):
        """ret: identifier | (prefix, identifier)"""
        self.skip()

        m = main.re_keyword.match(self.buf)
        if m == None:
            main.err_add(self.errors, self.pos,
                         'UNEXPECTED_KEYWORD', self.buf)
            raise Abort
        else:
            self.set_buf(m.end())
            if m.group(2) == None: # no prefix
                return m.group(4)
            else:
                return (m.group(2), m.group(4))

    def peek(self):
        """Return next real character in input stream.

        Skips whitespace and comments, and returns next character
        withoyt consuming it.  Use skip_tok() to consume the characater.
        """
        self.skip()
        try:
            return self.buf[0]
        except:
            raise Eof

    def skip_tok(self):
        self.skip()
        self.set_buf(1)
    
    def get_string(self, need_quote=False):
        """ret: string"""
        self.skip()
        
        if self.buf[0] == ';' or self.buf[0] == '{' or self.buf[0] == '}':
            main.err_add(self.errors, self.pos,
                         'EXPECTED_ARGUMENT', self.buf[0])
            raise Abort
        if self.buf[0] == '"' or self.buf[0] == "'":
            # for double-quoted string,  loop over string and translate
            # escaped characters.  also strip leading whitespace as
            # necessary.
            # for single-quoted string, keep going until end quote is found.
            quote_char = self.buf[0]
            # collect output in strs (list of strings)
            strs = [] 
            # remember position of " character
            indentpos = self.offset
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
                                main.err_add(self.errors, self.pos,
                                             'EXPECTED_QUOTED_STRING', ())
                                raise Abort
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
            main.err_add(self.errors, self.pos, 'EXPECTED_QUOTED_STRING', ())
            raise Abort
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


class YangParser(object):
    def __init__(self):
        self.module = None
        pass

    def parse(self, ctx, filename):
        """Parse the file containing a YANG (sub)module.

        Return a Statement on success or None on failure
        """

        self.ctx = ctx
        self.pos = main.Position(filename)

        try:
            fd = open(filename, "r")
            self.tokenizer = YangTokenizer(fd, self.pos, ctx.errors)
            module = self._parse_statement(None)
        except Abort:
            return None
        except Eof, e:
            main.err_add(self.ctx.errors, self.pos, 'EOF_ERROR', ())
            return None
        except IOError, ex:
            main.err_add(self.ctx.errors, self.pos, 'IO_ERROR', str(ex))
            return None
        try:
            # we expect a Eof at this point, everything else is an error
            self.tokenizer.peek()
        except Eof:
            return module
        except:
            pass
        main.err_add(self.ctx.errors, self.pos, 'TRAILING_GARBAGE', ())
        return None

    def _parse_statement(self, parent):
        keywd = self.tokenizer.get_keyword()
        if not is_prefixed(keywd):
            # this is a core YANG keyword
            try:
                (arg_type, _children) = grammar.stmt_map[keywd]
            except KeyError:
                main.err_add(self.ctx.errors, self.pos,
                             'UNKNOWN_KEYWORD', keywd)
            # check if the statement needs an argument
            if arg_type is not None:
                arg = self.tokenizer.get_string()
                # verify the argument syntax
                if (arg_type != 'string' and
                    syntax.arg_type_map[arg_type].search(arg) is None):
                    main.err_add(self.ctx.errors, self.pos,
                                 'BAD_VALUE', (arg, arg_type))
            else:
                arg = None
            # instantiate a class representing this statement
            if parent == None:
                stmt = self._top_stmt(keywd, arg)
                self.module = stmt
            else:
                try:
                    handle = grammar.handler_map[keywd]
                    stmt = handle(parent, self.pos, self.module, arg)
                except KeyError:
                    stmt = main.Statement(parent, self.pos, keywd,
                                          self.module, arg)
        else:
            # this is an extension
            # read optional argument
            tok = self.tokenizer.peek()
            if tok == '{' or tok == ';':
                arg = None
            else:
                arg = self.tokenizer.get_string()
            (prefix, identifier) = keywd # FIXME: rewrite ExtensionStmt
            stmt = main.ExtensionStatement(parent, self.pos, identifier,
                                           prefix, arg)
        # check for substatements
        tok = self.tokenizer.peek()
        if tok == '{':
            self.tokenizer.skip_tok() # skip the '{'
            while self.tokenizer.peek() != '}':
                substmt = self._parse_statement(stmt)
                stmt.substmts.append(substmt)
            self.tokenizer.skip_tok() # skip the '}'
        elif tok == ';':
            self.tokenizer.skip_tok() # skip the ';'
        else:
            main.err_add(self.ctx.errors, self.pos, 'INCOMPLETE_STATEMENT', tok)
            raise Abort
        return stmt

    def _top_stmt(keywd, arg):
        if keywd == 'module':
            is_submodule = False
        elif keywd == 'submodule':
            is_submodule = True
        else:
            main.err_add(self.ctx.errors, self.pos,
                         'UNEXPECTED_KEYWORD_N',
                         (keywd, ('module', 'submodule')))
            raise Abort
        return main.Module(self.pos, self.ctx, arg, is_submodule),

# FIXME: tmp debug
import sys

def ppkeywd(tok):
    if is_prefixed(tok):
        return tok[0] + ':' + tok[1]
    else:
        return tok

def pp(s, indent=0):
    sys.stdout.write(" " * indent + ppkeywd(s.keyword))
    if s.arg is not None:
        sys.stdout.write(" '" + s.arg + "'")
    if s.substmts == []:
        sys.stdout.write(";\n")
    else:
        sys.stdout.write(" {\n")
        for ss in s.substmts:
            pp(ss, indent+4)
        sys.stdout.write(" " * indent + "}\n")
        
