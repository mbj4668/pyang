import sys

from xml.parsers import expat

import syntax
import grammar
import error
import statements

yin_namespace = "urn:ietf:params:xml:ns:yang:yin:1"

class YinParser(object):

    ns_sep = "}"
    """namespace separator"""

    def split_qname(qname):
        """Split `qname` into namespace URI and local name

        Return namespace and local name as a tuple. This is a static
        method."""
        res = qname.split(YinParser.ns_sep)
        if len(res) == 1:       # no namespace
            return None, res[0]
        else:
            return res
    split_qname = staticmethod(split_qname)

    def __init__(self):
        self.parser = expat.ParserCreate("UTF-8", self.ns_sep)
        self.parser.CharacterDataHandler = self.char_data
        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element
        self.stmt_stack = []

    def parse(self, ctx, ref, text):
        """Parse the string `text` containing a YIN (sub)module.

        Return a Statement on success or None on failure
        """

        self.ctx = ctx
        self.pos = error.Position(ref)
        self.module = None
        self.argument = None
        self.statement_data = None
        self.is_extension = False

        try:
            self.parser.Parse(text, True)
        except error.Abort:
            return None
        except expat.ExpatError, ex:
            print ex
            self.pos.line = ex.lineno
            error.err_add(self.ctx.errors, self.pos, 'SYNTAX_ERROR',
                          str(ex).split(":")[0])
            return None

        return self.module

    def get_lineno(self):
        """Return current line of the parser."""

        return self.parser.CurrentLineNumber
    lineno = property(get_lineno, doc="parser position")

    def get_arg_from_attr(self, name, attribs):
        """Get argument of `stmt` from attribute `name` in `attribs`.

        If found, the attribute is removed from `attribs`."""

        try:
            arg = attribs[name]
            del attribs[name]
            return arg
        except KeyError:
            error.err_add(self.ctx.errors, self.pos,
                          'MISSING_ARGUMENT_ATTRIBUTE', name)
            raise error.Abort

    def check_attr(self, pos, attribs):
        """Check for unknown attributes."""

        for at in attribs:
            (ns, local_name) = self.split_qname(at)
            if ns is None:
                error.err_add(self.ctx.errors, pos,
                              'UNEXPECTED_ATTRIBUTE', local_name)
            if ns == yin_namespace:
                error.err_add(self.ctx.errors, pos,
                              'UNEXPECTED_ATTRIBUTE', "{"+at)
        
    # Handlers for Expat events

    def char_data(self, data):
        if self.is_extension:
            # just ignore data for extensions for now
            return
        if self.argument is not None:
            self.argument += data
            return
        stripped = data.lstrip()
        if len(stripped) > 0:
            self.pos.line = self.lineno
            error.err_add(self.ctx.errors, self.pos, 'SYNTAX_ERROR',
                          "unexpected character data")

    def start_element(self, name, attrs):
        name = str(name) # convert from unicode strings
        self.pos.line = self.lineno
        if self.argument is not None:
            error.err_add(self.ctx.errors, self.pos, 'SYNTAX_ERROR',
                          "invalid argument - mixed content")
        (ns, local_name) = self.split_qname(name)
        if self.stmt_stack == []:
            # this is the top-level element
            if ns != yin_namespace:
                # FIXME: error - extension on top-level
                return
            if local_name == 'module':
                is_submodule = False
            elif local_name == 'submodule':
                is_submodule = True
            else:
                error.err_add(self.ctx.errors, self.pos,
                              'UNEXPECTED_KEYWORD_N',
                              (local_name, ('module', 'submodule')))
                raise error.Abort
            arg = self.get_arg_from_attr('name', attrs)
            stmt = statements.Module(self.pos, self.ctx, arg, is_submodule)
            self.module = stmt
            self.check_attr(self.pos, attrs)
            self.stmt_stack.append(stmt)
            return

        if self.statement_data != None:
            (keywd, argname) = self.statement_data
            if local_name == argname:
                # this element contains the argument for its parent
                # read the argument data in char_data
                self.argument = ""
                return
            else:
                error.err_add(self.ctx.errors, self.pos,
                              'MISSING_ARGUMENT_ELEMENT', (argname, keywd))
                raise error.Abort
        # check if it is an extension
        if ns != yin_namespace:
            # FIXME: extensions currently just ignored!
            self.is_extension = True
            return

        # otherwise, this element is a YANG statement
        parent = self.stmt_stack[-1]
        try:
            # FIXME: yin_map doesn't work for extensions - we need to parse
            # the corresponding extension statement in order to do this
            # correctly :(  sigh...
            # we need to do that in a separate pass
            # As an alternative, we could skip extensions unless a plugin has
            # registered the argument syntax and extenstion grammar.
            # The downside of this is that we won't be able to translate
            # to yang :(
            (arg_is_elem, argname) = syntax.yin_map[local_name]
        except KeyError:
            error.err_add(self.ctx.errors, self.pos,
                          'UNKNOWN_KEYWORD', local_name)
            # push dummy statement on the stack
            self.stmt_stack.append(None)
            return
        if arg_is_elem == True:
            # remember this data and check for the next element; it will
            # contain the argument for this statement
            self.statement_data = (local_name, argname)
        else:
            if arg_is_elem == False:
                arg = self.get_arg_from_attr(argname, attrs)
            else:
                # no argument
                arg = None
            self.create_statement(parent, local_name, arg)
        self.check_attr(self.pos, attrs)

    def end_element(self, name):
        self.pos.line = self.lineno
        name = str(name) # convert from unicode strings
        (ns, local_name) = self.split_qname(name)
        if ns != yin_namespace:
            # FIXME: extensions currently just ignored!
            self.is_extension = False
            return
        if self.argument is not None:
            # end of argument element
            parent = self.stmt_stack[-1]
            arg = self.argument
            self.argument = None
            (keywd, argname) = self.statement_data
            self.statement_data = None
            self.create_statement(parent, keywd, arg)
        else:
            # end of statement, pop from stack
            del self.stmt_stack[-1]
        if self.statement_data is not None:
            # we were expecting an argument element, but got end
            # of statement
            (keywd, argname) = self.statement_data
            if argname is not None:
                error.err_add(self.ctx.errors, self.pos,
                              'MISSING_ARGUMENT_ELEMENT', (argname, keywd))
                raise error.Abort

    def create_statement(self, parent, keywd, arg):
        try:
            handle = grammar.handler_map[keywd]
            stmt = handle(parent, self.pos, self.module, arg)
        except KeyError:
            stmt = statements.Statement(parent, self.pos, keywd,
                                        self.module, arg)
        parent.substmts.append(stmt)
        self.stmt_stack.append(stmt)
