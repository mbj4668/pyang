import re
import copy
import time
import libxml2

from debug import dbg
import util
from util import attrsearch, keysearch
from error import err_add
import types

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

### Exceptions

class NotFound(Exception):
    """used when a referenced item is not found"""
    pass


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
        if not is_submodule: keywd = 'module'
        else: keywd = 'submodule'
        Statement.__init__(self, None, pos, keywd, self, name)
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

    def set_import(self, import_):
        # check for circular import
        if import_.modulename not in self.ctx.modules:
            # FIXME: do a correct circular check in validate
            #       err_add(self.ctx.errors, parser.pos,
            #            'CIRCULAR_DEPENDENCY', ('module', import_.modulename))

            # parse and load the imported module
            self.ctx.search_module(import_.pos, modulename = import_.modulename)

        prefix = import_.prefix.arg
        # check if the prefix is already used by someone else
        if prefix in self.i_prefixes:
            err_add(self.ctx.errors, import_.pos,
                    'PREFIX_ALREADY_USED', (prefix, self.i_prefixes[prefix]))
        else:
            # add the prefix->modulename mapping to this module
            self.i_prefixes[prefix] = import_.modulename

    def set_include(self, include):
        # parse and load the included module
        self.ctx.search_module(include.pos, modulename = include.modulename)

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
            except KeyError:
                err_add(errors, pos, 'PREFIX_NOT_DEFINED', prefix)
                return None
            # even if the prefix is defined, the module might not be
            # loaded; the load might have failed
            try:
                module = self.ctx.modules[modulename]
            except KeyError:
                return None
            return module

    def validate(self):
        errors = self.ctx.errors

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
        if self.i_validated == False:
            err_add(errors, self.pos,
                    'CIRCULAR_DEPENDENCY', ('type', self.name) )
            return
        self.i_validated = False
        dbg("validating typedef %s" % self.name)
        if types.is_base_type(self.name):
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
    
class Argument(Statement):
    def __init__(self, parent, pos, module, arg):
        Statement.__init__(self, parent, pos, self.__class__.__name__.lower(),
                      module, arg)
        # argument
        self.name = arg
        # statements
        self.yin_element = None

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
                    self.i_type_spec = types.yang_type_specs[name]
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
                self.i_type_spec = types.EnumerationTypeSpec(self.enum)

        # check the bits - only applicable when the type is the builtin
        # bits type
        if self.bit != [] and self.name != 'bits':
            err_add(errors, self.bit[0].pos, 'BAD_RESTRICTION', 'bit')
        elif self.name == 'bits':
            self.i_is_derived = True
            if self.bits_validate(errors):
                self.i_type_spec = types.BitsTypeSpec(self.bit)

        # check the union types
        if self.type != [] and self.name != 'union':
            err_add(errors, self.pattern.pos, 'BAD_RESTRICTION', 'union')
        elif self.name == 'union':
            self.i_is_derived = True
            if self.union_validate(errors):
                self.i_type_spec = types.UnionTypeSpec(self.type)

    def enums_validate(self, errors):
        if self.enum == []:
            err_add(errors, self.pos, 'MISSING_TYPE_SPEC',
                    ('enumeration', 'enum'))
            return False
        # make sure all values given are unique
        values = []
        for e in self.enum:
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
        return types.RangeTypeSpec(base_type_spec, self.i_ranges)

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
        return types.LengthTypeSpec(base_type_spec, self.i_lengths)

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
        return types.PatternTypeSpec(base_type_spec, self.i_re)

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
        return types.PathTypeSpec(self.i_target_node)

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
        if util.is_prefixed(identifier):
            (prefix, name) = identifier
            module = path.i_module.prefix_to_module(prefix, path.pos, errors)
            if module == None:
                raise NotFound
            return (module, name)
        else: # local identifier
            return (path.i_module, identifier)

    def is_identifier(x):
        if util.is_local(x):
            return True
        if util.is_prefixed(x):
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
            if c.keyword not in ['case', 'input', 'output']:
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
        if self.input != None:
            self.children.append(self.input)
        if self.output != None:
            self.children.append(self.output)
        validate_children(self, self.children, errors)

class Input(SchemaNodeStatement):
    def __init__(self, parent, pos, module, arg):
        SchemaNodeStatement.__init__(self, parent, pos,
                                     self.__class__.__name__.lower(),
                                     module, arg)
        # statements
        self.children = []  # leaves, containers, lists, leaf-lists, uses
        self.typedef = []
        self.grouping = []
        self.augment = []
        
    def validate(self, errors):
        validate_children(self, self.children, errors)

class Output(SchemaNodeStatement):
    def __init__(self, parent, pos, module, arg):
        SchemaNodeStatement.__init__(self, parent, pos,
                                     self.__class__.__name__.lower(),
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


def keyword_to_str(keyword):
    if util.is_prefixed(keyword):
        (prefix, keyword) = keyword
        return prefix + ":" + keyword
    else:
        return keyword

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
