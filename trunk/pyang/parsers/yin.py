import sys

from xml.parsers import expat

import syntax
import grammar
from pyang import main

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

    def parse(self, ctx, filename):
        """Parse the file containing a YIN (sub)module.

        Return a Statement on success or None on failure
        """

        self.ctx = ctx
        self.pos = main.Position(filename)
        self.argument = None
        self.root = None

        try:
            fd = open(filename, "r")
            self.parser.ParseFile(fd)
        except expat.ExpatError, ex:
            print ex
            self.pos.line = ex.lineno
            main.err_add(self.ctx.errors, self.pos, 'SYNTAX_ERROR',
                         str(ex).split(":")[0])
            return None
        except IOError, ex:
            main.err_add(self.ctx.errors, self.pos, 'IO_ERROR', str(ex))
            return None

        return self.root

    def get_lineno(self):
        """Return current line of the parser."""

        return self.parser.CurrentLineNumber
    lineno = property(get_lineno, doc="parser position")

    def set_arg_from_attr(self, stmt, name, attribs):
        """Set argument of `stmt` from attribute `name` in `attribs`."""

        try:
            stmt.arg = attribs[name]
            del attribs[name]
        except KeyError:
            main.err_add(self.ctx.errors, stmt.pos,
                         'MISSING_ARGUMENT_ATTRIBUTE', name)

    def check_attr(self, stmt, attribs):
        """Check for unknown attributes."""

        for at in attribs:
            (ns, local_name) = self.split_qname(at)
            if ns is None:
                main.err_add(self.ctx.errors, stmt.pos,
                             'UNEXPECTED_ATTRIBUTE', local_name)
            if ns == yin_namespace:
                main.err_add(self.ctx.errors, stmt.pos,
                             'UNEXPECTED_ATTRIBUTE', "{"+at)
        
    # Handlers for Expat events

    def char_data(self, data):
        if self.argument is not None:
            self.argument += data
            return
        stripped = data.lstrip()
        if len(stripped) > 0:
            self.pos.line = self.lineno
            main.err_add(self.ctx.errors, self.pos, 'SYNTAX_ERROR',
                         "unexpected character data")

    def start_element(self, name, attrs):
        self.pos.line = self.lineno
        if self.argument is not None:
            main.err_add(self.ctx.errors, self.pos, 'SYNTAX_ERROR',
                         "invalid argument - mixed content")
        (ns, local_name) = self.split_qname(name)
        if self.stmt_stack == []:  # root element
            if ns != yin_namespace:
                # FIXME: error - extension on top-level
                return
            self.root = main.Statement(None, self.pos, local_name, None, None)
            self.set_arg_from_attr(self.root, "name", attrs)
            self.stmt_stack.append(self.root)
            return
        parent = self.stmt_stack[-1]
        # FIXME: yin_map doesn't work for extensions - we need to parse
        # the corresponding extension statement in order to do this
        # correctly :(  sigh...
        # we need to do that in a separate pass
        # As an alternative, we could skip extensions unless a plugin has
        # registered the argument syntax and extenstion grammar.
        # The downside of this is that we won't be able to translate
        # to yang :(
        (parg_iselem, pargname) = syntax.yin_map[parent.keyword]
        if parg_iselem and local_name == pargname:
            # this element contains the argument for its parent
            # read the argument data in char_data
            self.argument = ""
            return
        yst = main.Statement(parent, self.pos, local_name, self.root, None)
        parent.substmts.append(yst)
        self.stmt_stack.append(yst)
        try:
            (arg_is_elem, argname) = syntax.yin_map[local_name]
        except KeyError:
            main.err_add(self.ctx.errors, self.pos,
                         'UNKNOWN_KEYWORD', local_name)
        if arg_is_elem == True:
            self.arg_name = argname
        elif arg_is_elem == False:
            self.set_arg_from_attr(yst, argname, attrs)
        else:
            # no argument
            pass
        self.check_attr(yst, attrs)

    def end_element(self, name):
        stmt = self.stmt_stack[-1]
        if self.argument is not None:
            stmt.arg = self.argument
            self.argument = None
            return
        (ns, local_name) = self.split_qname(name)
        if stmt.arg is None:
            (arg_is_elem, argname) = syntax.yin_map[stmt.keyword]
            if arg_is_elem == True and argname is not None:
                main.err_add(self.ctx.errors, stmt.pos,
                             'MISSING_ARGUMENT_ELEMENT', argname)
        del self.stmt_stack[-1]
