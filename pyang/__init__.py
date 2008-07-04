"""The pyang library for parsing, validating, and converting YANG modules"""

import os
import string
import sys

import error
import yang_parser
import yin_parser
import grammar
import util

__version__ = '0.9.6c'

class Context(object):
    """Class which encapsulates a parse session"""

    def __init__(self, repository):
        """`repository` is a `Repository` instance"""
        
        self.modules = {}
        """dict of modulename:<class Module>)"""
        
        self.module_list = []
        """ordered list of modules; we must validate in this order"""
        
        self.repository = repository
        self.errors = []
        self.canonical = False
        self.submodule_expansion = True

    def add_module(self, ref, text, format=None):
        """Parse a module text and add the module data to the context

        `ref` is a string which is used to identify the source of
              the text for the user.  used in error messages
        `text` is the raw text data
        `format` is one of 'yang' or 'yin'.

        Returns the parsed module on success, and None on error.
        """

        if format == None:
            format = util.guess_format(text)

        if format == 'yin':
            p = yin_parser.YinParser()
        else:
            p = yang_parser.YangParser()

        module = p.parse(self, ref, text)
        if module == None:
            return None

        grammar.chk_module_statements(self, module, self.canonical)
        self._set_attrs(module)

        if module.name not in self.modules or self.modules[module.name] == None:
            self.modules[module.name] = module
            self.module_list.append(module)
        return module

    def del_module(self, module):
        """Remove a module from the context"""

        del self.modules[module.name]
        self.module_list.remove(module)

    def search_module(self, pos, modulename):
        """Searches for a module named `modulename` in the repository

        If the module is found, it is added to the context.
        Returns the module if found, and None otherwise"""
        if modulename in self.modules:
            return self.modules[modulename]
        try:
            r = self.repository.get_module(modulename)
            if r == None:
                error.err_add(self.errors, pos, 'MODULE_NOT_FOUND', modulename)
                self.modules[modulename] = None
                return None
        except self.repository.ReadError, ex:
            error.err_add(self.errors, pos, 'READ_ERROR', str(ex))
        (ref, format, text) = r
        module = self.add_module(ref, text, format)
        if modulename != module.name:
            error.err_add(self.errors, module.pos, 'BAD_MODULE_FILENAME',
                          (module.name, filename, modulename))
            self.del_module(module)
            self.modules[modulename] = None
            return None
        return module

    def _set_attrs(self, stmt):
        """temporary function which sets class attributes for substatements"""

        def get_occurance(subkeywd):
            def find(spec):
                for (keywd, occ) in spec:
                    if keywd == subkeywd:
                        return occ
                    if keywd == '$choice':
                        for s in occ:
                            r = find(s)
                            if r is not None:
                                return r
                    if keywd == '$interleave':
                        r = find(occ)
                        if r is not None:
                            return r
                return None
            if util.is_prefixed(stmt.keyword): return '*'
            (_arg_type, children) = grammar.stmt_map[stmt.keyword]
            return find(children)

        def get_attr(keywd):
            if keywd == 'import': return "import_"
            if keywd in ['leaf', 'container', 'leaf-list', 'list', 'anyxml',
                         'case', 'choice', 'uses', 'rpc', 'notification']:
                return 'children'
            if util.is_prefixed(keywd): return None
            return keywd.replace('-','_')

        for s in stmt.substmts:
            occurance = get_occurance(s.keyword)
            attr = get_attr(s.keyword)
            if attr is not None and attr in stmt.__dict__:
                if occurance == '?' or occurance == '1':
                    # single-instance attribute
                    stmt.__dict__[attr] = s
                else:
                    # make sure the substmt is not already defined
                    if (s.keyword != 'augment' and
                        s.keyword != 'type' and
                        util.attrsearch(s.arg, 'arg', stmt.__dict__[attr])):
                        error.err_add(self.errors, s.pos,
                                      'DUPLICATE_STATEMENT', s.arg)
                    stmt.__dict__[attr].append(s)
            self._set_attrs(s)
            if s.keyword == 'import':
                s.parent.set_import(s)
            elif s.keyword == 'include':
                s.parent.set_include(s)

    def validate(self):
        uris = {}
        for modname in self.modules:
            m = self.modules[modname]
            if m != None and m.namespace != None:
                uri = m.namespace.arg
                if uri in uris:
                    error.err_add(self.errors, m.namespace.pos,
                                  'DUPLICATE_NAMESPACE', (uri, uris[uri]))
                else:
                    uris[uri] = m.name
        for m in self.module_list:
            if m != None:
                m.validate()

class Repository(object):
    """Abstract base class that represents a module repository"""

    def __init__(self):
        pass

    def get_module(self, modulename):
        """Return the raw module text from the repository

        Returns (`ref`, `format`, `text`) if found, or None if not found.
        `ref` is a string which is used to identify the source of
              the text for the user.  used in error messages
        `format` is one of 'yang' or 'yin'.
        `text` is the raw text data

        Raises `ReadError`
        """

    class ReadError(Exception):
        """Signals that an error occured during module retrieval"""

        def __init__(self, str):
            Exception.__init__(self, str)

class FileRepository(Repository):
    def __init__(self, path=""):
        """Create a Repository which searches the filesystem for modules

        `path` is a ':'-separated string of directories
        """
        basedir = os.path.split(sys.modules['pyang'].__file__)[0]
        path = path + ':' + basedir + '/../modules' + ':.'
        Repository.__init__(self)
        self.path = path

    def _search_file(self, filename):
        """Given a search path, find file"""

        paths = string.split(self.path, os.pathsep)
        for path in paths:
            fname = os.path.join(path, filename)
            if fname.startswith("./"):
                fname = fname[2:]
            if os.path.exists(fname):
                return fname
        return None

    def get_module(self, modulename):
        filename = self._search_file(modulename + ".yang")
        format = 'yang'
        if filename == None:
            filename = self._search_file(modulename + ".yin")
            format = 'yin'
        if filename == None:
            filename = self._search_file(modulename)
            format = None
        if filename == None:
            return None
        try:
            fd = file(filename)
            text = fd.read()
        except IOError, ex:
            raise self.ReadError(filename + ": " + str(ex))

        if format is None:
            format = util.guess_format(text)
        return (filename, format, text)
