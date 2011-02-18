"""YANG built-in types"""

from error import err_add
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
    
class Decimal64Value(object):
    def __init__(self, value, s=None):
        self.value = value
        self.s = s
        if s == None:
            self.s = str(value)
    def __str__(self):
        return self.s

    def __cmp__(self, other):
        if not isinstance(other, Decimal64Value):
            return -1
        return cmp(self.value, other.value)

    def __eq__(self, other):
        if not isinstance(other, Decimal64Value):
            return False
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        if not isinstance(other, Decimal64Value):
            return True
        return self.__cmp__(other) != 0

class Decimal64TypeSpec(TypeSpec):
    def __init__(self, fraction_digits):
        TypeSpec.__init__(self)
        self.fraction_digits = int(fraction_digits.arg)
        self.min = Decimal64Value(-9223372036854775808)
        self.max = Decimal64Value(9223372036854775807)

    def str_to_val(self, errors, pos, s0):
        if s0 in ('min', 'max'):
            return s0
        # make sure it is syntactically correct
        if syntax.re_decimal.search(s0) is None:
            err_add(errors, pos, 'TYPE_VALUE',
                    (s0, self.definition, 'not a decimal'))
            return None
        if s0[0] == '-':
            is_negative = True
            s = s0[1:]
        else:
            is_negative = False
            s = s0
        p = s.find('.')
        if p == -1:
            v = int(s)
            i = self.fraction_digits
            while i > 0:
                v = v * 10
                i -= 1
        else:
            v = int(s[:p])
            i = self.fraction_digits
            j = p + 1
#            slen = len(s.rstrip('0')) # ignore trailing zeroes
# No, do not ignore trailing zeroes!
            slen = len(s)
            while i > 0:
                v *= 10
                i -= 1
                if j < slen:
                    v += int(s[j])
                j += 1
            if j < slen:
                err_add(errors, pos, 'TYPE_VALUE',
                        (s, self.definition, 'too many fraction digits'))
                return None
        if is_negative:
            v = -v
        return Decimal64Value(v, s0)

    def validate(self, errors, pos, val, errstr = ''):
        if val < self.min or val > self.max:
            err_add(errors, pos, 'TYPE_VALUE',
                    (str(val), self.definition, 'range error' + errstr))
            return False
        else:
            return True
    
    def restrictions(self):
        return ['range']
    
class BooleanTypeSpec(TypeSpec):
    def __init__(self):
        TypeSpec.__init__(self)

    def str_to_val(self, errors, pos, str):
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

class IdentityrefTypeSpec(TypeSpec):
    def __init__(self, base):
        TypeSpec.__init__(self)
        self.base = base

    def str_to_val(self, errors, pos, s):
        if s.find(":") == -1:
            prefix = None
            name = s
        else:
            [prefix, name] = s.split(':', 1)
        if prefix is None or self.base.i_module.i_prefix == prefix:
            # check local identities
            pmodule = self.base.i_module
        else:
            # this is a prefixed name, check the imported modules
            pmodule = statements.prefix_to_module(self.base.i_module, prefix,
                                                  pos, errors)
            if pmodule is None:
                return None
        if name not in pmodule.i_identities:
            err_add(errors, pos, 'TYPE_VALUE',
                    (s, self.definition, 'identityref not found'))
            return None
        val = pmodule.i_identities[name]
        my_identity = self.base.i_identity
        vals = []
        while True:
            if val == my_identity:
                return pmodule.i_identities[name]
            else:
                p = val.search_one('base')
                if p is None or p.i_identity is None:
                    err_add(errors, pos, 'TYPE_VALUE',
                            (s, self.definition,
                             'identityref not derived from %s' % \
                             my_identity.arg))
                    return None
                else:
                    val = p.i_identity
                    if val in vals:
                        # circular; has been reported already
                        return
                    vals.append(val)


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
            err_add(errors, stmt.pos, 'TYPE_VALUE',
                    (lostr, '', 'not an integer'))
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
            err_add(errors, stmt.pos, 'TYPE_VALUE',
                    (histr, '', 'not an integer'))
            return None
        return (lo, hi)
    lengths = [f(m[1], m[3]) for m in syntax.re_length_part.findall(stmt.arg)]
    # make sure the length values are of correct type and increasing
    cur_lo = None
    for (lo, hi) in lengths:
        # check that cur_lo < lo < hi
        if not is_smaller(cur_lo, lo):
            err_add(errors, stmt.pos, 'LENGTH_BOUNDS', (str(lo), cur_lo))
            return None
        if not is_smaller(lo, hi):
            err_add(errors, stmt.pos, 'LENGTH_BOUNDS', (str(hi), str(lo)))
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
            err_add(errors, stmt.pos, 'LENGTH_VALUE', str(cur_lo))
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
        try:
            re = libxml2.regexpCompile(stmt.arg)
            return (re, stmt.pos)
        except libxml2.treeError, v:
            err_add(errors, stmt.pos, 'PATTERN_ERROR', str(v))
            return None
    except ImportError:
## Do not report a warning in this case.  Maybe we should add some
## flag to turn on this warning...
#        err_add(errors, stmt.pos, 'PATTERN_FAILURE',
#                "Could not import python module libxml2 "
#                    "(see http://xmlsoft.org for installation help)")
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
    # make sure all names and values given are unique
    names = {}
    values = {}
    next = 0
    for e in enums:
        value = e.search_one('value')
        if value is not None:
            try:
                x = int(value.arg)
                e.i_value = x
                if x < -2147483648 or x > 2147483647:
                    raise ValueError
                if x >= next:
                    next = x + 1
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
            if next > 2147483647:
                err_add(errors, e.pos, 'ENUM_VALUE', str(next))
            e.i_value = next
            next = next + 1
        if e.arg in names:
            err_add(errors, e.pos, 'DUPLICATE_ENUM_NAME', (e.arg, names[e.arg]))
        else:
            names[e.arg] = e.pos

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
    # make sure all names and positions given are unique
    names = {}
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
        if b.arg in names:
            err_add(errors, b.pos, 'DUPLICATE_BIT_NAME', (b.arg, names[b.arg]))
        else:
            names[b.arg] = b.pos

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

    # FIXME: rewrite using the new xpath tokenizer

    # PRE: s matches syntax.path_arg
    # -type dn [identifier | ('predicate', identifier, up::int(), [identifier])]
    # Ret: (up::int(),
    #       dn::dn(),
    #       derefup::int(),
    #       derefdn::dn())
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
                elif s[i].isspace():
                    i = i + 1
                else:
                    # s points to an identifier
                    break
            return (up, s[i:])

        def skip_space(s):
            if len(s) == 0:
                return s
            i = 0
            while s[i].isspace():
                i = i + 1
            return s[i:]
    
        def parse_identifier(s, is_absolute):
            m = syntax.re_keyword_start.match(s)
            if m is None:
                raise Abort
            s = s[m.end():]
            if m.group(2) is None:
                # no prefix
                return (m.group(3), s)
            elif m.group(2) == path.i_module.i_prefix and is_absolute == False:
                # reference to local module in a relative keypath -
                # remove the prefix.  this makes it easier to handle
                # leafrefs in groupings.  local identifiers in relative keypaths
                # in groupings are resolved to point:
                #   (i) within the grouping only (checked by
                #       statements.validate_leafref_path()) and
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
            if s[:7] == 'current':
                s = s[7:] # skip 'current'
                s = skip_space(s)
                s = s[1:] # skip '('
                s = skip_space(s)
                s = s[1:] # skip ')'
                s = skip_space(s)
                s = s[1:] # skip '/'
                s = skip_space(s)
                (up, s) = parse_dot_dot(s)
                s = skip_space(s)
            else:
                up = -1
                b = s.find(']') + 1
                s = s[b:]
                if len(s) > 0 and s[0] == '/':
                    s = s[1:] # skip '/'
            dn = []
            while len(s) > 0:
                (xidentifier, s) = parse_identifier(s, is_absolute)
                dn.append(xidentifier)
                s = skip_space(s)
                if len(s) == 0:
                    break
                if s[0] == '/':
                    s = s[1:] # skip '/'
                elif s[0] == ']':
                    s = s[1:] # skip ']'
                    break
            return (('predicate', identifier, up, dn), s)

        def parse_descendant(s, is_absolute):
            dn = []
            # all '..'s are now parsed
            while len(s) > 0 and (not s[0].isspace()) and s[0] != ')':
                (identifier, s) = parse_identifier(s, is_absolute)
                dn.append(identifier)
                s = skip_space(s)
                if len(s) == 0:
                    break
                while len(s) > 0 and s[0] == '[':
                    (pred, s) = parse_key_predicate(s, is_absolute)
                    dn.append(pred)
                    s = skip_space(s)
                if len(s) > 0 and s[0] == '/':
                    s = s[1:] # skip '/'

            return (dn, s)

        derefup = 0
        derefdn = None
        if s.startswith('deref'):
            s = s[5:] # skip 'deref'
            s = skip_space(s)
            s = s[1:] # skip '('
            s = skip_space(s)
            (derefup, s) = parse_dot_dot(s)
            (derefdn, s) = parse_descendant(s, is_absolute=False)
            s = skip_space(s)
            s = s[1:] # skip ')'
            s = skip_space(s)
            s = s[1:] # skip '/'

        (up, s) = parse_dot_dot(s)
        is_absolute = up == -1
        (dn, s) = parse_descendant(s, is_absolute)
        return (up, dn, derefup, derefdn)

    try:
        return parse_keypath(path.arg)
    except Abort:
        return None

class PathTypeSpec(TypeSpec):
    def __init__(self, path_spec, path, pos):
        TypeSpec.__init__(self)
        # no base - no restrictions allowed
        self.path_spec = path_spec
        self.path_ = path
        self.pos = pos


    def str_to_val(self, errors, pos, str):
        if hasattr(self, 'i_target_node'):
            return self.i_target_node.type.i_type_spec.str_to_val(errors, pos,
                                                                  str)
        else:
            # if a default value is verified
            return str

    def validate(self, errors, pos, val, errstr = ''):
        if hasattr(self, 'i_target_node'):
            return self.i_target_node.type.i_type_spec.validate(errors, pos, str)
        else:
            # if a default value is verified
            return True

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
   'decimal64':TypeSpec(),
   'string':StringTypeSpec(),
   'boolean':BooleanTypeSpec(),
   'enumeration':TypeSpec(),
   'bits':TypeSpec(),
   'binary':BinaryTypeSpec(),
   'leafref':TypeSpec(),
   'identityref':TypeSpec(),
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

