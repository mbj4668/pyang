### tokenizer

import main

### tokens

T_SEMICOLON   = 1
T_OPEN_BRACE  = 2
T_CLOSE_BRACE = 3

def is_tok(tok):
    return type(tok) == type(T_SEMICOLON)

def tok_to_str(tok):
    if type(tok) == type(''):
        return tok
    elif main.is_prefixed(tok):
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
            raise main.Eof()
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

        m = main.re_keyword.match(self.buf)
        if m == None:
            main.err_add(self.errors, self.pos,
                         'UNEXPECTED_KEYWORD', self.buf)
            raise main.Abort
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
                                main.err_add(self.errors, self.pos,
                                             'EXPECTED_QUOTED_STRING', ())
                                raise main.Abort
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
            raise main.Abort
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

