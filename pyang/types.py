"""YANG built-in types"""

from error import err_add
from debug import dbg
import util
import syntax
import statements

class Abort(Exception):
    pass

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

def validate_range_expr(errors, stmt, type_):
    # break the expression apart
    def f(lostr, histr):
        if histr == '':
            # this means that a single number was in the range, e.g.
            # "4 | 5..6".
            return (type_.i_type_spec.str_to_val(errors, stmt.pos, lostr),
                    None)
        return (type_.i_type_spec.str_to_val(errors, stmt.pos, lostr),
                type_.i_type_spec.str_to_val(errors, stmt.pos, histr))
    ranges = [f(m[1], m[6]) for m in syntax.re_range_part.findall(stmt.arg)]
    # make sure the range values are of correct type and increasing
    pos = stmt.pos
    cur_lo = None
    for (lo, hi) in ranges:
        if lo != 'min' and lo != 'max':
            type_.i_type_spec.validate(errors, pos, lo)
        if hi != 'min' and hi != 'max' and hi != None:
            type_.i_type_spec.validate(errors, pos, hi)
        # check that cur_lo < lo < hi
        if not is_smaller(cur_lo, lo):
            err_add(errors, pos, 'RANGE_BOUNDS', (str(lo), cur_lo))
            return None
        if not is_smaller(lo, hi):
            err_add(errors, pos, 'RANGE_BOUNDS', (str(hi), str(lo)))
            return None
        if hi == None:
            cur_lo = lo
        else:
            cur_lo = hi
    return (ranges, stmt.pos)

class RangeTypeSpec(TypeSpec):
    def __init__(self, base, range_spec):
        TypeSpec.__init__(self)
        self.base = base
        (ranges, ranges_pos) = range_spec
        self.ranges = ranges
        self.ranges_pos = ranges_pos

    def str_to_val(self, errors, pos, str):
        return self.base.str_to_val(errors, pos, str)

    def validate(self, errors, pos, val, errstr=''):
            if self.base.validate(errors, pos, val, errstr) == False:
                return False
            for (lo, hi) in self.ranges:
                if ((lo == 'min' or val >= lo) and
                    ((hi == None and val == lo) or hi == 'max' or val <= hi)):
                    return True
            err_add(errors, pos, 'TYPE_VALUE',
                    (str(val), self.definition, 'range error' + errstr +
                     ' for range defined at ' + str(self.ranges_pos)))
            return False

    def restrictions(self):
        return self.base.restrictions()

def validate_length_expr(errors, stmt):
    def f(lostr, histr):
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
    lengths = [f(m[1], m[3]) for m in syntax.re_length_part.findall(stmt.arg)]
    # make sure the length values are of correct type and increasing
    cur_lo = None
    for (lo, hi) in lengths:
        # check that cur_lo < lo < hi
        if not is_smaller(cur_lo, lo):
            err_add(errors, pos, 'LENGTH_BOUNDS', (str(lo), cur_lo))
            return None
        if not is_smaller(lo, hi):
            err_add(errors, pos, 'length_bounds', (str(hi), str(lo)))
            return None
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
            return None
    return (lengths, stmt.pos)

class LengthTypeSpec(TypeSpec):
    def __init__(self, base, length_spec):
        TypeSpec.__init__(self)
        self.base = base
        (lengths, length_pos) = length_spec
        self.lengths = lengths
        self.length_pos = length_pos

    def str_to_val(self, errors, pos, str):
        return self.base.str_to_val(errors, pos, str)

    def validate(self, errors, pos, val, errstr=''):
        if self.base.validate(errors, pos, val, errstr) == False:
            return False
        vallen = len(val)
        for (lo, hi) in self.lengths:
            if ((lo == 'min' or vallen >= lo) and
                ((hi == None and vallen == lo) or hi == 'max' or vallen <= hi)):
                return True
        err_add(errors, pos, 'TYPE_VALUE',
                (val, self.definition, 'length error' + errstr + 
                 ' for length defined at ' + str(self.length_pos)))
        return False

    def restrictions(self):
        return self.base.restrictions()


def validate_pattern_expr(errors, stmt):
    # check that it's syntactically correct
    try:
        import libxml2
        re = libxml2.regexpCompile(stmt.arg)
        return (re, stmt.pos)
    except libxml2.treeError, v:
        err_add(errors, stmt.pos, 'PATTERN_ERROR', str(v))
        return None
    except ImportError:
        err_add(errors, stmt.pos, 'PATTERN_FAILURE',
                "Could not import python module libxml2 "
                    "(see http://xmlsoft.org)")
        return None

class PatternTypeSpec(TypeSpec):
    def __init__(self, base, pattern_specs):
        TypeSpec.__init__(self)
        self.base = base
        self.res = pattern_specs

    def str_to_val(self, errors, pos, str):
        return self.base.str_to_val(errors, pos, str)

    def validate(self, errors, pos, val, errstr=''):
        if self.base.validate(errors, pos, val, errstr) == False:
            return False
        for (re, re_pos) in self.res:
            if re.regexpExec(val) != 1:
                err_add(errors, pos, 'TYPE_VALUE',
                        (val, self.definition, 'pattern mismatch' + errstr +
                         ' for pattern defined at ' + str(re_pos)))
                return False
        return True
    
    def restrictions(self):
        return self.base.restrictions()

def validate_enums(errors, enums, stmt):
    if enums == []:
        err_add(errors, stmt.pos, 'MISSING_TYPE_SPEC',
                ('enumeration', 'enum'))
        return None
    # make sure all values given are unique
    values = {}
    next = 0
    for e in enums:
        value = e.search_one('value')
        if value is not None:
            try:
                x = int(value.arg)
                if x < -2147483648 or x > 2147483647:
                    raise ValueError
                if x >= next:
                    next = x + 1
                e.i_value = x
                if x in values:
                    err_add(errors, value.pos, 'DUPLICATE_ENUM_VALUE', 
                            (x, values[x]))
                else:
                    values[x] = value.pos
            except ValueError:
                err_add(errors, value.pos, 'ENUM_VALUE', value.arg)
        else:
            # auto-assign a value
            values[next] = e.pos
            e.i_value = next
            next = next + 1
    # check status (here??)
    return enums

class EnumerationTypeSpec(TypeSpec):
    def __init__(self, enums):
        TypeSpec.__init__(self)
        # no base - no restrictions allowed
        self.enums = [(e.arg, e.i_value) for e in enums]

    def validate(self, errors, pos, val, errstr = ''):
        if util.keysearch(val, 0, self.enums) == None:
            err_add(errors, pos, 'TYPE_VALUE',
                    (val, self.definition, 'enum not defined' + errstr))
            return False
        else:
            return True

def validate_bits(errors, bits, stmt):
    if bits == []:
        err_add(errors, stmt.pos, 'MISSING_TYPE_SPEC',
                ('bits', 'bit'))
        return None
    # make sure all positions given are unique
    values = {}
    next = 0
    for b in bits:
        position = b.search_one('position')
        if position is not None:
            try:
                x = int(position.arg)
                if x < 0:
                    raise ValueError
                if x >= next:
                    next = x + 1
                b.i_position = x
                if x in values:
                    err_add(errors, position.pos, 'DUPLICATE_BIT_POSITION',
                            (x, values[x]))
                else:
                    values[x] = position.pos
            except ValueError:
                err_add(errors, position.pos, 'BIT_POSITION', position.arg)
        else:
            # auto-assign a value
            values[next] = b.pos
            b.i_position = next
            next = next + 1
    # check status (here??)
    return bits

class BitsTypeSpec(TypeSpec):
    def __init__(self, bits):
        TypeSpec.__init__(self)
        # no base - no restrictions allowed
        self.bits = [(b.arg, b.i_position) for b in bits]

    def str_to_val(self, errors, pos, str):
        return str.split()

    def validate(self, errors, pos, val, errstr = ''):
        for v in val:
            if util.keysearch(v, 0, self.bits) == None:
                err_add(errors, pos, 'TYPE_VALUE',
                        (v, self.definition, 'bit not defined' + errstr))
                return False
        return True

def validate_path_expr(errors, path):

    # PRE: s matches syntax.path_arg
    # Ret: (up::int(), [identifier | [(identifier, up::int(), [identifier])]])
    def parse_keypath(s):

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
    
        def parse_identifier(s, is_absolute):
            m = syntax.re_keyword_start.match(s)
            s = s[m.end():]
            if m.group(2) is None:
                # no prefix
                return (m.group(3), s)
            elif m.group(2) == path.i_module.i_prefix and is_absolute == False:
                # reference to local module in a relative keypath -
                # remove the prefix.  this makes it easier to handle
                # keyrefs in groupings.  local identifiers in relative keypaths
                # in groupings are resolved to point:
                #   (i) within the grouping only (checked by
                #       statements.validate_keyref_path()) and
                #  (ii) to elements where the grouping is used.  this is
                #       easier to handle if the prefix is removed here.
                return (m.group(3), s)
            else:
                return ((m.group(2), m.group(3)), s)

                prefix = m.group(2)
                mod = statements.prefix_to_module(path.i_module, prefix,
                                                  path.pos, errors)
                if mod is not None:
                    return ((mod, m.group(3)), s)
                else:
                    raise Abort

        def parse_key_predicate(s, is_absolute):
            s = s[1:] # skip '['
            s = skip_space(s)
            (identifier, s) = parse_identifier(s, is_absolute)
            s = skip_space(s)
            s = s[1:] # skip '='
            s = skip_space(s)
            s = s[10:] # skip 'current()/'
            (up, s) = parse_dot_dot(s)
            s = skip_space(s)
            dn = []
            while True:
                (xidentifier, s) = parse_identifier(s[i:], is_absolute)
                dn.append(xidentifier)
                if s[0] == '/':
                    s = s[1:] # skip '/'
                else:
                    s = skip_space(s)
                    s = s[1:] # skip ']'
                    break
            return (('predicate', identifier, up, dn), s)

        (up, s) = parse_dot_dot(s)
        is_absolute = up == -1
        dn = []
        i = 0
        # all '..'s are now parsed
        while len(s) > 0:
            (identifier, s) = parse_identifier(s[i:], is_absolute)
            dn.append(identifier)
            if len(s) == 0:
                break
            while len(s) > 0 and s[0] == '[':
                (pred, s) = parse_key_predicate(s, is_absolute)
                dn.append(pred)
            if len(s) > 0:
                s = s[1:] # skip '/'
        return (up, dn)

    try:
        return parse_keypath(path.arg)
    except Abort:
        return None

class PathTypeSpec(TypeSpec):
    def __init__(self, path, pos):
        TypeSpec.__init__(self)
        # no base - no restrictions allowed
        self.path = path
        self.pos = pos

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
            if t.i_type_spec != None:
                val = t.i_type_spec.str_to_val([], pos, str)
                if val != None:
                    if t.i_type_spec.validate([], pos, val):
                        return True;
        err_add(errors, pos, 'TYPE_VALUE',
                (str, self.definition, 'no member type matched' + errstr))
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

def is_base_type(typename):
    return typename in yang_type_specs

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

