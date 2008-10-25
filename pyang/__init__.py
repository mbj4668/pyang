"""The pyang library for parsing, validating, and converting YANG modules"""

import os
import string
import sys
import zlib

import error
import yang_parser
import yin_parser
import grammar
import util

__version__ = '0.9.3pre1'

class Context(object):
    """Class which encapsulates a parse session"""

    def __init__(self, repository):
        """`repository` is a `Repository` instance"""
        
        self.modules = {}
        """dict of modulename:<class Module>)
        contains all modules and submodule found"""
        
        self.module_list = []
        """list of modules added explicitly to the Context"""
        
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

        Returns the parsed and validated module on success, and None on error.
        """
        module = self._add_module(ref, text, format)
        if module != None:
            self.module_list.append(module)
            return module

    def _add_module(self, ref, text, format=None):
        if format == None:
            format = util.guess_format(text)

        if format == 'yin':
            p = yin_parser.YinParser()
        else:
            p = yang_parser.YangParser()

        module = p.parse(self, ref, text)
        if module is None:
            return None
        if module.arg is None:
            error.err_add(self.errors, module.pos,
                          'EXPECTED_ARGUMENT', module.keyword)
            return None
        top_keywords = ['module', 'submodule']
        if module.keyword not in top_keywords:
            error.err_add(self.errors, module.pos,
                          'UNEXPECTED_KEYWORD_N', (module.keyword, top_keywords))
            return None
            

        module.i_adler32 = zlib.adler32(text)

        if module.arg in self.modules:
            other = self.modules[module.arg]
            if other.i_adler32 != module.i_adler32:
                error.err_add(self.errors, module.pos,
                              'DUPLICATE_MODULE', (module.arg, other.pos))
                return None
            # exactly same module
            return other

        self.modules[module.arg] = module
        statements.validate_module(self, module)

        return module

    def del_module(self, module):
        """Remove a module from the context"""

        del self.modules[module.arg]
        if module in self.module_list:
            self.module_list.remove(module)

    def get_module(self, modulename):
        if modulename in self.modules:
            return self.modules[modulename]
        else:
            return None

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
        module = self._add_module(ref, text, format)
        if modulename != module.arg:
            error.err_add(self.errors, module.pos, 'BAD_MODULE_FILENAME',
                          (module.arg, ref, modulename))
            self.del_module(module)
            self.modules[modulename] = None
            return None
        return module

    def read_module(self, modulename):
        """Searches for a module named `modulename` in the repository

        The module is just read, and not compiled at all.
        Returns the module if found, and None otherwise"""
        if modulename in self.modules:
            return self.modules[modulename]
        try:
            r = self.repository.get_module(modulename)
            if r == None:
                return 'not_found'
        except self.repository.ReadError, ex:
            return ('read_error', ex)

        (ref, format, text) = r

        if format == None:
            format = util.guess_format(text)

        if format == 'yin':
            p = yin_parser.YinParser()
        else:
            p = yang_parser.YangParser()

        return p.parse(self, ref, text)

    def validate(self):
        uris = {}
        for modname in self.modules:
            m = self.modules[modname]
            if m != None:
                namespace = m.search_one('namespace')
                if namespace != None:
                    uri = namespace.arg
                    if uri in uris:
                        error.err_add(self.errors, namespace.pos,
                                      'DUPLICATE_NAMESPACE', (uri, uris[uri]))
                    else:
                        uris[uri] = m.arg
   #     for m in self.module_list:
   #         if m != None:
   #             m.validate()

class Repository(object):
    """Abstract base class that represents a module repository"""

    def __init__(self):
        pass

    def get_module(self, modulename):
        """Return the raw module text from the repository

        Returns (`ref`, `format`, `text`) if found, or None if not found.
        `ref` is a string which is used to identify the source of
              the text for the user.  used in error messages
        `format` is one of 'yang' or 'yin' or None.
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

        `path` is a `os.pathsep`-separated string of directories
        """

        # add standard search path
        path += os.pathsep + '.'

        modpath = os.getenv('YANG_MODPATH')
        if modpath is not None:
            path += os.pathsep + modpath

        home = os.getenv('HOME')
        if home is not None:
            path += os.pathsep + os.path.join(home, 'yang', 'modules')

        inst = os.getenv('YANG_INSTALL')
        if inst is not None:
            path += os.pathsep + os.path.join(inst, 'yang', 'modules')
        else:
            path += os.pathsep + \
                os.path.join(sys.prefix, 'share', 'yang', 'modules')

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
