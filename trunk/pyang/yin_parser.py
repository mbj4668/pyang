import sys

from xml.parsers import expat
import copy

import syntax
import grammar
import error
import statements
import util

yin_namespace = "urn:ietf:params:xml:ns:yang:yin:1"

# We're using expat to parse to our own primitive dom-like
# structure, because we need to keep track of the linenumber per
# statement.  And expat is easier to work with than minidom.
class Element(object):
    def __init__(self, ns, local_name, attrs, pos):
        self.ns = ns
        self.local_name = local_name
        self.attrs = attrs
        self.pos = copy.copy(pos)
        self.children = []
        self.data = ''

    def find_child(self, ns, local_name):
        for ch in self.children:
            if ch.ns == ns and ch.local_name == local_name:
                return ch
        return None

    def remove_child(self, ch):
        self.children.remove(ch)

    def find_attribute(self, name):
        try:
            return self.attrs[name]
        except KeyError:
            return None

    def remove_attribute(self, name):
        del self.attrs[name]

class YinParser(object):

    ns_sep = "}"
    """namespace separator"""

    def __init__(self):
        self.parser = expat.ParserCreate("UTF-8", self.ns_sep)
        self.parser.CharacterDataHandler = self.char_data
        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element

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

    def parse(self, ctx, ref, text):
        """Parse the string `text` containing a YIN (sub)module.

        Return a Statement on success or None on failure.
        """

        self.ctx = ctx
        self.pos = error.Position(ref)
        self.top = None

        self.uri = None
        self.nsmap = {}
        self.prefixmap = {}
        self.included = []
        self.extensions = {}

        self.data = ''
        self.element_stack = []

        try:
            self.parser.Parse(text, True)
        except error.Abort:
            return None
        except expat.ExpatError, ex:
            self.pos.line = ex.lineno
            error.err_add(self.ctx.errors, self.pos, 'SYNTAX_ERROR',
                          str(ex).split(":")[0])
            return None

        self.look_ahead()
        top_element = self.top
        self.top = None
        self.create_statement(top_element, None)
        return self.top

    def get_lineno(self):
        """Return current line of the parser."""

        return self.parser.CurrentLineNumber
    lineno = property(get_lineno, doc="parser position")

    # Handlers for Expat events

    def start_element(self, name, attrs):
        name = str(name) # convert from unicode strings
        self.pos.line = self.lineno
        (ns, local_name) = self.split_qname(name)
        e = Element(ns, local_name, attrs, self.pos)
        if self.data.lstrip() != '':
            error.err_add(self.ctx.errors, self.pos, 'SYNTAX_ERROR',
                          "unexpected element - mixed content")
        self.data = ''
        if self.element_stack == []:
            # this is the top-level element
            self.top = e
            self.element_stack.append(e)
            return
        else:
            parent = self.element_stack[-1]
            parent.children.append(e)
            self.element_stack.append(e)

    def char_data(self, data):
        self.data += data

    def end_element(self, name):
        self.pos.line = self.lineno
        e = self.element_stack[-1]
        e.data = self.data
        self.data = ''
        # end of statement, pop from stack
        del self.element_stack[-1]

    # Builds the statement tree

    def create_statement(self, e, parent):
        if e.ns == yin_namespace:
            keywd = e.local_name
            try:
                (argname, arg_is_elem) = syntax.yin_map[keywd]
            except KeyError:
                error.err_add(self.ctx.errors, e.pos,
                              'UNKNOWN_KEYWORD', keywd)
                return None
        else:
            # extension
            try:
                prefix = self.prefixmap[e.ns]
            except KeyError:
                error.err_add(self.ctx.errors, e.pos,
                              'UNKNOWN_KEYWORD', e.local_name)
                return None
            keywd = (prefix, e.local_name)
            keywdstr = util.keyword_to_str(keywd)
            res = self.find_extension(e.ns, e.local_name)
            if res is None:
                error.err_add(self.ctx.errors, e.pos,
                              'UNKNOWN_KEYWORD', keywdstr)
                return None
            (arg_is_elem, argname)  = res

        keywdstr = util.keyword_to_str(keywd)
        if arg_is_elem == True:
            # find the argument element
            arg_elem = e.find_child(e.ns, argname)
            if arg_elem is None:
                arg = None
                error.err_add(self.ctx.errors, e.pos,
                              'MISSING_ARGUMENT_ELEMENT', (argname, keywdstr))

            else:
                arg = arg_elem.data
                e.remove_child(arg_elem)
        elif arg_is_elem == False:
            arg = e.find_attribute(argname)
            if arg is None:
                error.err_add(self.ctx.errors, e.pos,
                              'MISSING_ARGUMENT_ATTRIBUTE', (argname, keywdstr))
            else:
                e.remove_attribute(argname)
        else:
            # no arguments
            arg = None

        self.check_attr(e.pos, e.attrs)
            
        stmt = statements.Statement(self.top, parent, e.pos, keywd, arg)
        if self.top is None:
            self.pos.top_name = arg
            self.top = stmt
        else:
            parent.substmts.append(stmt)

        for ch in e.children:
            self.create_statement(ch, stmt)
            
    def check_attr(self, pos, attrs):
        """Check for unknown attributes."""

        for at in attrs:
            (ns, local_name) = self.split_qname(at)
            if ns is None:
                error.err_add(self.ctx.errors, pos,
                              'UNEXPECTED_ATTRIBUTE', local_name)
            elif ns == yin_namespace:
                error.err_add(self.ctx.errors, pos,
                              'UNEXPECTED_ATTRIBUTE', "{"+at)
            # allow foreign attributes
            # FIXME: hmm... is this the right thing to do?
            # these things are supposed to be handled with extensions...

    def look_ahead(self):
        # To find an extension <smi:oid> we need to find the module
        # that corresponds to 'smi'.  We get extension's URI from expat,
        # so we need a map from URI -> module.  This works for
        # imported modules, but for extensions defined in the local
        # module we have to check if the extension's URI is
        # the local URI.
        # 
        # If we're a submodule, we need to find our module's
        # namespace, so we need to parse the module :(
        # This could be fixed if the spec required the XML prefix
        # be the same as the YANG belongs-to prefix.

        # 1.  find our own namespace URI
        if self.top.local_name == 'module':
            p = self.top.find_child(yin_namespace, 'namespace')
            if p is not None:
                self.uri = p.find_attribute('uri')
            p = self.top.find_child(yin_namespace, 'prefix')
            if p is not None:
                self.prefixmap[self.uri] = p.find_attribute('value')
        elif self.top.local_name == 'submodule':
            p = self.top.find_child(yin_namespace, 'belongs-to')
            modname = p.find_attribute('module')
            # read the parent module in order to find the namespace uri
            res = self.ctx.read_module(modname)
            if res == 'not_found':
                error.err_add(self.ctx.errors, p.pos,
                              'MODULE_NOT_FOUND', modname)
            elif type(res) == type(()) and res[0] == 'read_error':
                error.err_add(self.ctx.errors, p.pos, 'READ_ERROR', res[1])
            elif res == None:
                pass
            else:
                namespace = res.search_one('namespace')
                if namespace is None or namespace.arg is None:
                    pass
                else:
                    # success - save our uri
                    self.uri = namespace.arg
        else:
            return

        # 2.  read all imports and includes and add the modules to the context
        #     and to the nsmap.
        for ch in self.top.children:
            if ch.ns == yin_namespace and ch.local_name == 'import':
                modname = ch.find_attribute('module')
                if modname is not None:
                    mod = self.ctx.search_module(ch.pos, modname)
                    if mod is not None:
                        ns = mod.search_one('namespace')
                        if ns is not None and ns.arg is not None:
                            # record the uri->mod mapping
                            self.nsmap[ns.arg] = mod
                            # also record uri->prefix, where prefix
                            # is the *yang* prefix, *not* the XML prefix
                            # (it can be different in theory...)
                            p = ch.find_child(yin_namespace, 'prefix')
                            if p is not None:
                                prefix = p.find_attribute('value')
                                if prefix is not None:
                                    self.prefixmap[ns.arg] = prefix
                            
            elif ch.ns == yin_namespace and ch.local_name == 'include':
                modname = ch.find_attribute('module')
                if modname is not None:
                    mod = self.ctx.search_module(ch.pos, modname)
                    if mod is not None:
                        self.included.append(mod)

        # 3.  find all extensions defined locally
        for ch in self.top.children:
            if ch.ns == yin_namespace and ch.local_name == 'extension':
                extname = ch.find_attribute('name')
                if extname is None:
                    continue
                arg = ch.find_child(yin_namespace, 'argument')
                if arg is None:
                    self.extensions[extname] = (None, None)
                else:
                    argname = arg.find_attribute('name')
                    if argname is None:
                        continue
                    arg_is_elem = arg.find_child(yin_namespace, 'yin-element')
                    if arg_is_elem is None:
                        self.extensions[extname] = (False, argname)
                        continue
                    val = arg_is_elem.find_attribute('value')
                    if val == 'false':
                        self.extensions[extname] = (False, argname)
                    elif val == 'true':
                        self.extensions[extname] = (True, argname)

    def find_extension(self, uri, extname):
        def find_in_mod(mod):
            ext = mod.search_one('extension', extname)
            if ext is None:
                return None
            ext_arg = ext.search_one('argument')
            if ext_arg is None:
                return (None, None)
            arg_is_elem = ext_arg.search_one('yin-element')
            if arg_is_elem is None or arg_is_elem.arg == 'false':
                return (False, ext_arg.arg)
            else:
                return (True, ext_arg.arg)

        if uri == self.uri:
            # extension is defined locally or in one of our submodules
            try:
                return self.extensions[extname]
            except KeyError:
                pass
            # check submodules
            for submod in self.included:
                res = find_in_mod(submod)
                if res is not None:
                    return res
            return None
        else:
            try:
                mod = self.nsmap[uri]
                return find_in_mod(mod)
            except KeyError:
                return None
