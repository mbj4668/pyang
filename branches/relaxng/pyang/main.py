import sys
import os
import string
import re
import optparse
import copy
#import traceback # for debugging. use: traceback.print_stack()
import time
import libxml2
import types

import pyang.plugin
import tokenizer

from util import attrsearch, keysearch, dictsearch

pyang_version = '0.9.0b'

### Exceptions

class Abort(Exception):
    """used for non-recoverable errors to abort parsing"""
    pass

class Eof(Exception):
    """raised by tokenizer when end of file is detected"""
    pass


class NotFound(Exception):
    """used when a referenced item is not found"""
    pass

### error codes

error_codes = \
    {
    'EOF_ERROR':
      (1,
       'premature end of file'),
    'EXPECTED_QUOTED_STRING':
      (1,
       'expected quoted string after \'+\' operator'),
    'UNEXPECTED_KEYWORD':
      (1,
       'unexpected keyword "%s"'),
    'UNEXPECTED_KEYWORD_1':
      (1,
       'unexpected keyword "%s", expected %s'),
    'UNEXPECTED_KEYWORD_N':
      (1,
       'unexpected keyword "%s", expected one of %s'),
    'UNEXPECTED_TOKEN':
      (1,
       'unexpected token "%s"'),
    'UNEXPECTED_TOKEN_1':
      (1,
       'unexpected token "%s", expected %s'),
    'UNEXPECTED_TOKEN_N':
      (1,
       'unexpected token "%s", expected one of %s'),
    'EXPECTED_ARGUMENT':
      (1,
       'expected an argument, got "%s"'),
    'TRAILING_GARBAGE':
      (2,
       'trailing garbage after module'),
    'BAD_VALUE':
      (1,
       'bad value "%s" for %s'),
    'CIRCULAR_DEPENDENCY':
      (1,
       'circular dependency for %s "%s"'),
    'MODULE_NOT_FOUND':
      (1,
       'module "%s" not found in search path'),
    'BAD_MODULE_FILENAME':
    (2,
       'unexpected modulename "%s" in file %s should be %s'),
    'BAD_SUB_BELONGS_TO':
      (1,
       'module %s includes %s, but %s does not specifiy a correct belongs-to'),
    'PREFIX_ALREADY_USED':
      (1,
       'prefix "%s" already used for module %s'),
    'PREFIX_NOT_DEFINED':
      (1,
       'prefix "%s" is not defined'),
    'NODE_NOT_FOUND':
      (1,
       'node %s::%s is not found'),
    'EXTENSION_NOT_DEFINED':
      (1,
       'extension "%s" is not defined in module %s'),
    'TYPE_NOT_FOUND':
      (1,
       'type "%s" not found in module %s'),
    'GROUPING_NOT_FOUND':
      (1,
       'grouping "%s" not found in module %s'),
    'DEFAULT_CASE_NOT_FOUND':
      (1,
       'the default case "%s" is not found"'),
    'NODE_NOT_IN_GROUPING':
      (1,
       'the node "%s" is not found in the grouping at this position'),
    'NODE_GROUPING_TYPE':
      (1,
       'the node "%s" does not match the type in the grouping'),
    'RANGE_BOUNDS':
      (2,
       'range error: "%s" is not larger than %s'),
    'LENGTH_BOUNDS':
      (2,
       'length error: "%s" is not larger than %s'),
    'LENGTH_VALUE':
      (2,
       'length error: "%s" is too large'),
    'TYPE_VALUE':
      (2,
       'the value "%s" does not match its base type %s- %s'),
    'DUPLICATE_ENUM_VALUE':
      (1,
       'the integer value "%d" has already been used for the ' \
       'enumeration'),
    'ENUM_VALUE':
      (1,
       'the enumeration value "%s" is not an 32 bit integer'),
    'DUPLICATE_BIT_POSITION':
      (1,
       'the position "%d" has already been used for another bit'),
    'BIT_POSITION':
      (1,
       'the position value "%s" is not valid'),
    'NEED_KEY':
      (1,
       'The list needs at least one key'),
    'NEED_KEY_USES':
      (1,
       'The list at "%s" needs at least one key because it is used as config'),
    'BAD_KEY':
      (1,
       'The key "%s" does not reference an existing leaf'),
    'BAD_UNIQUE':
      (1,
       'The unique argument "%s" does not reference an existing leaf'),
    'BAD_UNIQUE_PART':
      (1,
       'The identifier "%s" in the unique argument does not reference '
       'an existing container or list'),
    'DUPLICATE_KEY':
      (1,
       'The key "%s" must not be used more than once'),
    'DUPLICATE_UNIQUE':
      (3,
       'The leaf "%s" occurs more than once in the unique expression'),
    'PATTERN_ERROR':
      (2,
       'syntax error in pattern: %s'),
    'KEYREF_TOO_MANY_UP':
      (1,
       'the keyref path for %s at %s has too many ".."'),
    'KEYREF_IDENTIFIER_NOT_FOUND':
      (1,
       '%s::%s in the keyref path for %s at %s is not found'),
    'KEYREF_IDENTIFIER_BAD_NODE':
      (1,
       '%s::%s in the keyref path for %s at %s references a %s node'),
    'KEYREF_BAD_PREDICATE':
      (1,
       '%s::%s in the keyref path for %s at %s has a predicate, '
       'but is not a list'),
    'KEYREF_BAD_PREDICATE_PTR':
      (1,
       '%s::%s in the keyref path\'s predicate for %s at %s is compared '
       'with a leaf that is not a correct keyref'),
    'KEYREF_NOT_LEAF_KEY':
      (1,
       'the keyref path for %s at %s does not refer to a key leaf in a list'),
    'KEYREF_NO_KEY':
      (1,
       '%s::%s in the keyref path for %s at %s is not the name of a key leaf'),
    'KEYREF_MULTIPLE_KEYS':
      (1,
       '%s::%s in the keyref path for %s at %s is referenced more than once'),
    'DUPLICATE_CHILD_NAME':
      (1,
       'there is already a child node with the name "%s"'),
    'BAD_TYPE_NAME':
      (1,
       'illegal type name "%s"'),
    'TYPE_ALREADY_DEFINED':
      (1,
       'type name "%s" is already defined at %s'),
    'GROUPING_ALREADY_DEFINED':
      (1,
       'grouping name "%s" is already defined at %s'),
    'BAD_RESTRICTION':
      (1,
       'restriction %s not allowed for this base type'),
    'BAD_DEFAULT_VALUE':
      (1,
       'the type "%s" cannot have a default value'),
    'MISSING_TYPE_SPEC':
      (1,
       'a type %s must have at least one %s statement'),
    'BAD_TYPE_IN_UNION':
      (1,
       'the type %s cannot be part of a union'),
    'BAD_TYPE_IN_KEY':
      (1,
       'the type %s cannot be part of a key'),
    'DUPLICATE_STATEMENT':
      (1,
       'multiple statements with the same argument "%s" found'),
    'DEFAULT_AND_MANDATORY':
      (1,
       'a \'default\' value cannot be given when \'mandatory\' is "true"'),
    'CURRENT_USES_DEPRECATED':
      (2,
       'the %s definiton is current, but the %s it references is deprecated'),
    'CURRENT_USES_OBSOLETE':
      (2,
       'the %s definiton is current, but the %s it references is obsolete'),
    'DEPRECATED_USES_OBSOLETE':
      (3,
       'the %s definiton is deprecated, but the %s it references is obsolete'),
    'REVISION_ORDER':
      (3,
       'the revision statements are not given in reverse chronological order'),
    'EXTENSION_ARGUMENT_PRESENT':
      (1,
       'unexpected argument for extension %s'),
    'EXTENSION_NO_ARGUMENT_PRESENT':
      (1,
       'expected argument for extension %s'),
    'SYNTAX_ERROR':
      (1,
       'syntax error: %s'),
    'DUPLICATE_NAMESPACE':
      (1,
       'duplicate namespace uri %s found in module %s'),
    }

def err_level(tag):
    try:
        (level, fmt) = error_codes[tag]
        return level
    except KeyError:
        return 0

def err_to_str(tag, args):
    try:
        (level, fmt) = error_codes[tag]
        return fmt % args
    except KeyError:
        return 'unknown error %s' % tag

def err_add(errors, pos, tag, args):
    errors.append((copy.copy(pos), tag, args))

### regular expressions

re_prefix_str = '([a-z_]([a-z0-9\-_\.])*)'
re_identifier_str = '([a-z_]([a-z0-9\-_\.])*)'
re_keyword_str = '(' + re_prefix_str + ':)?' + re_identifier_str

re_identifier = re.compile('^' + re_identifier_str + '$', re.IGNORECASE)

re_keyword = re.compile('^' + re_keyword_str, re.IGNORECASE)

re_range_str = '((\-INF|min|max|((\+|\-)?[0-9]+(\.[0-9]+)?))\s*' \
               '(\.\.\s*' \
               '(INF|min|max|(\+|\-)?[0-9]+(\.[0-9]+)?)\s*)?)'
re_range = re.compile('^' + re_range_str + '(\|\s*' + re_range_str + ')*$')
re_range_part = re.compile(re_range_str)

re_length_str = '((min|max|[0-9]+)\s*' \
                '(\.\.\s*' \
                '(min|max|[0-9]+)\s*)?)'
re_length = re.compile('^' + re_length_str + '(\|\s*' + re_length_str + ')*$')
re_length_part = re.compile(re_length_str)

# schema node identifier
re_schema_nid = re.compile('^(/' + re_keyword_str + ')+$', re.IGNORECASE)
re_schema_nid_part = re.compile('/' + re_keyword_str, re.IGNORECASE)

# keypath
re_keypath = re.compile('^(/|(\.\./)+)' + re_keyword_str + \
                        '((\[\s*' + re_keyword_str + '\s*=\s*' + \
                        '\$this/(../)+(' + re_keyword_str + '/)*' + \
                        re_keyword_str + '\])*(/' + re_keyword_str + '))*$',
                        re.IGNORECASE)


# URI - RFC 3986, Appendix A
scheme = "[A-Za-z][-+.A-Za-z0-9]*"
unreserved = "[-._~A-Za-z0-9]"
pct_encoded = "%[0-9A-F]{2}"
sub_delims = "[!$&'()*+,;=]"
pchar = ("(" + unreserved + "|" + pct_encoded + "|" + 
         sub_delims + "|[:@])")
segment = pchar + "*"
segment_nz = pchar + "+"
userinfo = ("(" + unreserved + "|" + pct_encoded + "|" +
            sub_delims + "|:)*")
dec_octet = "([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"
ipv4address = "(" + dec_octet + r"\.){3}" + dec_octet
h16 = "[0-9A-F]{1,4}"
ls32 = "(" + h16 + ":" + h16 + "|" + ipv4address + ")"
ipv6address = (
    "((" + h16 + ":){6}" + ls32 +
    "|::(" + h16 + ":){5}" + ls32 +
    "|(" + h16 + ")?::(" + h16 + ":){4}" + ls32 +
    "|((" + h16 + ":)?" + h16 + ")?::(" + h16 + ":){3}" + ls32 +
    "|((" + h16 + ":){,2}" + h16 + ")?::(" + h16 + ":){2}" + ls32 +
    "|((" + h16 + ":){,3}" + h16 + ")?::" + h16 + ":" + ls32 +
    "|((" + h16 + ":){,4}" + h16 + ")?::" + ls32 +
    "|((" + h16 + ":){,5}" + h16 + ")?::" + h16 +
    "|((" + h16 + ":){,6}" + h16 + ")?::)")
ipvfuture = r"v[0-9A-F]+\.(" + unreserved + "|" + sub_delims + "|:)+"
ip_literal = r"\[(" + ipv6address + "|" + ipvfuture + r")\]"
reg_name = "(" + unreserved + "|" + pct_encoded + "|" + sub_delims + ")*"
host = "(" + ip_literal + "|" + ipv4address + "|" + reg_name + ")"
port = "[0-9]*"
authority = "(" + userinfo + "@)?" + host + "(:" + port + ")?"
path_abempty = "(/" + segment + ")*"
path_absolute = "/(" + segment_nz + "(/" + segment + ")*)?"
path_rootless = segment_nz + "(/" + segment + ")*"
path_empty = pchar + "{0}"
hier_part = ("(" + "//" + authority + path_abempty + "|" +
             path_absolute + "|" + path_rootless + "|" + path_empty + ")")
query = "(" + pchar + "|[/?])*"
fragment = query
uri = (scheme + ":" + hier_part + r"(\?" + query + ")?" +
       "(#" + fragment + ")?")

re_uri = re.compile('^' + uri + '$')


def is_prefixed(identifier):
    return type(identifier) == type(()) and len(identifier) == 2

def is_local(identifier):
    return type(identifier) == type('')


class Context(object):
    """struct which contain variables for a parse session"""
    def __init__(self):
        self.modules = {}
        """dict of modulename:<class Module>)"""
        
        self.module_list = []
        """ordered list of modules; we must validate in this order"""
        
        self.path = "."
        self.errors = []
        self.canonical = False
        self.submodule_expansion = True

    def add_module(self, filename):
        return self.search_module(Position(filename), filename)

    def search_module(self, pos, filename=None, modulename=None):
        # mark that we're adding this module, so that circular deps can
        # be found
        if modulename != None:
            # check for circular dependencies
            if modulename in self.modules:
# FIXME: do a correct circular check in validate
#                err_add(self.errors,
#                        pos, 'CIRCULAR_DEPENDENCY', ('module', modulename) )
                return None
            else:
                self.modules[modulename] = None

        if filename == None:
            filename = search_file(modulename + ".yang", self.path)
        if filename == None:
            filename = search_file(modulename + ".yin", self.path)
        if filename == None:
            err_add(self.errors, pos, 'MODULE_NOT_FOUND', modulename )
            return None
        
        if filename.endswith(".yin"):
            # FIXME: write a YIN parser
            p = YinParser(self, filename)
            module = p.parse_module()
        else:
            # by default, assume it's yang
            p = YangParser(self, filename)
            module = p.parse_module()

        if module == None:
            return None
        if modulename != None and modulename != module.name:
            err_add(self.errors, pos, 'BAD_MODULE_FILENAME',
                    (module.name, filename, modulename))
            return None
        if module.name not in self.modules or self.modules[module.name] == None:
            self.modules[module.name] = module
            self.module_list.append(module)
        return module.name

    def validate(self):
        uris = {}
        for modname in self.modules:
            m = self.modules[modname]
            if m != None and m.namespace != None:
                uri = m.namespace.arg
                if uri in uris:
                    err_add(self.errors, m.namespace.pos,
                            'DUPLICATE_NAMESPACE', (uri, uris[uri]))
                else:
                    uris[uri] = m.name
        for m in self.module_list:
            if m != None:
                m.validate()

### struct to keep track of position for error messages

class Position(object):
    def __init__(self, filename):
        self.filename = filename
        self.line = 0
        self.module_name = None
    def __str__(self):
        return self.filename + ':' + str(self.line)

### structs used to represent a YANG module

## Each statement in YANG is represented as a class.  Simple statements,
## which don't have any sub-statements defined in YANG, are represented
## with the class Statement.

## All YANG statements are derived from Statement.  Simple statements
## which don't have any sub statements defined, e.g. 'description' are
## represented as Statement directly.

class Statement(object):
    def __init__(self, parent, pos, keyword, module, arg=None):
        self.parent = parent
        self.pos = copy.copy(pos)
        self.keyword = keyword
        """the name of the statement"""

        self.arg = arg
        """the statement's argument;  a string or None"""
        
        self.substmts = []
        """the statement's substatements; a list of Statements"""

        # extra
        self.i_module = module

    def search_typedef(self, name):
        if 'typedef' in self.__dict__:
            typedef = attrsearch(name, 'name', self.typedef)
            if typedef != None:
                return typedef
        return self.parent.search_typedef(name)

    def escaped_arg(self):
        """In `self.arg`, replace characters forbidden in XML by
        entities and return the result.
        """
        res = self.arg.replace("&", "&amp;")
        res = res.replace('"', "&quot;")
        res = res.replace("<", "&lt;")
        return res.replace(">", "&gt;")

    def search_grouping(self, name, modules=None):
        if 'grouping' in self.__dict__:
            dbg("search for grouping %s in %s" % (name, self.arg))
            grouping = attrsearch(name, 'name', self.grouping)
            if grouping != None:
                return grouping
        return self.parent.search_grouping(name)

    def validate(self, errors):
        return True
    
    def validate_extensions(self, module, errors):
        for x in self.substmts:
            x.validate_extensions(module, errors)

    def pprint(self, indent='', f=None):
        print indent + self.__class__.__name__ + " " + self.arg
        if f != None:
             f(self, indent)
        for x in self.substmts:
            x.pprint(indent + ' ', f)

class SchemaNodeStatement(Statement):
    def __init__(self, parent, pos, keyword, module, arg):
        Statement.__init__(self, parent, pos, keyword, module, arg)
        # extra
        self.i_expanded_children = []
        
    def validate_post_augment(self, errors):
        for c in self.i_expanded_children:
            c.validate_post_augment(errors)

class DataDefStatement(SchemaNodeStatement):
    def __init__(self, parent, pos, keyword, module, arg):
        SchemaNodeStatement.__init__(self, parent, pos, keyword, module, arg)
        # extra
        self.i_config = None

    def validate_post_uses(self, pos, errors, config):
        if self.i_config == None:
            self.i_config = config
        for c in self.i_expanded_children:
            c.validate_post_uses(pos, errors, config)

class Module(Statement):
    def __init__(self, pos, ctx, name, is_submodule):
        self.name = name
        Statement.__init__(self, None, pos, self.__class__.__name__.lower(),
                      self, name)
        self.ctx = ctx
        # argument
        self.name = name
        # statements
        self.yang_version = None
        self.description = None
        self.reference = None
        self.contact = None
        self.import_ = []       # MUST set using set_import
        self.include = []       # MUST set using set_include
        self.belongs_to = None  # only set for submodules
        self.namespace = None
        self.prefix = None
        self.revision = []
        self.typedef = []
        self.grouping = []
        self.extension = []
        self.children = []  # leaves, containers, lists, leaf-lists, choices
        self.augment = []
        # extra
        self.i_is_submodule = is_submodule
        self.i_prefixes = {}
        """dict of prefix:modulename"""
        
        self.i_local_typedefs = []
        self.i_gen_typedef = []
        """generated 'dummy' typedefs"""
        
        self.i_gen_import = []
        """generated 'dummy' imports"""
        
        self.i_gen_augment_idx = 0
        """generated augment names"""
        
        self.i_expanded_children = []
        """augment and uses expanded schema tree"""
        
        self.i_config = True
        """default config property for top-level nodes"""

        if name not in ctx.modules:
            ctx.modules[name] = None

    def set_import(self, parser, import_):
        # check for circular import
        if import_.modulename not in self.ctx.modules:
            # FIXME: do a correct circular check in validate
            #       err_add(self.ctx.errors, parser.pos,
            #            'CIRCULAR_DEPENDENCY', ('module', import_.modulename))

            # parse and load the imported module
            self.ctx.search_module(parser.pos, modulename = import_.modulename)

        # get the prefix to use for this import
        if import_.prefix == None:
            imported_module = parser.ctx.modules[import_.modulename]
            if imported_module == None:
                # failed to import
                return
            prefix = imported_module.prefix.arg
        else:
            prefix = import_.prefix.arg
        # check if the prefix is already used by someone else
        if prefix in self.i_prefixes:
            err_add(self.ctx.errors, parser.pos,
                    'PREFIX_ALREADY_USED', (prefix, self.i_prefixes[prefix]))
        else:
            # add the prefix->modulename mapping to this module
            self.i_prefixes[prefix] = import_.modulename

    def set_include(self, parser, include):
        # parse and load the included module
        self.ctx.search_module(parser.pos, modulename = include.modulename)

    def search_extension(self, name, modules=None):
        extension = attrsearch(name, 'name', self.extension)
        if extension != None:
            return extension
        if modules == None:
            modules = []
        modules.append(self.name)
        for inc in self.include:
            if inc.modulename not in modules:
                mod = self.ctx.modules[inc.modulename]
                if mod != None:
                    extension = mod.search_extension(name, modules)
                    if extension != None:
                        return extension
        return None

    def search_typedef(self, name, modules=None):
        typedef = attrsearch(name, 'name', self.typedef)
        if typedef != None:
            return typedef
        if modules == None:
            modules = []
        modules.append(self.name)
        for inc in self.include:
            if inc.modulename not in modules:
                mod = self.ctx.modules[inc.modulename]
                if mod != None:
                    typedef = mod.search_typedef(name, modules)
                    if typedef != None:
                        return typedef
        return None

    def search_grouping(self, name, modules=None):
        dbg("search for grouping %s in module %s" % (name, self.name))
        grouping = attrsearch(name, 'name', self.grouping)
        if grouping != None:
            return grouping
        if modules == None:
            modules = []
        modules.append(self.name)
        for inc in self.include:
            if inc.modulename not in modules:
                mod = self.ctx.modules[inc.modulename]
                if mod != None:
                    grouping = mod.search_grouping(name, modules)
                    if grouping != None:
                        return grouping
        return None

    def search_child(self, name, modules=None):
        child = attrsearch(name, 'name', self.i_expanded_children)
        if child != None:
            return child
        if modules == None:
            modules = []
        modules.append(self.name)
        for inc in self.include:
            if inc.modulename not in modules:
                mod = self.ctx.modules[inc.modulename]
                if mod != None:
                    child = mod.search_child(name, modules)
                    if child != None:
                        return child
        return None

    def prefix_to_module(self, prefix, pos, errors):
        if prefix == '':
            return self
        elif self.prefix != None and prefix == self.prefix.arg:
            return self
        else:
            try:
                modulename = self.i_prefixes[prefix]
                module = self.ctx.modules[modulename]
            except KeyError:
                err_add(errors, pos, 'PREFIX_NOT_DEFINED', prefix)
                return None
            return module

    def validate(self):
        errors = self.ctx.errors
        validate_identifier(self.name, self.pos, errors)

        # make sure all sub modules we include have a proper belongs-to
        if self.belongs_to == None:
            parent_module_name = self.name
        else:
            parent_module_name = self.belongs_to.arg
        for sub_include in self.include:
            sub_name = sub_include.modulename
            sub_module = self.ctx.modules[sub_name]
            # if we belong to M, then all our include N
            # must belong to M
            if (sub_module != None and
                (sub_module.belongs_to == None or
                 sub_module.belongs_to.arg != parent_module_name)):
                err_add(errors, sub_include.pos,
                        'BAD_SUB_BELONGS_TO', (self.name, sub_name, sub_name)) 
        # check that the revision clauses are in descending order
        if self.revision != []:
            cur = None
            for rev in self.revision:
                try:
                    res = time.strptime(rev.date, "%Y-%m-%d")
                    date = (res[0], res[1], res[2])
                    if cur != None and date >= cur:
                        err_add(errors, rev.pos, 'REVISION_ORDER', ())
                    cur = date
                except ValueError:
                    err_add(errors, rev.pos, 'SYNTAX_ERROR',
                            'bad revision date')

        for x in self.typedef:
            x.validate(errors)

        for x in self.grouping:
            x.validate(errors)

        validate_children(self, self.children, errors, True)

        ## validate augments.  simple alg - since a later augment
        ## might add nodes for an earlier augment, we try to validate
        ## each augment until we no longer make progress
        as = []
        new_as = self.augment
        while len(as) != len(new_as):
            as = new_as
            new_as = []
            for x in as:
                if x.validate(errors) == 'may_recover':
                    new_as.append(x)
        for x in new_as:
            x.validate(errors, recover=False)

        for x in self.substmts:
            x.validate_extensions(self, errors)

        ## after augment, we can now validate all keyrefs
        for c in self.i_expanded_children:
            c.validate_post_augment(errors)

        return errors

    def gen_new_typedef(self, type):
        i = 0
        name = "t" + str(i)
        all_typedefs = self.typedef + self.i_local_typedefs + \
                       self.i_gen_typedef
        while attrsearch(name, 'name', all_typedefs):
            i = i + 1
            name = "t" + str(i)
        typedef = Typedef(type, type.pos, self, name)
        typedef.type = type
        self.i_gen_typedef.append(typedef)
        return name

    def gen_new_import(self, modname):
        i = 0
        pre = "p" + str(i)
        while pre in self.i_prefixes:
            i = i + 1
            pre = "p" + str(i)
        self.i_prefixes[pre] = modname
        imp = Import(self, None, self, modname)
        self.i_gen_import.append(imp)

class Import(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.modulename = arg
        # statements
        self.prefix = None

class Include(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.modulename = arg
        # statements

class Revision(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.date = arg
        # statements
        self.description = None

class Typedef(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.name = arg
        # statements
        self.type = None
        self.units = None
        self.status = None
        self.description = None
        self.reference = None
        self.default = None
        # extra
        self.i_validated = None
        self.i_default = None

    def validate(self, errors):
        # check if we're initialized
        if self.i_validated == True:
            return
        validate_identifier(self.name, self.pos, errors)
        if self.i_validated == False:
            err_add(errors, self.pos,
                    'CIRCULAR_DEPENDENCY', ('type', self.name) )
            return
        self.i_validated = False
        dbg("validating typedef %s" % self.name)
        if is_base_type(self.name):
            err_add(errors, self.pos, 'BAD_TYPE_NAME', self.name)
        elif self.parent.parent != None:
            ptype = self.parent.parent.search_typedef(self.name)
            if ptype != None:
                err_add(errors, self.pos, 'TYPE_ALREADY_DEFINED',
                        (self.name, ptype.pos))
        self.type.validate(errors)
        self.i_validated = True
        if self.type.i_typedef != None:
            self.i_default = self.type.i_typedef.i_default
        if self.default != None and self.type.i_type_spec != None :
            self.i_default = self.type.i_type_spec.str_to_val(errors,
                                                              self.default.pos,
                                                              self.default.arg)
        if self.i_default != None:
            self.type.i_type_spec.validate(errors, self.default.pos,
                                           self.i_default,
                                           ' for the default value')

class Grouping(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.name = arg
        # statements
        self.description = None
        self.status = None
        self.reference = None
        self.typedef = []
        self.grouping = []
        self.children = []
        self.augment = []
        # extra
        self.i_expanded_children = []
        self.i_validated = False

    def validate(self, errors):
        if self.i_validated == True:
            return
        validate_identifier(self.name, self.pos, errors)
        for x in self.typedef:
            x.validate(errors)
        for x in self.grouping:
            x.validate(errors)
        if self.parent.parent != None:
            pgrouping = self.parent.parent.search_grouping(self.name)
            if pgrouping != None:
                err_add(errors, self.pos, 'GROUPING_ALREADY_DEFINED',
                        (self.name, pgrouping.pos))
        validate_children(self, self.children, errors)
        self.i_validated = True

class Extension(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.name = arg
        # statements
        self.description = None
        self.reference = None
        self.status = None
        self.argument = None
    
    def validate(self, errors):
        validate_identifier(self.name, self.pos, errors)

class Argument(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.name = arg
        # statements
        self.yin_element = None

    def validate(self, errors):
        validate_identifier(self.name, self.pos, errors)

class Type(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.name = arg
        # statements
        self.range = None
        self.length = None
        self.pattern = None
        self.enum = []
        self.bit = []
        self.path = None
        self.type = []
        # extra
        self.i_type_spec = None
        self.i_typedef = None
        """pointer back its typedef, if applicable"""
        
        self.i_is_derived = False
        """true if type has any restrictions"""

    def has_type(self, names):
        # returns name if the has name as one of its base types,
        # and name is in the names list.  otherwise, returns None.
        if self.name in names:
            return self.name
        for t in self.type: # check all unions
            r = t.has_type(names)
            if r != None:
                return r
        if self.i_typedef != None:
            return self.i_typedef.type.has_type(names)
        return None

    def validate(self, errors):
        # Find the base type_spec
        name = self.name
        dbg("searching for type spec: %s" % self.name)
        if name.find(":") == -1:
           # this is a no-prefixed name, first check local typedefs
            typedef = self.parent.search_typedef(name)
            self.i_typedef = typedef
            if typedef == None:
                # check built-in types
                try:
                    self.i_type_spec = yang_type_specs[name]
                except KeyError:
                    err_add(errors, self.pos,
                            'TYPE_NOT_FOUND', (name, self.i_module.name))
                    return
            else:
                typedef.validate(errors)
                self.i_type_spec = copy.copy(typedef.type.i_type_spec)
                if self.i_type_spec != None:
                    self.i_type_spec.definition = 'at ' + str(typedef.pos) + ' '
        else:
            # this is a prefixed name, check the imported modules
            [prefix, name] = name.split(':', 1)
            pmodule = self.i_module.prefix_to_module(prefix, self.pos, errors)
            if pmodule == None:
                return
            typedef = pmodule.search_typedef(name)
            self.i_typedef = typedef
            if typedef == None:
                err_add(errors, self.pos,
                        'TYPE_NOT_FOUND', (name, pmodule.name))
                return
            else:
                typedef.validate(errors)
                self.i_type_spec = copy.copy(typedef.type.i_type_spec)
                if self.i_type_spec != None:
                    self.i_type_spec.definition = 'at ' + str(typedef.pos) + ' '

        if self.i_type_spec == None:
            # an error has been added already; skip further validation
            return

        # check the range restriction
        if (self.range != None and
            'range' not in self.i_type_spec.restrictions()):
            err_add(errors, self.range.pos, 'BAD_RESTRICTION', 'range')
        elif self.range != None:
            self.i_is_derived = True
            if self.range.validate(errors, self):
                self.i_type_spec = self.range.mk_type_spec(self.i_type_spec)
            
        # check the length restriction
        if (self.length != None and
            'length' not in self.i_type_spec.restrictions()):
            err_add(errors, self.length.pos, 'BAD_RESTRICTION', 'length')
        elif self.length != None:
            self.i_is_derived = True
            if self.length.validate(errors):
                self.i_type_spec = self.length.mk_type_spec(self.i_type_spec)
            
        # check the pattern restriction
        if (self.pattern != None and
            'pattern' not in self.i_type_spec.restrictions()):
            err_add(errors, self.pattern.pos, 'BAD_RESTRICTION', 'pattern')
        elif self.pattern != None:
            self.i_is_derived = True
            if self.pattern.validate(errors):
                self.i_type_spec = self.pattern.mk_type_spec(self.i_type_spec)

        # check the path restriction
        if self.path != None and self.name != 'keyref':
            err_add(errors, self.path.pos, 'BAD_RESTRICTION', 'path')
        elif self.path != None:
            self.i_is_derived = True
            if self.path.validate(errors):
                self.i_type_spec = self.path.mk_type_spec(self.i_type_spec)

        # check the enums - only applicable when the type is the builtin
        # enumeration type
        if self.enum != [] and self.name != 'enumeration':
            err_add(errors, self.enum[0].pos, 'BAD_RESTRICTION', 'enum')
        elif self.name == 'enumeration':
            self.i_is_derived = True
            if self.enums_validate(errors):
                self.i_type_spec = EnumerationTypeSpec(self.enum)

        # check the bits - only applicable when the type is the builtin
        # bits type
        if self.bit != [] and self.name != 'bits':
            err_add(errors, self.bit[0].pos, 'BAD_RESTRICTION', 'bit')
        elif self.name == 'bits':
            self.i_is_derived = True
            if self.bits_validate(errors):
                self.i_type_spec = BitsTypeSpec(self.bit)

        # check the union types
        if self.type != [] and self.name != 'union':
            err_add(errors, self.pattern.pos, 'BAD_RESTRICTION', 'union')
        elif self.name == 'union':
            self.i_is_derived = True
            if self.union_validate(errors):
                self.i_type_spec = UnionTypeSpec(self.type)

    def enums_validate(self, errors):
        if self.enum == []:
            err_add(errors, self.pos, 'MISSING_TYPE_SPEC',
                    ('enumeration', 'enum'))
            return False
        # make sure all values given are unique
        values = []
        for e in self.enum:
            validate_identifier(e.name, e.pos, errors)
            if e.value != None:
                try:
                    x = int(e.value.arg)
                    if x < -2147483648 or x > 2147483647:
                        raise ValueError
                    e.i_value = x
                    if x in values:
                        err_add(errors, e.value.pos, 'DUPLICATE_ENUM_VALUE', x)
                    else:
                        values.append(x)
                except ValueError:
                    err_add(errors, e.value.pos, 'ENUM_VALUE', e.value.arg)
        # check status (here??)
        return True

    def bits_validate(self, errors):
        if self.bit == []:
            err_add(errors, self.pos, 'MISSING_TYPE_SPEC',
                    ('bits', 'bit'))
            return False
        # make sure all positions given are unique
        values = []
        for b in self.bit:
            validate_identifier(b.name, b.pos, errors)
            try:
                x = int(b.position.arg)
                if x < 0:
                    raise ValueError
                b.i_position = x
                if x in values:
                    err_add(errors, b.position.pos, 'DUPLICATE_BIT_POSITION', x)
                else:
                    values.append(x)
            except ValueError:
                err_add(errors, b.position.pos, 'BIT_POSITION', b.position.arg)

        # check status (here??)
        return True

    def union_validate(self, errors):
        if self.type == []:
            err_add(errors, self.pos, 'MISSING_TYPE_SPEC',
                    ('union', 'type'))
            return False
        res = True
        for t in self.type:
            if t.validate(errors) == False:
                res = False
        t = self.has_type(['empty', 'keyref'])
        if t != None:
            err_add(errors, self.pos, 'BAD_TYPE_IN_UNION', t)
            return False
        return res

def is_smaller(lo, hi):
    if lo == None:
        return True;
    if lo == 'min' and hi != 'min':
        return True;
    if lo == 'max' and hi != None:
        return False
    if hi == 'min':
        return False
    if hi == None:
        return True
    if hi == 'max':
        return True
    return lo < hi

class Range(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.expr = arg
        # statements
        self.error_message = None
        self.error_app_tag = None
        # extra
        self.i_ranges = []
        """list of parsed ranges, (lo,hi) where lo and hi are
        None, 'min', 'max', or a number matching the base type"""

    def validate(self, errors, type):
        # check that it's syntactically correct
        if re_range.search(self.expr) == None:
            err_add(errors, self.pos, 'SYNTAX_ERROR', 'bad range expression')
            return False
        # now break it apart
        def f(self, lostr, histr):
            if histr == '':
                # this means that a single number was in the range, e.g.
                # "4 | 5..6".
                return (type.i_type_spec.str_to_val(errors, self.pos, lostr),
                        None)
            return (type.i_type_spec.str_to_val(errors, self.pos, lostr),
                    type.i_type_spec.str_to_val(errors, self.pos, histr))
        self.i_ranges = [f(self, m[1], m[6])
                         for m in re_range_part.findall(self.expr)]
        # make sure the range values are of correct type and increasing
        pos = self.pos
        cur_lo = None
        for (lo, hi) in self.i_ranges:
            if lo != 'min' and lo != 'max':
                type.i_type_spec.validate(errors, pos, lo)
            if hi != 'min' and hi != 'max' and hi != None:
                type.i_type_spec.validate(errors, pos, hi)
            # check that cur_lo < lo < hi
            if not is_smaller(cur_lo, lo):
                err_add(errors, pos, 'RANGE_BOUNDS', (str(lo), cur_lo))
                return False
            if not is_smaller(lo, hi):
                err_add(errors, pos, 'RANGE_BOUNDS', (str(hi), str(lo)))
                return False
            if hi == None:
                cur_lo = lo
            else:
                cur_lo = hi
        return True

    def mk_type_spec(self, base_type_spec):
        return RangeTypeSpec(base_type_spec, self.i_ranges)

class Length(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.expr = arg
        # statements
        self.error_message = None
        self.error_app_tag = None
        # extra
        self.i_lengths = None
        """list of parsed lengths, (lo,hi), where lo and hi are
        None, 'min', 'max', or an integer"""

    def validate(self, errors):
        # check that it's syntactically correct
        pos = self.pos
        if re_length.search(self.expr) == None:
            err_add(errors, pos, 'SYNTAX_ERROR', 'bad length expression')
            return False
        def f(self, lostr, histr):
            try:
                if lostr in ['min', 'max']:
                    lo = lostr
                else:
                    lo = int(lostr)
            except ValueError:
                err_add(errors, pos, 'TYPE_VALUE', (lostr, '', 'not an integer'))
                return (None, None)
            try:
                if histr == '':
                    # this means that a single number was in the length, e.g.
                    # "4 | 5..6".
                    return (lo, None)
                if histr in ['min', 'max']:
                    hi = histr
                else:
                    hi = int(histr)
            except ValueError:
                err_add(errors, pos, 'TYPE_VALUE', (histr, '', 'not an integer'))
                return None
            return (lo, hi)
        self.i_lengths = [f(self, m[1], m[3]) \
                          for m in re_length_part.findall(self.expr)]
        # make sure the length values are of correct type and increasing
        cur_lo = None
        for (lo, hi) in self.i_lengths:
            # check that cur_lo < lo < hi
            if not is_smaller(cur_lo, lo):
                err_add(errors, pos, 'LENGTH_BOUNDS', (str(lo), cur_lo))
                return False
            if not is_smaller(lo, hi):
                err_add(errors, pos, 'length_bounds', (str(hi), str(lo)))
                return False
            # FIXME: we should check that the lengths are just restrictions
            # of any base type's lengths.  Have to figure out some way to do
            # that... currently we can't check just length values; we'd have
            # to pass just the length integer to typespec.validate().  Or
            # something...
            if hi == None:
                cur_lo = lo
            else:
                cur_lo = hi
            if type(cur_lo) == type(0) and cur_lo > 18446744073709551615:
                err_add(errors, pos, 'LENGTH_VALUE', str(cur_lo))
                return False
        return True

    def mk_type_spec(self, base_type_spec):
        """creates a new type_spec for this type"""
        return LengthTypeSpec(base_type_spec, self.i_lengths)

class Pattern(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.expr = arg
        # statements
        self.error_message = None
        self.error_app_tag = None
        # extra
        self.i_re = None

    def validate(self, errors):
        # check that it's syntactically correct
        try:
            self.i_re = libxml2.regexpCompile(self.expr)
            return True
        except libxml2.treeError, v:
            err_add(errors, self.pos, 'PATTERN_ERROR', str(v))
            return False

    def mk_type_spec(self, base_type_spec):
        # create a new type_spec for this type
        return PatternTypeSpec(base_type_spec, self.i_re)

class Path(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.expr = arg
        # statements
        self.error_message = None
        self.error_app_tag = None
        # extra
        self.i_path = None
        self.i_target_node = None

    # PRE: s matches re_keypath
    # Ret: (up::int(), [identifier | [(identifier, up::int(), [identifier])]])
    def parse_keypath(self, s):

        def parse_dot_dot(s):
            up = 0
            i = 0
            while True:
                if s[i] == '.' and s[i+1] == '.':
                    up = up + 1
                    i = i + 3 # skip the '/'
                elif s[i] == '/':
                    i = i + 1 # skip the '/'
                    if up == 0: # absolute path
                        up = -1
                    break
                else:
                    # s points to an identifier
                    break
            return (up, s[i:])

        def skip_space(s):
            i = 0
            while s[i].isspace():
                i = i + 1
            return s[i:]
    
        def parse_identifier(s):
            m = re_keyword.match(s)
            s = s[m.end():]
            if m.group(2) == None: # no prefix
                return (m.group(4), s)
            else:
                return ((m.group(2), m.group(4)), s)

        def parse_key_predicate(s):
            s = s[1:] # skip '['
            s = skip_space(s)
            (identifier, s) = parse_identifier(s)
            s = skip_space(s)
            s = s[1:] # skip '='
            s = skip_space(s)
            s = s[6:] # skip '$this/'
            (up, s) = parse_dot_dot(s)
            s = skip_space(s)
            dn = []
            while True:
                (xidentifier, s) = parse_identifier(s[i:])
                dn.append(xidentifier)
                if s[0] == '/':
                    s = s[1:] # skip '/'
                else:
                    s = skip_space(s)
                    s = s[1:] # skip ']'
                    break
            return ((identifier, up, dn), s)

        (up, s) = parse_dot_dot(s)
        dn = []
        i = 0
        # all '..'s are now parsed
        while len(s) > 0:
            (identifier, s) = parse_identifier(s[i:])
            dn.append(identifier)
            if len(s) == 0:
                break
            while s[0] == '[':
                (pred, s) = parse_key_predicate(s)
                dn.append(pred)
            if len(s) > 0:
                s = s[1:] # skip '/'
        return (up, dn)

    def validate(self, errors):
        if re_keypath.search(self.expr) == None:
            err_add(errors, self.pos, 'SYNTAX_ERROR',
                    'bad keypath expression')
            return False
        self.i_path = self.parse_keypath(self.expr)
        return True

    def mk_type_spec(self, base_type_spec):
        # create a new type_spec for this type
        return PathTypeSpec(self.i_target_node)

class Must(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.expr = arg
        # statements
        self.error_message = None
        self.error_app_tag = None
        self.description = None
        self.reference = None

class Enum(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.name = arg
        # statements
        self.status = None
        self.description = None
        self.reference = None
        self.value = None
        # extra
        self.i_value = None

class Bit(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.name = arg
        # statements
        self.status = None
        self.description = None
        self.reference = None
        self.position = None
        # extra
        self.i_position = None

class Leaf(DataDefStatement):
    def __init__(self, parent, pos, module, arg):
        DataDefStatement.__init__(self, parent, pos,
                             self.__class__.__name__.lower(),
                             module, arg)
        # argument
        self.name = arg
        # statements
        self.description = None
        self.status = None
        self.reference = None
        self.config = None
        self.mandatory = None
        self.must = []
        self.type = None
        self.units = None
        self.default = None
        # extra
        self.i_keyrefs = [] # if this is a union, there might be several
        self.i_keyrefs_validated = False
        self.i_keyref_ptrs = [] # pointers to the keys the keyrefs refer to

    def validate(self, errors):
        validate_identifier(self.name, self.pos, errors)
        if self.config != None:
            self.i_config = (self.config.arg == "true")
        if self.default != None:
            if self.mandatory != None and self.mandatory.arg == "true":
                err_add(errors, self.default.pos, 'DEFAULT_AND_MANDATORY', ())

        if self.type != None:
            self.type.validate(errors)
            self.validate_default(errors)
            if self.type.i_typedef != None:
                validate_status(errors, self, self.type.i_typedef,
                                'leaf', 'typedef')

        add_keyref_path(self.i_keyrefs, self.type)

    def validate_default(self, errors):
        if ((self.default != None) and
            (self.type != None) and
            (self.type.i_type_spec != None)):
            val = self.type.i_type_spec.str_to_val(errors,
                                                   self.default.pos,
                                                   self.default.arg)
            if val != None:
                self.type.i_type_spec.validate(errors,
                                               self.default.pos, val)

    def validate_post_augment(self, errors):
        if self.i_keyrefs_validated == True:
            return
        for path in self.i_keyrefs:
            self.i_keyrefs_validated = True
            ptr = validate_keyref_path(self, path, errors)
            if ptr != None:
                self.i_keyref_ptrs.append(ptr)

def add_keyref_path(keyrefs, type):
    if type != None:
        if type.path != None:
            keyrefs.append(type.path)
        if type.i_typedef != None:
            add_keyref_path(keyrefs, type.i_typedef.type)
        for t in type.type: # union
            add_keyref_path(keyrefs, t)

def validate_keyref_path(obj, path, errors):
    def find_identifier(identifier):
        if is_prefixed(identifier):
            (prefix, name) = identifier
            module = path.i_module.prefix_to_module(prefix, path.pos, errors)
            if module == None:
                raise NotFound
            return (module, name)
        else: # local identifier
            return (path.i_module, identifier)

    def is_identifier(x):
        if is_local(x):
            return True
        if is_prefixed(x):
            return True
        return False

    def is_predicate(x):
        if type(x) == type(()) and len(x) == 3:
            return True
        return False
    
    def follow_path(ptr, up, dn):
        if up == -1: # absolute path
            (pmodule, name) = find_identifier(dn[0])
            ptr = pmodule.search_child(name)
            if ptr == None:
                err_add(errors, path.pos, 'KEYREF_IDENTIFIER_NOT_FOUND',
                        (pmodule.name, name, obj.name, obj.pos))
                raise NotFound
            dn = dn[1:]
        else:
            while up > 0:
                if ptr == None:
                    err_add(errors, path.pos, 'KEYREF_TOO_MANY_UP',
                            (obj.name, obj.pos))
                    raise NotFound
                ptr = ptr.parent
                up = up - 1
        i = 0
        key_list = None
        keys = []
        while i < len(dn):
            if is_identifier(dn[i]) == True:
                (pmodule, name) = find_identifier(dn[i])
                module_name = pmodule.name
            elif ptr.keyword == 'list': # predicate on a list, good
                key_list = ptr
                keys = []
                # check each predicate
                while i < len(dn) and is_predicate(dn[i]) == True:
                    # unpack the predicate
                    (keyleaf, pup, pdn) = dn[i]
                    (pmodule, pname) = find_identifier(keyleaf)
                    # make sure the keyleaf is really a key in the list
                    pleaf = search_child(ptr.i_key, pmodule.name, pname)
                    if pleaf == None:
                        err_add(errors, path.pos, 'KEYREF_NO_KEY',
                                (pmodule.name, pname, obj.name, obj.pos))
                        raise NotFound
                    # make sure it's not already referenced
                    if keyleaf in keys:
                        err_add(errors, path.pos, 'KEYREF_MULTIPLE_KEYS',
                                (pmodule.name, pname, obj.name, obj.pos))
                        raise NotFound
                    keys.append((pmodule.name, pname))
                    # check what this predicate refers to; make sure it's
                    # another leaf; either of type keyref to keyleaf, OR same
                    # type as the keyleaf
                    (xkey_list, x_key, xleaf) = follow_path(ptr, pup, pdn)
                    xleaf.validate_post_augment(errors)
                    if xleaf.i_keyref_ptrs == []:
                        err_add(errors, path.pos, 'KEYREF_BAD_PREDICATE_PTR',
                                (pmodule.name, pname, obj.name, obj.pos))
                    for xptr in xleaf.i_keyref_ptrs:
                        if xptr != pleaf:
                            err_add(errors, path.pos, 'KEYREF_BAD_PREDICATE_PTR',
                                    (pmodule.name, pname, obj.name, obj.pos))
                            raise NotFound
                    i = i + 1
                continue
            else:
                err_add(errors, path.pos, 'KEYREF_BAD_PREDICATE',
                        (ptr.i_module.name, ptr.name, obj.name, obj.pos))
                raise NotFound
            if ptr.keyword in ['list', 'container', 'case', 'grouping']:
                ptr = search_exp_data_node(ptr.i_expanded_children,
                                           module_name, name)
                if ptr == None:
                    err_add(errors, path.pos, 'KEYREF_IDENTIFIER_NOT_FOUND',
                            (module_name, name, obj.name, obj.pos))
                    raise NotFound
            else:
                err_add(errors, path.pos, 'KEYREF_IDENTIFIER_BAD_NODE',
                        (module_name, name, obj.name, obj.pos,
                         ptr.keyword))
                raise NotFound
            i = i + 1
        return (key_list, keys, ptr)

    try:
        if path.i_path == None: # e.g. invalid path
            return None
        (up, dn) = path.i_path
        (key_list, keys, ptr) = follow_path(obj, up, dn)
        # ptr is now the node that the keyref path points to
        # check that it is a key in a list
        is_key = False
        if ptr.keyword == 'leaf':
            if ptr.parent.keyword == 'list':
                if ptr in ptr.parent.i_key:
                    is_key = True
        if is_key == False:
            err_add(errors, path.pos, 'KEYREF_NOT_LEAF_KEY',
                    (obj.name, obj.pos))
            return None
        if key_list == ptr.parent and (ptr.i_module.name, ptr.name) in keys:
            err_add(errors, path.pos, 'KEYREF_MULTIPLE_KEYS',
                    (ptr.i_module.name, ptr.name, obj.name, obj.pos))
        return ptr
    except NotFound:
        return None

class LeafList(DataDefStatement):
    def __init__(self, parent, pos, module, arg):
        DataDefStatement.__init__(self, parent, pos,
                             'leaf-list',
                             module, arg)
        # argument
        self.name = arg
        # statements
        self.description = None
        self.status = None
        self.reference = None
        self.config = None
        self.type = None
        self.units = None
        self.min_elements = None
        self.max_elements = None
        self.ordered_by = None
        # extra
        self.i_keyrefs = []
        """if this is a union, there might be several"""
        
        self.i_keyrefs_validated = False
        self.i_keyref_ptrs = []
        """pointers to the keys the keyrefs refer to"""

    def validate(self, errors):
        validate_identifier(self.name, self.pos, errors)
        if self.config != None:
            self.i_config = (self.config.arg == "true")
        if self.type != None:
            self.type.validate(errors)
            if self.type.i_typedef != None:
                validate_status(errors, self, self.type.i_typedef, 'leaf-list',
                                'typedef')
        add_keyref_path(self.i_keyrefs, self.type)

    def validate_post_augment(self, errors):
        if self.i_keyrefs_validated == True:
            return
        for path in self.i_keyrefs:
            ptr = validate_keyref_path(self, path, errors)
            if ptr != None:
                self.i_keyref_ptrs.append(ptr)
        self.i_keyrefs_validated = True

class Container(DataDefStatement):
    def __init__(self, parent, pos, module, arg):
        DataDefStatement.__init__(self, parent, pos,
                             self.__class__.__name__.lower(),
                             module, arg)
        # argument
        self.name = arg
        # statements
        self.description = None
        self.status = None
        self.reference = None
        self.config = None
        self.presence = None
        self.must = []
        self.typedef = []
        self.grouping = []
        self.children = []
        self.augment = []

    def validate(self, errors): 
        validate_identifier(self.name, self.pos, errors)
        for x in self.typedef:
            x.validate(errors)
        for x in self.grouping:
            x.validate(errors)
        if self.config != None:
            self.i_config = (self.config.arg == "true")
        validate_children(self, self.children, errors, self.i_config)

class List(DataDefStatement):
    def __init__(self, parent, pos, module, arg):
        DataDefStatement.__init__(self, parent, pos,
                             self.__class__.__name__.lower(),
                             module, arg)
        # argument
        self.name = arg
        # statements
        self.description = None
        self.status = None
        self.reference = None
        self.config = None
        self.must = []
        self.min_elements = None
        self.max_elements = None
        self.ordered_by = None
        self.key = None
        self.unique = []
        self.children = []
        self.typedef = []
        self.grouping = []
        self.augment = []
        # extra
        self.i_key = []
        """list of pointers to the leaves in i_expanded_children"""
        
        self.i_unique = []
        """list of list of pointers to the  leaves in i_expanded_children"""

    def validate(self, errors):
        validate_identifier(self.name, self.pos, errors)
        for x in self.typedef:
            x.validate(errors)
        for x in self.grouping:
            x.validate(errors)
        if self.config != None:
            self.i_config = (self.config.arg == "true")

        validate_children(self, self.children, errors, self.i_config)

        self.validate_key(errors)
        self.validate_unique(errors)

    def validate_key(self, errors):
        found = []
        if self.key != None:
            for x in self.key.arg.split():
                if x == '':
                    continue
                ptr = attrsearch(x, 'name', self.i_expanded_children)
                if x in found:
                    err_add(errors, self.key.pos, 'DUPLICATE_KEY', x)
                    return
                elif ((ptr == None) or (ptr.keyword != 'leaf')):
                    err_add(errors, self.key.pos, 'BAD_KEY', x)
                    return
                t = ptr.type.has_type(['empty'])
                if t != None:
                    err_add(errors, self.pos, 'BAD_TYPE_IN_KEY', t)
                    return False
                self.i_key.append(ptr)
                found.append(x)
        if ((self.i_config == True) and (len(self.i_key) == 0)):
            err_add(errors, self.pos, 'NEED_KEY', ())

    def validate_post_uses(self, pos, errors, config):
        DataDefStatement.validate_post_uses(self, pos, errors, config)
        if ((self.i_config == True) and (len(self.i_key) == 0)):
            err_add(errors, pos, 'NEED_KEY_USES', self.pos)

    def validate_unique(self, errors):
        for u in self.unique:
            found = []
            for expr in u.arg.split():
                if expr == '':
                    continue
                ptr = self
                for x in expr.split('/'):
                    if x == '':
                        continue
                    if ptr.keyword not in ['container', 'list',
                                           'choice', 'case']:
                        err_add(errors, u.pos, 'BAD_UNIQUE_PART', x)
                        return None
                    ptr = attrsearch(x, 'name', ptr.i_expanded_children)
                if ((ptr == None) or (ptr.keyword != 'leaf')):
                    err_add(errors, u.pos, 'BAD_UNIQUE', expr)
                    return
                if ptr in found:
                    err_add(errors, u.pos, 'DUPLICATE_UNIQUE', expr)
                found.append(ptr)
            if found == []:
                err_add(errors, u.pos, 'BAD_UNIQUE', u.arg)
                return
            self.i_unique.append(found)

class Uses(SchemaNodeStatement):
    def __init__(self, parent, pos, module, arg):
        SchemaNodeStatement.__init__(self, parent, pos,
                                self.__class__.__name__.lower(),
                                module, arg)
        # argument
        self.name = arg
        # statements
        self.description = None
        self.reference = None
        self.status = None
        self.children = []
        # extra
        self.i_grouping = None

    def validate(self, errors):
        # Find the base grouping
        name = self.name
        dbg("searching for grouping: %s" % self.name)
        if name.find(":") == -1:
            # this is a no-prefixed name, check module-local groupings
            self.i_grouping = self.parent.search_grouping(name)
            modulename = self.i_module.name
        else:
            # this is a prefixed name, check the imported modules
            [prefix, name] = name.split(':', 1)
            module = self.i_module.prefix_to_module(prefix, self.pos, errors)
            if module == None:
                return
            self.i_grouping = module.search_grouping(name)
            modulename = module.name
        if self.i_grouping == None:
            err_add(errors, self.pos, 'GROUPING_NOT_FOUND', (name, modulename))
            return
        self.i_grouping.validate(errors)

        def validate_uses_children(uch, gch, xch, errors):
            if len(uch) == 0:
                if len(gch) > 0:
                    # create an expanded child and add it to the
                    # list of expanded chs.
                    for g in gch:
                        newx = copy.copy(g)
                        # inline the definition into our modulde
                        newx.i_module.name = self.i_module.name
                        xch.append(newx)
                return
            if len(gch) == 0:
                err_add(errors, uch[0].pos, 'NODE_NOT_IN_GROUPING', uch[0].name)
                return
            # create an expanded child and add it to the list of expanded chs.
            newx = copy.copy(gch[0])
            xch.append(newx)
            # inline the definition into our modulde
            newx.i_module.name = self.i_module.name
            # check if we found the refined node
            if uch[0].name != gch[0].name:
                return validate_uses_children(uch, gch[1:], xch, errors)
            # check that uch[0] and gch[0] are of compatible type
            if uch[0].keyword != gch[0].keyword:
                err_add(errors, uch[0].pos, 'NODE_GROUPING_TYPE', uch[0].name)
                return
            # possibly recurse
            if uch[0].keyword in ['list', 'container', 'choice', 'case']:
                newx.children = []
                validate_uses_children(uch[0].children, gch[0].children,
                                       newx.children, errors)
            # possibly modify the expanded child
            if uch[0].keyword in ['leaf', 'choice']:
                if uch[0].default != None:
                    newx.default = uch[0].default
                    newx.validate_default(errors)
            if 'description' in uch[0].__dict__:
                if uch[0].description != None:
                    newx.description = uch[0].description
            if 'config' in uch[0].__dict__:
                if uch[0].config != None:
                    newx.config = uch[0].config
            if 'mandatory' in uch[0].__dict__:
                if uch[0].mandatory != None:
                    newx.mandatory = uch[0].mandatory

            validate_uses_children(uch[1:], gch[1:], xch, errors)
                
        if ((self.i_module.ctx.submodule_expansion == False) and
            ((self.i_grouping.i_module.i_is_submodule) and
             self.i_grouping.parent.keyword == 'module')):
            # do not expand groupings on top-level in submodules for XSD
            self.i_expanded_children = [self]
        else:
            validate_uses_children(self.children,
                                   self.i_grouping.i_expanded_children,
                                   self.i_expanded_children, errors)
            if 'i_config' in self.parent.__dict__:
                config = self.parent.i_config
            else:
                config = None
            for c in self.i_expanded_children:
                c.validate_post_uses(self.pos, errors, config)

    def validate_post_augment(self, errors):
        pass

def validate_children(obj, children, errors, config=None):
    for c in children:
        if 'i_config' in c.__dict__ and c.i_config == None:
            c.i_config = config
        c.validate(errors)
        if c.keyword == 'uses':
            obj.i_expanded_children.extend(c.i_expanded_children)
        else:
            obj.i_expanded_children.append(c)

    def chk_children(names, children):
        for c in children:
            if c.keyword != 'case':
                if (c.i_module.name, c.name) in names:
                    err_add(errors, c.pos, 'DUPLICATE_CHILD_NAME', c.name)
                names[(c.i_module.name, c.name)] = True
            if c.keyword in ['choice', 'case']:
                chk_children(names, c.children)

    chk_children({}, obj.i_expanded_children)

def search_child(children, modulename, identifier):
    for child in children:
        if ((child.name == identifier) and
            (child.i_module.name == modulename)):
            return child
    return None

def search_exp_data_node(children, modulename, identifier):
    for child in children:
        if child.keyword in ['choice', 'case']:
            r = search_exp_data_node(child.i_expanded_children,
                                     modulename, identifier)
            if r != None:
                return r
        elif ((child.name == identifier) and
              (child.i_module.name == modulename)):
            return child
    return None

class Choice(DataDefStatement):
    def __init__(self, parent, pos, module, arg):
        DataDefStatement.__init__(self, parent, pos,
                             self.__class__.__name__.lower(),
                             module, arg)
        # argument
        self.name = arg
        # statements
        self.description = None
        self.status = None
        self.reference = None
        self.default = None
        self.mandatory = None
        self.children = [] # cases and shorthands

    def validate(self, errors):
        validate_identifier(self.name, self.pos, errors)
        children = []
        for c in self.children:
            if c.keyword == 'case':
                children.append(c)
            else:
                # add the shorthand case node
                new_case = Case(c.parent, c.pos, c.i_module, c.name)
                new_child = copy.copy(c)
                new_child.parent = new_case
                new_case.children.append(new_child)
                children.append(new_case)
        validate_children(self, children, errors, self.i_config)
        self.validate_default(errors)
        # FIXME: check case for mandatory leafs?

    def validate_default(self, errors):
        if self.default != None:
            default_case = attrsearch(self.default.arg, 'name', self.children)
            if default_case == None:
                err_add(errors, self.pos, 'DEFAULT_CASE_NOT_FOUND',
                        self.default.arg)

class Case(DataDefStatement):
    def __init__(self, parent, pos, module, arg):
        DataDefStatement.__init__(self, parent, pos,
                             self.__class__.__name__.lower(),
                             module, arg)
        # argument
        self.name = arg
        # statements
        self.description = None
        self.status = None
        self.reference = None
        self.children = []
        self.augment = []

    def validate(self, errors):
        validate_identifier(self.name, self.pos, errors)
        validate_children(self, self.children, errors, self.i_config)

class Augment(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.expr = arg
        # statements
        self.description = None
        self.status = None
        self.when_ = None
        self.typedef = []
        self.grouping = []
        self.children = []  # leaves, containers, lists, leaf-lists, uses
        # extra
        self.i_path = None
        self.i_expanded_children = []
        self.i_validated = False
        self.i_target_node = None

    def validate(self, errors, recover=True):
        if self.i_validated == False:
            # check that it's syntactically correct
            if re_schema_nid.search(self.expr) == None:
                err_add(errors, self.pos, 'SYNTAX_ERROR',
                        'bad augment target node expression')
                return False
            #validate_children(self, self.children, errors)

        self.i_validated = True

        for x in self.typedef:
            x.validate(errors)
        for x in self.grouping:
            x.validate(errors)

        self.i_path = [(m[1], m[3]) \
                       for m in re_schema_nid_part.findall(self.expr)]
        (prefix, identifier) = self.i_path[0]
        module = self.i_module.prefix_to_module(prefix, self.pos, errors)
        if module == None:
            return False
        node = module.search_child(identifier)
        if node == None:
            err_add(errors, self.pos, 'NODE_NOT_FOUND',
                    (module.name, identifier))
            return False
        for (prefix, identifier) in self.i_path[1:]:
            module = self.i_module.prefix_to_module(prefix, self.pos, errors)
            if module == None:
                return False
            if 'i_expanded_children' in node.__dict__:
                node = search_child(node.i_expanded_children, module.name,
                                    identifier)
                if node == None:
                    # we might recover from this error, if some other augment
                    # adds this node
                    if recover == False:
                        err_add(errors, self.pos, 'NODE_NOT_FOUND',
                                (module.name, identifier))
                    return 'may_recover'
            else:
                err_add(errors, self.pos, 'NODE_NOT_FOUND',
                        (module.name, identifier))
                return False
                
        self.i_target_node = node

        # first, create the expanded children...
        validate_children(self, self.children, errors)
        # ... then copy the expanded children into the target node
        for c in self.i_expanded_children:
            self.i_target_node.i_expanded_children.append(c)

        return True

class AnyXML(DataDefStatement):
    def __init__(self, parent, pos, module, arg):
        SchemaNodeStatement.__init__(self, parent, pos,
                                self.__class__.__name__.lower(),
                                module, arg)
        # argument
        self.name = arg
        # statements
        self.config = None
        self.status = None
        self.description = None
        self.reference = None
        self.mandatory = None

    def validate(self, errors):
        validate_identifier(self.name, self.pos, errors)

    def validate_post_augment(self, errors):
        return True

class Rpc(SchemaNodeStatement):
    def __init__(self, parent, pos, module, arg):
        SchemaNodeStatement.__init__(self, parent, pos,
                                self.__class__.__name__.lower(),
                                module, arg)
        # argument
        self.name = arg
        # statements
        self.status = None
        self.description = None
        self.reference = None
        self.input = None
        self.output = None
        self.children = [] # input / output
        self.typedef = []
        self.grouping = []
        
    def validate(self, errors):
        validate_identifier(self.name, self.pos, errors)
        if self.input != None:
            self.children.append(self.input)
        if self.output != None:
            self.children.append(self.output)
        validate_children(self, self.children, errors)

class Params(SchemaNodeStatement):
    def __init__(self, parent, pos, arg, module):
        SchemaNodeStatement.__init__(self, parent, pos,
                                arg,
                                module, arg)
        # argument
        self.name = arg
        # statements
        self.children = []  # leaves, containers, lists, leaf-lists, uses
        self.typedef = []
        self.grouping = []
        self.augment = []
        
    def validate(self, errors):
        validate_children(self, self.children, errors)

class Notification(SchemaNodeStatement):
    def __init__(self, parent, pos, module, arg):
        SchemaNodeStatement.__init__(self, parent, pos,
                                self.__class__.__name__.lower(),
                                module, arg)
        # argument
        self.name = arg
        # statements
        self.status = None
        self.description = None
        self.reference = None
        self.children = []  # leaves, containers, lists, leaf-lists, uses
        self.typedef = []
        self.grouping = []
        self.augment = []
        
    def validate(self, errors):
        validate_identifier(self.name, self.pos, errors)
        validate_children(self, self.children, errors)

## this class represents the usage of an (unknown) extension
class ExtensionStatement(Statement):
    def __init__(self, parent, pos, identifier, prefix=None, arg=None):
        if prefix == None:
            keyword = identifier
        else:
            keyword = (prefix, identifier)
        Statement.__init__(self, parent, pos, keyword, parent.i_module, arg)
        # argument
        self.prefix = prefix
        self.identifier = identifier
        # extra
        self.i_def_module = None # module where the extension is defined

    def validate_extensions(self, module, errors):
        if self.i_def_module == None:
            self.i_def_module = module.prefix_to_module(self.prefix, self.pos,
                                                        errors)
        # possibly inherit i_module
        for x in self.substmts:
            if x.prefix == None:
                x.i_def_module = self.i_def_module
        # recurse only if this prefix was found
        if self.i_def_module != None:
            ext = self.i_def_module.search_extension(self.identifier)
            if ext == None:
                err_add(errors, self.pos, 'EXTENSION_NOT_DEFINED',
                        (self.identifier, self.i_module.name))
            elif self.arg != None and ext.argument == None:
                err_add(errors, self.pos, 'EXTENSION_ARGUMENT_PRESENT',
                        self.identifier)
            elif self.arg == None and ext.argument != None:
                err_add(errors, self.pos, 'EXTENSION_NO_ARGUMENT_PRESENT',
                        self.identifier)

            Statement.validate_extensions(self, module, errors)

### parser

class YangParser(object):
    def __init__(self, ctx, filename):
        self.ctx = ctx
        self.pos = Position(filename)
        dbg("BEGIN parse %s" % filename)
        fd = open(filename, "r")
        self.tokenizer = tokenizer.YangTokenizer(fd, self.pos, ctx.errors)

    def parse_module(self):
        # parse the 'module <name> {' part here, since we need to pass
        # the Module object to some other functions in the child spec
        try:
            keywd = self.tokenizer.get_keyword()
            if keywd not in ['module', 'submodule']:
                err_add(self.ctx.errors, self.pos, 'UNEXPECTED_KEYWORD_N',
                        (tokenizer.tok_to_str(keywd), 'module, submodule'))
                raise Abort
            is_submodule = (keywd == 'submodule')
            self.module = Module(self.pos, self.ctx, self.tokenizer.get_string(),
                                 is_submodule)
            self.pos.module_name = self.module.name
            tok = self.tokenizer.get_string()
            if tok != tokenizer.T_OPEN_BRACE:
                err_add(self.ctx.errors, self.pos, 'UNEXPECTED_TOKEN_1',
                        (tokenizer.tok_to_str(tok), '{'))
                raise Abort
            tok = self.tokenizer.get_keyword()
            self.parse_stmt_list(self.module, self.module_children(keywd), tok)
        except Abort:
            return None
        except Eof, e:
            err_add(self.ctx.errors, self.pos, 'EOF_ERROR', ())
            return None
            

        try:
            # call get_tok to skip whitespace and comments
            # we expect a Eof at this point, everything else is an error
            self.tokenizer.get_string()
        except Eof:
            dbg("END parse %s" % self.pos.filename)
            return self.module
        except:
            pass
        err_add(self.ctx.errors, self.pos, 'TRAILING_GARBAGE', ())
        return None

    def module_children(self, modtype):
        module = self.module
        # trick to create a recursive definition of type
        type_children_rec = []
        type_children = \
             [[('range', '?', None,
                (lambda parent, pos, arg: Range(parent, pos, module, arg), 1,
                 [('error-message', '?', ('error_message', None,None),()),
                  ('error-app-tag', '?', ('error_app_tag', None,None),())]))],
              [('length', '?', None,
                (lambda parent, pos, arg: Length(parent, pos, module, arg), 1,
                 [('error-message', '?', ('error_message', None,None),()),
                  ('error-app-tag', '?', ('error_app_tag', None,None),())])),
               ('pattern', '?', ('pattern', None, 'expr'),
                (lambda parent, pos, arg: Pattern(parent, pos, module, arg), 1,
                 [('error-message', '?', ('error_message', None,None),()),
                  ('error-app-tag', '?', ('error_app_tag', None,None),())]))],
              [('enum', '+', ('enum', None, 'name'),
                (lambda parent, pos, arg: Enum(parent, pos, module, arg), 1,
                 [('value', '?', None, ()),
                  ('status', '?', ('', self.chk_status, None), ()),
                  ('description', '?', None, ()),
                  ('reference', '?', None, ())]))],
              [('bit', '+', ('bit', None, 'name'),
                (lambda parent, pos, arg: Bit(parent, pos, module, arg), 1,
                 [('position', '1', None, ()),
                  ('status', '?', ('', self.chk_status, None), ()),
                  ('description', '?', None, ()),
                  ('reference', '?', None, ())]))],
              [('path', '?', None,
                (lambda parent, pos, arg: Path(parent, pos, module, arg),
                 1, []))],
              [('type', '*', None,
                (lambda parent, pos, arg: Type(parent, pos, module, arg), 1,
                 [('$choice', '?', None,
                   type_children_rec)]))]]
        type_stmt = \
            ('type', '1', None,
             (lambda parent, pos, arg: Type(parent, pos, module, arg), 1,
              [('$choice', '?', None,
                type_children)]))
        type_children_rec.extend(type_children)
        
        typedef_stmt = \
            ('typedef', '*',
             ('', None, 'name'),
             (lambda parent, pos, arg: Typedef(parent, pos, module, arg), 1,
              [type_stmt,
               ('units', '?', None, ()),
               ('default', '?', None, ()),
               ('status', '?', ('', self.chk_status, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ())]))

        # trick to get recursive definitions
        data_def_stmts = []
        data_def_ext_stmts = []

        grouping_stmt = \
            ('grouping', '*',
             ('', None, 'name'),
             (lambda parent, pos, arg: Grouping(parent, pos, module, arg),
              1,
              [('status', '?', ('', self.chk_status, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ()),
               ('$any-order', '?', None, data_def_ext_stmts)]))

        must_stmt = \
            ('must', '*', None,
             (lambda parent, pos, arg: Must(parent, pos, module, arg), 1,
              [('error-message', '?', ('error_message', None, None), ()),
               ('error-app-tag', '?', ('error_app_tag', None, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ()),
               ]))
        
        leaf_stmt = \
            ('leaf', '*', ('children', None, 'name'),
             (lambda parent, pos, arg: Leaf(parent, pos, module, arg), 1,
              [type_stmt,
               ('units', '?', None, ()),
               must_stmt,
               ('default', '?', None, ()),
               ('config', '?', ('', self.chk_config, None), ()),
               ('mandatory', '?', ('', self.chk_mandatory, None), ()),
               ('status', '?', ('', self.chk_status, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ()),
               ]))

        leaf_list_stmt = \
            ('leaf-list', '*', ('children', None, 'name'),
             (lambda parent, pos, arg: LeafList(parent, pos, module, arg), 1,
              [type_stmt,
               ('units', '?', None, ()),
               must_stmt,
               ('config', '?', ('', self.chk_config, None), ()), 
               ('min-elements', '?', ('min_elements', None, None), ()),
               ('max-elements', '?', ('max_elements', None, None), ()),
               ('ordered-by', '?', ('ordered_by', self.chk_ordered_by,None), ()),
               ('status', '?', ('', self.chk_status, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ()),
               ]))
               
        list_stmt = \
            ('list', '*', ('children', None, 'name'),
             (lambda parent, pos, arg: List(parent, pos, module, arg), 1,
              [must_stmt,
               ('key', '?', None, ()),
               ('unique', '*', None, ()),
               ('config', '?', ('', self.chk_config, None), ()),
               ('min-elements', '?', ('min_elements', None, None), ()),
               ('max-elements', '?', ('max_elements', None, None), ()),
               ('ordered-by', '?', ('ordered_by', self.chk_ordered_by, None),()),
               ('status', '?', ('', self.chk_status, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ()),
               ('$any-order', '?', None, data_def_ext_stmts)]))

        container_stmt = \
            ('container', '*', ('children', None, 'name'),
             (lambda parent, pos, arg: Container(parent, pos, module, arg), 1,
              [must_stmt,
               ('presence', '?', None, ()),
               ('config', '?', ('', self.chk_config, None), ()),
               ('status', '?', ('', self.chk_status, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ()),
               ('$any-order', '?', None, data_def_ext_stmts)]))

        anyxml_stmt = \
            ('anyxml', '*', ('children', None, 'name'),
             (lambda parent, pos, arg: AnyXML(parent, pos, module, arg), 1,
              [('config', '?', ('', self.chk_config, None), ()),
               ('mandatory', '?', ('', self.chk_mandatory, None), ()),
               ('status', '?', ('', self.chk_status, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ())]))

        case_stmt = \
               ('case', '*', ('children', None, 'name'),
                (lambda parent, pos, arg: Case(parent, pos, module, arg), 1,
                 [('status', '?', ('', self.chk_status, None), ()),
                  ('description', '?', None, ()),
                  ('reference', '?', None, ()),
                  ('$any-order', '?', None, data_def_stmts)]))

        choice_stmt = \
            ('choice', '*', ('children', None, 'name'),
             (lambda parent, pos, name: Choice(parent, pos, module, name), 1,
              [('default', '?', None, ()),
               ('mandatory', '?', ('', self.chk_mandatory, None), ()),
               ('status', '?', ('', self.chk_status, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ()),
               case_stmt,
               list_stmt,
               leaf_stmt,
               container_stmt,
               anyxml_stmt,
               leaf_list_stmt]))

        uses_children_rec = []
        uses_stmt = \
            ('uses', '*', ('children', None, 'name'),
             (lambda parent, pos, name: Uses(parent, pos, module, name), 1,
              uses_children_rec))

        refine_leaf_stmt = \
            ('leaf', '*', ('children', None, 'name'),
             (lambda parent, pos, name: Leaf(parent, pos, module, name), 1,
              [must_stmt,
               ('default', '?', None, ()),
               ('config', '?', ('', self.chk_config, None), ()),
               ('mandatory', '?', ('', self.chk_mandatory, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ()),
               ]))

        refine_leaf_list_stmt = \
            ('leaf-list', '*', ('children', None, 'name'),
             (lambda parent, pos, name: LeafList(parent, pos, module, name), 1,
              [must_stmt,
               ('config', '?', ('', self.chk_config, None), ()),
               ('min-elements', '?', ('min_elements', None, None), ()),
               ('max-elements', '?', ('max_elements', None, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ()),
               ]))

        refine_list_children_rec = []
        refine_list_stmt = \
            ('list', '*', ('children', None, 'name'),
             (lambda parent, pos, name: List(parent, pos, module, name),1,
              refine_list_children_rec))

        refine_container_children_rec = []
        refine_container_stmt = \
            ('container', '*', ('children', None, 'name'),
             (lambda parent, pos, name: Container(parent, pos, module, name), 1,
              refine_container_children_rec))

        refine_case_children_rec = []
        refine_case_stmt = \
            ('case', '*', ('children', None, 'name'),
             (lambda parent, pos, name: Case(parent, pos, module, name), 1,
              [('description', '?', None, ()),
               ('reference', '?', None, ()),
               ('$any-order', '?', None,
                [refine_leaf_stmt,
                 refine_container_stmt,
                 refine_leaf_list_stmt,
                 refine_list_stmt,
                 uses_stmt])]))

        refine_choice_stmt = \
            ('choice', '*', ('children', None, 'name'),
             (lambda parent, pos, name: Choice(parent, pos, module, name), 1,
              [('default', '?', None, ()),
               ('mandatory', '?', ('', self.chk_mandatory, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ()),
               refine_case_stmt]))

        refine_container_children_rec.extend(
            [must_stmt,
             ('config', '?', ('', self.chk_config, None), ()),
             ('description', '?', None, ()),
             ('reference', '?', None, ()),
             ('$any-order', '?', None,
              [refine_leaf_stmt,
               refine_container_stmt,
               refine_leaf_list_stmt,
               refine_list_stmt,
               refine_choice_stmt,
               uses_stmt])])
        
        refine_list_children_rec.extend(
            [must_stmt,
             ('config', '?', ('', self.chk_config, None), ()),
             ('min-elements', '?', ('min_elements', None, None), ()),
             ('max-elements', '?', ('max_elements', None, None), ()),
             ('description', '?', None, ()),             
             ('reference', '?', None, ()),
             ('$any-order', '?', None,
              [refine_leaf_stmt,
               refine_container_stmt,
               refine_leaf_list_stmt,
               refine_list_stmt,
               refine_choice_stmt,
               uses_stmt])])

        uses_children_rec.extend(
            [('status', '?', ('', self.chk_status, None), ()),
             ('description', '?', None, ()),
             ('reference', '?', None, ()),
             ('$any-order', '?', None,
              [refine_leaf_stmt,
               refine_container_stmt,
               refine_leaf_list_stmt,
               refine_list_stmt,
               refine_choice_stmt])])
        
        module_header_stmts = \
            [('yang-version', '?',
              ('yang_version', self.chk_yang_version, None), ()),
             ('namespace', '1', ('namespace', self.chk_uri, None), ()),
             ('prefix', '1', ('prefix', None,None), ())]
        
        sub_module_header_stmts = \
            [('yang-version', '?',
              ('yang_version', self.chk_yang_version, None), ()),
             ('belongs-to', '1', ('belongs_to', None,None), ())]
        
        linkage_stmts = \
            [('import', '*',
              ('import_',
               lambda mod, name: mod.set_import(self, name),
               'modulename'),
              (lambda parent, pos, arg: Import(parent, pos, module, arg),
               1,
               [('prefix', '1', None, ())])),
             ('include', '*',
              ('',
               lambda mod, name: mod.set_include(self, name),
               'modulename'),
              (lambda parent, pos, arg: Include(parent, pos, module, arg),
               1, []))]

        meta_stmts = \
            [('organization', '?', None, ()),
             ('contact', '?', None, ()),
             ('description', '?', None, ()),
             ('reference', '?', None, ())]

        sub_module_meta_stmts = \
            [('organization', '?', None, ()),
             ('contact', '?', None, ()),
             ('description', '?', None, ()),
             ('reference', '?', None, ())]

        revision_stmts = \
            [('revision', '*', ('', None, 'date'),
              (lambda parent, pos, arg: Revision(parent, pos, module, arg), 1,
               [('description', '0', None, ())]))]

        input_stmt = \
            ('input', '?', None,
             (lambda parent, pos: Params(parent, pos, 'input', module), 0,
              [('$any-order', '?', None,
                data_def_ext_stmts)]))

        output_stmt = \
            ('output', '?', None,
             (lambda parent, pos: Params(parent, pos, 'output', module), 0,
              [('$any-order', '?', None,
                data_def_ext_stmts)]))

        augment_children = []
        augment_stmt = \
            ('augment', '**',
             ('', None, 'expr'),
             (lambda parent, pos, arg: Augment(parent, pos, module, arg), 1,
              [('status', '?', ('', self.chk_status, None), ()),
               ('description', '?', None, ()),
               ('reference', '?', None, ()),
               ('when', '?', ('when_', None, None), ()),
               ('$any-order', '?', None,
                augment_children)]))

        data_def_stmts.extend([leaf_stmt,
                               list_stmt,
                               leaf_list_stmt,
                               uses_stmt,
                               choice_stmt,
                               container_stmt,
                               anyxml_stmt,
                               augment_stmt])

        data_def_ext_stmts.extend(data_def_stmts + [typedef_stmt, grouping_stmt])
        augment_children.extend(data_def_ext_stmts + [case_stmt])
        
        body_stmts = \
            [('$any-order', '?', None,
              [('rpc', '*',
                ('children', None, 'name'),
                (lambda parent, pos, arg: Rpc(parent, pos, module, arg), 1,
                 [('status', '?', ('', self.chk_status, None), ()),
                  ('description', '?', None, ()),
                  ('reference', '?', None, ()),
                  typedef_stmt,
                  grouping_stmt,
                  input_stmt,
                  output_stmt])),
               ('notification', '*',
                ('children', None, 'name'),
                (lambda parent, pos, arg: Notification(parent, pos,
                                                       module, arg), 1,
                 [('status', '?', ('', self.chk_status, None), ()),
                  ('description', '?', None, ()),
                  ('reference', '?', None, ()),
                  ('$any-order', '?', None, data_def_ext_stmts)])),
               ('extension', '*',
                ('', None, 'name'),
                (lambda parent, pos, arg: Extension(parent, pos, module, arg), 1,
                 [('argument', '?',
                   ('', None, 'name'),
                   (lambda parent, pos, arg: Argument(parent, pos,
                                                      module, arg), 1,
                    [('yin-element', '?',
                      ('yin_element', self.chk_yin_elem, None), ())])),
                  ('status', '?', ('', self.chk_status, None), ()),
                  ('description', '?', None, ()),
                  ('reference', '?', None, ())]))] + \
              data_def_ext_stmts)]
        
        cut = ('$cut', '*', None, [])

        module_children = \
            module_header_stmts + \
            [cut] + \
            linkage_stmts + \
            [cut] + \
            meta_stmts + \
            [cut] + \
            revision_stmts + \
            [cut] + \
            body_stmts

        sub_module_children = \
            sub_module_header_stmts + \
            [cut] + \
            linkage_stmts + \
            [cut] + \
            sub_module_meta_stmts + \
            [cut] + \
            revision_stmts + \
            [cut] + \
            body_stmts

        if modtype == 'module':
            return module_children
        elif modtype == 'submodule':
            return sub_module_children
        

    # parse_stmt() is called when a keyword has been read, and it gets
    # a specification of arguments and substatements for the keyword.
    # It first creates a new class, by calling create_class_fun().
    # All substatements read will be assigned to attributes in the class.
    # multi-instance substatements is assumed to be a list of attributes.
    # By default, the class attribute name is the same as the keyword
    # for the substatement.  Note that *all* statements are represented
    # a classes.  The reason for this is that all statements might have
    # substatements by extensions.
    #
    # spec = (create_class_fun, number_of_args, children) | ()
    #   spec == () means class is Statement
    #   number_of_args = 0 | 1
    #   children = list of (keywd, occurance, extra, spec) |
    #                      ('$choice', occurance, None, alternatives) |
    #                      ('$any-order', '?', None, children)
    #   alternatives = list of children
    #   occurance = '1', '+', '?', '*', '**'
    #     '?' means optional, '1' means mandatory, '+' means at least one
    #     '*' means zero or more
    #     '**' means zero or more, and argument not unique
    #     if '*' or '**' or '+', class.attr MUST be a list
    #   extra = None | (attrstr, attrhook, classkeystr)
    #   attrstr = () | <string>
    #     the name of the attribute in class to hold the substatement
    #     attrstr == () means that the name is the same as keywd
    #   attrhook = None | lambda(module, arg)
    #     arg is the argument to the keywd
    #     called after the sub stmt has been set/added to class.attr
    #   classkeystr = None | <string>
    #     set for multi-instance statements ('+' and '*' and '**') where every
    #     substmtclass.classkeystr is unique (i.e. we check for duplicates)
    #   hook = lambda(<class instance>)
    def parse_stmt(self, parent, (new_class_fun, nargs, children),
                   do_extensions=True):
        if nargs == 0:
            x = new_class_fun(parent, self.pos)
        else:
            arg = self.tokenizer.get_string()
            if type(arg) == type(''):
                x = new_class_fun(parent, self.pos, arg)
            else:
                err_add(self.ctx.errors, self.pos,
                        'EXPECTED_ARGUMENT', tokenizer.tok_to_str(arg))
                raise Abort
        tok = self.tokenizer.get_string()
        if tok == tokenizer.T_SEMICOLON:
            # check if any child is mandatory
            for (keywd, occurance, extra, cspec) in children:
                if occurance == '1' or occurance == '+':
                    err_add(self.ctx.errors, self.pos, 'UNEXPECTED_KEYWORD_1',
                            (tokenizer.tok_to_str(tok), keywd));
                    raise Abort
        elif tok == tokenizer.T_OPEN_BRACE:
            tok = self.tokenizer.get_keyword()
            self.parse_stmt_list(x, children, tok)
        else:
            err_add(self.ctx.errors, self.pos,
                    'UNEXPECTED_TOKEN_N', (tokenizer.tok_to_str(tok), '; {'))
            raise Abort
        return x

    # pre:  { read
    # post: } read
    def parse_stmt_list(self, x, children, tok, do_extensions = True):
        if self.ctx.canonical != True:
            return self.parse_stmt_list_noorder(x, children, tok)
        i = 0
        # ncur counts number of instances found (only for multi-instace
        # children)
        ncur = 0
        while i < len(children):
            multi_instance = False
            (keywd, occurance, extra, cspec) = children[i]
            if tok == keywd:
                attrhook = None
                argname = None
                if cspec == ():
                    cspec = (lambda parent, pos, arg: Statement(parent, pos,
                                                                keywd,
                                                                self.module,
                                                                arg),
                             1, [])
                if extra == None:
                    attr = keywd
                else:
                    (attr, attrhook, argname) = extra
                    if attr == '':
                        attr = keywd
                # remember current position
                old_pos = Position(self.pos.filename)
                old_pos.line = self.pos.line
                old_pos.module_name = self.pos.module_name
                dbg("entering gen_stmt for %s" % keywd)
                cstmt = self.parse_stmt(x, cspec)
                x.substmts.append(cstmt)
                dbg("did gen_stmt for %s in %s" % (keywd, x.keyword))
                if occurance == '+' or occurance == '*' or occurance == '**':
                    # multi-instance attribute
                    if argname != None:
                        # get the argument for this keyword
                        arg = cstmt.__dict__[argname]
                        # make sure it's not already defined
                        if (occurance != '**' and
                            attrsearch(arg, argname, x.__dict__[attr])):
                            err_add(self.ctx.errors, old_pos,
                                    'DUPLICATE_STATEMENT', arg)
                    x.__dict__[attr].append(cstmt)
                    ncur = ncur + 1
                    multi_instance = True
                else:
                    # single-instance attribute
                    x.__dict__[attr] = cstmt
                if attrhook != None:
                    attrhook(x, cstmt)
                dbg("ret from  gen_stmt for %s %s" % \
                    (keywd, x.keyword))
                tok = self.tokenizer.get_keyword()
                dbg("new tok %s at line %d" % (tok, self.pos.line))
                if tok != keywd and not is_prefixed(tok):
                    multi_instance = False
            elif is_prefixed(tok):
                # got a prefixed keyword - this is an extension
                self.parse_extension(x, tok, in_extension=True)
                ## FIXME: hack - use descriptive variable.  fix this
                ## when we handle any-order
                tok = self.tokenizer.get_keyword()
                dbg("new extension tok %s at line %d" % (tok, self.pos.line))
                multi_instance = True
            elif keywd == '$choice':
                j = 0
                found = False
                while not found and j < len(cspec):
                    # check if this alternative matches - check for a
                    # match with each optional keyword
                    k = 0
                    while not found and k < len(cspec[j]):
                        if tok == cspec[j][k][0]:
                            # this choice alternative matched, use it
                            tok = self.parse_stmt_list(x, cspec[j], tok,
                                                       do_extensions = False)
                            found = True
                        # if this is optional, check the next keyword
                        occ = cspec[j][k][1]
                        if (occ == '+' or occ == '1'):
                            break
                        k = k + 1
                    j = j + 1
                if (not found and
                    (occurance == '1' or occurance == '+')):
                    # FIXME: should say expected one of ...
                    err_add(self.ctx.errors, self.pos,
                            'UNEXPECTED_KEYWORD_1',
                            (tokenizer.tok_to_str(tok), cspec[0][0][0]))
                    raise Abort
            elif keywd == '$any-order':
                while True:
                    j = 0
                    found = False
                    # loop through all and see which one matches
                    while j < len(cspec):
                        if tok == cspec[j][0]:
                            dbg('any matched %s' % tok)
                            found = True
                            tok = self.parse_stmt_list(x, [cspec[j]], tok,
                                                       do_extensions = False)
                            break
                        j = j + 1
                    if not found:
                        # no more of the any elements found
                        dbg("no more any found")
                        break
            elif keywd == '$cut':
                pass
            elif occurance == '?' or occurance == '*' or occurance == '**':
                dbg("ignore optional %s" % keywd)
                pass
            elif occurance == '+' and ncur >= 1:
                pass
            else:
                err_add(self.ctx.errors, self.pos, 'UNEXPECTED_KEYWORD_1',
                        (tokenizer.tok_to_str(tok), keywd));
                raise Abort
            if not multi_instance:
                ncur = 0
                i = i + 1
        dbg("all children read for %s" % x.keyword)
        # all children read, check extensions if needed
        if do_extensions:
            self.parse_extsubstmts(x, tok)
            return None
        else:
            # return the read but not consumed token
            return tok

    def match_child(self, tok, children):
        i = 0
        while i < len(children):
            (keywd, occurance, extra, cspec) = children[i]
            if keywd == tok:
                if occurance == '1' or occurance == '?':
                    return (children[i], children[:i] + children[i+1:])
                if occurance == '+':
                    c = (keywd, '*', extra, cspec)
                    return (children[i], children[:i] + [c] + children[i+1:])
                else:
                    return (children[i], children)
            elif keywd == '$choice':
                j = 0
                while j < len(cspec):
                    # check if this alternative matches - check for a
                    # match with each optional keyword
                    res = self.match_child(tok, cspec[j])
                    if res != None:
                        # this choice alternative matched, use it
                        (rchild, rchildren) = res
                        # remove the choice and add rchildren to children
                        return (rchild,
                                children[:i] + rchildren + children[i+1:])
                    j = j + 1
            elif keywd == '$any-order':
                res = self.match_child(tok, cspec)
                if res != None:
                    (rchild, rchildren) = res
                    return (rchild, children)
            elif keywd == '$cut':
                for (keywd, occurance, extra, cspec) in children[:i]:
                    if occurance == '1' or occurance == '+':
                        err_add(self.ctx.errors, self.pos,
                                'UNEXPECTED_KEYWORD_1',
                                (tokenizer.tok_to_str(tok), keywd));
                        raise Abort
            # check next in children
            i = i + 1
        return None

    # pre:  { read
    # post: } read
    def parse_stmt_list_noorder(self, x, children, tok):
        rest_children = []
        while True:
            if is_prefixed(tok):
                # got a prefixed keyword - this is an extension
                self.parse_extension(x, tok, in_extension=True)
            else:
                res = self.match_child(tok, children)
                if res != None:
                    ((keywd, occurance, extra, cspec), children) = res
                    attrhook = None
                    argname = None
                    if cspec == ():
                        cspec = (lambda parent, pos, arg: Statement(parent, pos,
                                                               keywd,
                                                               self.module,
                                                               arg),
                                 1, [])
                    if extra == None:
                        attr = keywd
                    else:
                        (attr, attrhook, argname) = extra
                        if attr == '':
                            attr = keywd
                    # remember current position
                    old_pos = Position(self.pos.filename)
                    old_pos.line = self.pos.line
                    old_pos.module_name = self.pos.module_name
                    dbg("entering gen_stmt for %s" % keywd)
                    cstmt = self.parse_stmt(x, cspec)
                    x.substmts.append(cstmt)
                    dbg("did gen_stmt for %s in %s" % \
                        (keywd, x.keyword))
                    if occurance == '+' or occurance == '*' or occurance == '**':
                        # multi-instance attribute
                        if argname != None:
                            # get the argument for this keyword
                            arg = cstmt.__dict__[argname]
                            # make sure it's not already defined
                            if (occurance != '**' and
                                attrsearch(arg, argname, x.__dict__[attr])):
                                err_add(self.ctx.errors, old_pos,
                                        'DUPLICATE_STATEMENT', arg)
                        x.__dict__[attr].append(cstmt)
                    else:
                        # single-instance attribute
                        x.__dict__[attr] = cstmt
                    if attrhook != None:
                        attrhook(x, cstmt)
                    dbg("ret from  gen_stmt for %s %s" % \
                        (keywd, x.keyword))
                elif tok == tokenizer.T_CLOSE_BRACE:
                    for (keywd, occurance, extra, cspec) in children:
                        if occurance == '1' or occurance == '+':
                            err_add(self.ctx.errors, self.pos,
                                    'UNEXPECTED_KEYWORD_1',
                                    (tokenizer.tok_to_str(tok), keywd));
                            raise Abort
                    return
                else:
                    err_add(self.ctx.errors, self.pos,
                            'UNEXPECTED_KEYWORD', tokenizer.tok_to_str(tok));
                    raise Abort
            tok = self.tokenizer.get_keyword()
            dbg("new tok %s at line %d" % (tok, self.pos.line))

    # read a single extension statement
    # pre: tok is a prefixed keyword
    def parse_extension(self, parent, tok, in_extension=False):
        if is_prefixed(tok):
            (prefix, identifier) = tok
        elif is_local(tok) and in_extension == True:
            # got an unprefixed keyword in an extension - ok (I think)
            prefix = None
            identifier = tok
        else:
            err_add(self.ctx.errors, self.pos,
                    'UNEXPECTED_KEYWORD', tokenizer.tok_to_str(tok));
            raise Abort
        pos = self.pos
        # red the optional argument
        tok = self.tokenizer.get_string()
        if type(tok) == type(''):
            # an argument was present, read next tok
            arg = tok
            tok = self.tokenizer.get_string()
        else:
            # no argument present, check if that was ok
            arg = None
        stmt = ExtensionStatement(parent, pos, identifier, prefix, arg)
        parent.substmts.append(stmt)
        if tok == tokenizer.T_SEMICOLON:
            return
        elif tok == tokenizer.T_OPEN_BRACE:
            self.parse_extsubstmts(stmt, None, in_extension=True)
        else:
            err_add(self.ctx.errors, self.pos,'UNEXPECTED_TOKEN_1',
                    (tokenizer.tok_to_str(tok), ';'))
            raise Abort

    # parse a sequence of extensions
    # post: has consumed corresponding CLOSE_BRACE
    def parse_extsubstmts(self, parent, tok=None, in_extension=False):
        if tok == None:
            tok = self.tokenizer.get_keyword()
        if is_prefixed(tok) or is_local(tok):
            self.parse_extension(parent, tok, in_extension)
        elif tok == tokenizer.T_CLOSE_BRACE:
            return
        else:
            err_add(self.ctx.errors, self.pos,
                    'UNEXPECTED_KEYWORD', tokenizer.tok_to_str(tok));
            raise Abort
        
        self.parse_extsubstmts(parent, None, in_extension)

    def chk_yang_version(self, x, vsn):
        if vsn.arg not in ['1']:
            err_add(self.ctx.errors, self.pos,
                    'BAD_VALUE', (vsn.arg, 'yang-version'))

    def chk_uri(self, x, uri):
        if re_uri.search(uri.arg) == None:
            err_add(self.ctx.errors, self.pos,
                    'BAD_VALUE', (uri.arg, 'namespace'))

    def chk_mandatory(self, x, mandatory):
        if mandatory.arg not in ['true', 'false']:
            err_add(self.ctx.errors, self.pos,
                    'BAD_VALUE', (mandatory.arg, 'mandatory'))

    def chk_config(self, x, config):
        if config.arg not in ['true', 'false']:
            err_add(self.ctx.errors, self.pos,
                    'BAD_VALUE', (config.arg, 'config'))

    def chk_status(self, x, status):
        if status.arg not in ['current', 'obsolete', 'deprecated']:
            err_add(self.ctx.errors, self.pos,
                    'BAD_VALUE', (status.arg, 'status'))

    def chk_ordered_by(self, x, ordered_by):
        if ordered_by.arg not in ['system', 'user']:
            err_add(self.ctx.errors, self.pos,
                    'BAD_VALUE', (ordered_by.arg, 'ordered-by'))

    def chk_param(self, x, param):
        if param.arg not in ['in', 'out']:
            err_add(self.ctx.errors, self.pos,
                    'BAD_VALUE', (param.arg, 'param'))

    def chk_yin_elem(self, x, yin_elem):
        if yin_elem.arg not in ['true', 'false']:
            err_add(self.ctx.errors, self.pos,
                    'BAD_VALUE', (yin_elem.arg, 'yin-element'))

def keyword_to_str(keyword):
    if is_prefixed(keyword):
        (prefix, keyword) = keyword
        return prefix + ":" + keyword
    else:
        return keyword

### YANG output

# FIXME not complete.  rewrite.  use the stmt spec to get canonical order

def dump_yang(stmt, writef, indent=''):
    str = indent + keyword_to_str(stmt.keyword)
    writef(str)
    if stmt.arg != None:
        if len(str) + len(stmt.arg) < 77:
            writef(' ' + yang_quote(stmt.arg))
        else:
            writef('\n')
            writef(yang_fmt_text(indent + '  ', stmt.arg))
    if len(stmt.substmts) == 0:
        writef(";\n")
    else:
        writef(" {\n")
        for substmt in stmt.substmts:
            dump_yang(substmt, writef, indent + '  ')
        writef(indent + "}\n")
#    if stmt.keyword in yang_extra_newline:
#        writef("\n")

def yang_quote(str):
    return '"' + str + '"'

def yang_fmt_text(indent, str):
    return indent + '"' + str + '"'

### YANG built-in types

class TypeSpec(object):
    def __init__(self):
        self.definition = ""
        pass
    def str_to_val(self, errors, pos, str):
        return str;
    def validate(self, errors, pos, val, errstr=''):
        return True;
    def restrictions(self):
        return []
    
class IntTypeSpec(TypeSpec):
    def __init__(self, min, max):
        TypeSpec.__init__(self)
        self.min = min
        self.max = max

    def str_to_val(self, errors, pos, str):
        try:
            dbg('trying to convert "%s" to an int...' % str)
            if str in ['min', 'max']:
                return str
            return int(str, 0)
        except ValueError:
            err_add(errors, pos, 'TYPE_VALUE',
                    (str, self.definition, 'not an integer'))
            return None

    def validate(self, errors, pos, val, errstr = ''):
        if val < self.min or val > self.max:
            err_add(errors, pos, 'TYPE_VALUE',
                    (str(val), self.definition, 'range error' + errstr))
            return False
        else:
            return True
    
    def restrictions(self):
        return ['range']
    

class FloatTypeSpec(TypeSpec):
    def __init__(self, bits):
        TypeSpec.__init__(self)
        self.bits = bits

    def str_to_val(self, errors, pos, str):
        try:
            dbg('trying to convert "%s" to a float...' % str)
            if str in ['min', 'max']:
                return str
            return float(str)
        except ValueError:
            err_add(errors, pos, 'TYPE_VALUE',
                    (str, self.definition, 'not a float'))
            return None

    # FIXME: validate 32/64 bit floats

    def restrictions(self):
        return ['range']
    
class BooleanTypeSpec(TypeSpec):
    def __init__(self):
        TypeSpec.__init__(self)

    def str_to_val(self, errors, pos, str):
        dbg('trying to convert "%s" to a boolean...' % str)
        if str == 'true': return True;
        elif str == 'false': return False
        else:
            err_add(errors, pos, 'TYPE_VALUE',
                    (str, self.definition, 'not a boolean'))
            return None

class StringTypeSpec(TypeSpec):
    def __init__(self):
        TypeSpec.__init__(self)

    def restrictions(self):
        return ['pattern', 'length']
    
class BinaryTypeSpec(TypeSpec):
    def __init__(self):
        TypeSpec.__init__(self)

    # FIXME: validate base64 encoding

    def restrictions(self):
        return ['length']
    
class EmptyTypeSpec(TypeSpec):
    def __init__(self):
        TypeSpec.__init__(self)

    def str_to_val(self, errors, pos, str):
        err_add(errors, pos, 'BAD_DEFAULT_VALUE', 'empty')
        return None

## type restrictions

class RangeTypeSpec(TypeSpec):
    def __init__(self, base, ranges):
        TypeSpec.__init__(self)
        self.base = base
        self.ranges = ranges

    def str_to_val(self, errors, pos, str):
        return self.base.str_to_val(errors, pos, str)

    def validate(self, errors, pos, val, errstr=''):
            if self.base.validate(errors, pos, val, errstr) == False:
                return False
            for (lo, hi) in self.ranges:
                if ((lo == 'min' or val >= lo) and
                    (hi == None or hi == 'max' or val <= hi)):
                    return True
            err_add(errors, pos, 'TYPE_VALUE',
                    (str(val), self.definition, 'range error' + errstr))
            return False

    def restrictions(self):
        return self.base.restrictions()

class LengthTypeSpec(TypeSpec):
    def __init__(self, base, lengths):
        TypeSpec.__init__(self)
        self.base = base
        self.lengths = lengths

    def str_to_val(self, errors, pos, str):
        return self.base.str_to_val(errors, pos, str)

    def validate(self, errors, pos, val, errstr=''):
        if self.base.validate(errors, pos, val, errstr) == False:
            return False
        vallen = len(val)
        for (lo, hi) in self.lengths:
            if vallen >= lo and (hi == None or vallen <= hi):
                return True
        err_add(errors, pos, 'TYPE_VALUE',
                (val, self.definition, 'length error' + errstr))
        return False

    def restrictions(self):
        return self.base.restrictions()

class PatternTypeSpec(TypeSpec):
    def __init__(self, base, re):
        TypeSpec.__init__(self)
        self.base = base
        self.re = re

    def str_to_val(self, errors, pos, str):
        return self.base.str_to_val(errors, pos, str)

    def validate(self, errors, pos, val, errstr=''):
        if self.base.validate(errors, pos, val, errstr) == False:
            return False
        ret = False
        if self.re.regexpExec(val) == 1:
            return True
        else:
            err_add(errors, pos, 'TYPE_VALUE',
                    (val, self.definition, 'pattern mismatch' + errstr))
            return False
    
    def restrictions(self):
        return self.base.restrictions()

class EnumerationTypeSpec(TypeSpec):
    def __init__(self, enums):
        TypeSpec.__init__(self)
        # no base - no restrictions allowed
        self.enums = [(e.name, e.i_value) for e in enums]

    def validate(self, errors, pos, val, errstr = ''):
        if keysearch(val, 0, self.enums) == None:
            err_add(errors, pos, 'TYPE_VALUE',
                    (val, self.definition, 'enum not defined' + errstr))
            return False
        else:
            return True

class BitsTypeSpec(TypeSpec):
    def __init__(self, bits):
        TypeSpec.__init__(self)
        # no base - no restrictions allowed
        self.bits = [(b.name, b.i_position) for b in bits]

    def str_to_val(self, errors, pos, str):
        return str.split()

    def validate(self, errors, pos, val, errstr = ''):
        for v in val:
            if keysearch(v, 0, self.bits) == None:
                err_add(errors, pos, 'TYPE_VALUE',
                        (v, self.definition, 'bit not defined' + errstr))
                return False
        return True

class PathTypeSpec(TypeSpec):
    def __init__(self, target_node):
        TypeSpec.__init__(self)
        # no base - no restrictions allowed
        self.target_node = target_node

    def str_to_val(self, errors, pos, str):
        return self.target_node.type.i_type_spec.str_to_val(errors, pos, str)

    def validate(self, errors, pos, val, errstr = ''):
        return self.target_node.type.i_type_spec.validate(errors, pos, str)

class UnionTypeSpec(TypeSpec):
    def __init__(self, types):
        TypeSpec.__init__(self)
        # no base - no restrictions allowed
        self.types = types

    def str_to_val(self, errors, pos, str):
        return str

    def validate(self, errors, pos, str, errstr = ''):
        # try to validate against each membertype
        for t in self.types:
            t.validate(errors)
            if t.i_type_spec != None:
                val = t.i_type_spec.str_to_val([], pos, str)
                if val != None:
                    if t.i_type_spec.validate([], pos, val):
                        return True;
        err_add(errors, pos, 'TYPE_VALUE',
                (str, self.definition, 'no member type macthed' + errstr))
        return False

yang_type_specs = \
  {'int8':IntTypeSpec(-128, 127),
   'int16':IntTypeSpec(-32768, 32767),
   'int32':IntTypeSpec(-2147483648, 2147483647),
   'int64':IntTypeSpec(-9223372036854775808, 9223372036854775807),
   'uint8':IntTypeSpec(0, 255),
   'uint16':IntTypeSpec(0, 65535),
   'uint32':IntTypeSpec(0, 4294967295),
   'uint64':IntTypeSpec(0, 18446744073709551615),
   'float32':FloatTypeSpec(32),
   'float64':FloatTypeSpec(64),
   'string':StringTypeSpec(),
   'boolean':BooleanTypeSpec(),
   'enumeration':TypeSpec(),
   'bits':TypeSpec(),
   'binary':BinaryTypeSpec(),
   'keyref':TypeSpec(),
   'instance-identifier':TypeSpec(),
   'empty':EmptyTypeSpec(),
   'union':TypeSpec(),
   }


### YANG grammar

    # keyword             argument-name  yin-element xsd-appinfo
yang_keywords = \
    {'anyxml':           ('name',        False,      False),
     'argument':         ('name',        False,      False),
     'augment':          ('target-node', False,      False),
     'belongs-to':       ('module',      False,      True),
     'bit':              ('name',        False,      False),
     'case':             ('name',        False,      False),
     'choice':           ('name',        False,      False),
     'config':           ('value',       False,      True),
     'contact':          ('info',        True,       True),
     'container':        ('name',        False,      False),
     'default':          ('value',       False,      True),
     'description':      ('text',        True,       False),
     'enum':             ('name',        False,      False),
     'error-app-tag':    ('value',       False,      True),
     'error-message':    ('value',       True,       True),
     'extension':        ('name',        False,      False),
     'grouping':         ('name',        False,      False),
     'import':           ('module',      False,      True),
     'include':          ('module',      False,      True),
     'input':            (None,          None,       False),
     'key':              ('value',       False,      False),
     'leaf':             ('name',        False,      False),
     'leaf-list':        ('name',        False,      False),
     'length':           ('value',       False,      False),
     'list':             ('name',        False,      False),
     'mandatory':        ('value',       False,      True),
     'max-elements':     ('value',       False,      True),
     'min-elements':     ('value',       False,      True),
     'module':           ('name',        False,      False),
     'must':             ('condition',   False,      True),
     'namespace':        ('uri',         False,      False),
     'notification':     ('name',        False,      False),
     'ordered-by':       ('value',       False,      True),
     'organization':     ('info',        True,       True),
     'output':           (None,          None,       False),
     'path':             ('value',       False,      False),
     'pattern':          ('value',       False,      False),
     'position':         ('value',       False,      False),
     'presence':         ('value',       False,      False),
     'prefix':           ('value',       False,      True),
     'range':            ('value',       False,      False),
     'reference':        ('info',        False,      True),
     'revision':         ('date',        False,      True),
     'rpc':              ('name',        False,      False),
     'status':           ('value',       False,      True),
     'submodule':        ('name',        False,      False),
     'type':             ('name',        False,      False),
     'typedef':          ('name',        False,      False),
     'unique':           ('value',       False,      False),
     'units':            ('name',        False,      True),
     'uses':             ('name',        False,      False),
     'value':            ('value',       False,      False),
     'when':             ('condition',   False,      True),
     'yang-version':     ('value',       False,      True),
     'yin-element':      ('value',       False,      False),
     }

### utility functions

def is_base_type(typename):
    return typename in yang_type_specs

def validate_status(errors, x, y, defn, ref):
    xstatus = x.status
    if xstatus == None:
        xstatus = 'current'
    ystatus = y.status
    if ystatus == None:
        ystatus = 'current'
    if xstatus == 'current' and ystatus == 'deprecated':
        err_add(x.pos, 'CURRENT_USES_DEPRECATED', (defn, ref))
    elif xstatus == 'current' and ystatus == 'obsolete':
        err_add(x.pos, 'CURRENT_USES_OBSOLETE', (defn, ref))
    elif xstatus == 'deprecated' and ystatus == 'obsolete':
        err_add(x.pos, 'DEPRECATED_USES_OBSOLETE', (defn, ref))

def validate_identifier(str, pos, errors):
    if re_identifier.search(str) == None:
        err_add(errors, pos, 'SYNTAX_ERROR', 'bad identifier "' + str + '"')

def search_file(filename, search_path):
   """Given a search path, find file
   """
   paths = string.split(search_path, os.pathsep)
   for path in paths:
       fname = os.path.join(path, filename)
       if fname.startswith("./"):
           fname = fname[2:]
       if os.path.exists(fname):
           return fname
   return None

debug = False
def dbg(str):
    if debug:
        print "** %s" % str

plugins = []

def register_plugin(plugin):
    """Call this to register a pyang plugin. See class PyangPlugin
    for more info.
    """
    plugins.append(plugin)

def run():
    usage = """%prog [options] <filename>...

Validates the YANG module in <filename>, and all its dependencies."""

    # search for plugins in std directory
    plugindirs = []
    basedir = os.path.split(sys.modules['pyang'].__file__)[0]
    plugindirs.append(basedir + "/plugins")
    # check for --plugindir
    idx = 1
    while '--plugindir' in sys.argv[idx:]:
        idx = idx + sys.argv[idx:].index('--plugindir')
        plugindirs.append(sys.argv[idx+1])
        idx = idx + 1
    
    syspath = sys.path
    for plugindir in plugindirs:
        sys.path = [plugindir] + syspath
        fnames = os.listdir(plugindir)
        for fname in fnames:
            if fname.endswith(".py") and fname != '__init__.py':
                pluginmod = __import__(fname[:-3])
                try:
                    pluginmod.pyang_plugin_init()
                except AttributeError, s:
                    print pluginmod.__dict__
                    raise AttributeError, pluginmod.__file__ + ': ' + str(s)
        sys.path = syspath

    fmts = {}
    for p in plugins:
        p.add_output_format(fmts)

    optlist = [
        # use capitalized versions of std options help and version
        optparse.make_option("-h", "--help",
                             action="help",
                             help="Show this help message and exit"),
        optparse.make_option("-v", "--version",
                             action="version",
                             help="Show version number and exit"),
        optparse.make_option("-e", "--list-errors",
                             dest="list_errors",
                             action="store_true",
                             help="Print a listing of all error codes " \
                             "and exit."),
        optparse.make_option("--print-error-code",
                             dest="print_error_code",
                             action="store_true",
                             help="On errors, print the error code instead " \
                             "of the error message."),
        optparse.make_option("-l", "--level",
                             dest="level",
                             default=3,
                             type="int",
                             help="Report errors and warnings up to LEVEL. " \
                             "If any error or warnings are printed, the " \
                             "program exits with exit code 1, otherwise " \
                             "with exit code 0. The default error level " \
                             "is 3."),
        optparse.make_option("--canonical",
                             dest="canonical",
                             action="store_true",
                             help="Validate the module(s) according the " \
                             "canonical YANG order."),
        optparse.make_option("-f", "--format",
                             dest="format",
                             help="Convert to FORMAT.  Supported formats " \
                             "are " +  ', '.join(fmts.keys())),
        optparse.make_option("-o", "--output",
                             dest="outfile",
                             help="Write the output to OUTFILE instead " \
                             "of stdout."),
        optparse.make_option("-p", "--path", dest="path", default="",
                             help="Search path for yin and yang modules"),
        optparse.make_option("--plugindir",
                             dest="plugindir",
                             help="Loads pyang plugins from PLUGINDIR"),
        optparse.make_option("-d", "--debug",
                             dest="debug",
                             action="store_true",
                             help="Turn on debugging of the pyang code"),
        ]
        
    optparser = optparse.OptionParser(usage, add_help_option = False)
    optparser.version = '%prog ' + pyang_version
    optparser.add_options(optlist)

    for p in plugins:
        p.add_opts(optparser)

    (o, args) = optparser.parse_args()

    if o.list_errors == True:
        for tag in error_codes:
            (level, fmt) = error_codes[tag]
            print "Error:   %s - level %d" % (tag, level)
            print "Message: %s" % fmt
            print ""
        sys.exit(0)

    if o.outfile != None and o.format == None:
        print >> sys.stderr, "no format specified"
        sys.exit(1)
    if o.format != None and len(args) > 1:
        print >> sys.stderr, "too many files to convert"
        sys.exit(1)
    if len(args) == 0:
        print >> sys.stderr, "no file given"
        sys.exit(1)

    filenames = args

    global debug
    debug = o.debug

    ctx = Context()
    ctx.path = o.path + ':' + basedir + '/../modules' + ':.'
    ctx.canonical = o.canonical
    ctx.opts = o
    # temporary hack. needed for yin plugin
    ctx.filename = args[0]
    
    if o.format != None:
        emit_obj = fmts[o.format]
    else:
        emit_obj = None

    if emit_obj != None:
        emit_obj.setup_ctx(ctx)

    for filename in filenames:
        modulename = ctx.add_module(filename)
    ctx.validate()
    exit_code = 0
    for (epos, etag, eargs) in ctx.errors:
        elevel = err_level(etag)
        if elevel <= o.level:
            if o.print_error_code == True:
                print >> sys.stderr, \
                      str(epos) + ': [%d] %s' % (elevel, etag)
            else:
                print >> sys.stderr, \
                      str(epos) + ': [%d] ' % elevel + err_to_str(etag, eargs)
            exit_code = 1
    if o.outfile == None:
        writef = lambda str: sys.stdout.write(str)
    else:
        fd = open(o.outfile, "w+")
        writef = lambda str: fd.write(str)
    if emit_obj != None:
        module = ctx.modules[modulename]
        emit_obj.emit(ctx, module, writef)

    sys.exit(exit_code)
