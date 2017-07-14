"""YANG built-in types"""

from .error import err_add
from . import util
from . import syntax
import base64
from xml.sax.saxutils import quoteattr
from xml.sax.saxutils import escape

try:
    # python 2
    from StringIO import StringIO
except ImportError:
    # python 3
    from io import StringIO

class Abort(Exception):
    pass

class TypeSpec(object):
    def __init__(self, name):
        self.definition = ""
        self.name = name
        self.base = None

    def str_to_val(self, errors, pos, str):
        return str;

    def validate(self, errors, pos, val, errstr=''):
        return True;

    def restrictions(self):
        return []

class IntTypeSpec(TypeSpec):
    def __init__(self, name, min, max):
        TypeSpec.__init__(self, name)
        self.min = min
        self.max = max

    def str_to_val(self, errors, pos, s):
        try:
            if s in ['min', 'max']:
                return s
            if syntax.re_integer.search(s) is None:
                raise ValueError
            return int(s, 0)
        except ValueError:
            err_add(errors, pos, 'TYPE_VALUE',
                    (s, self.definition, 'not an integer'))
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
    def __init__(self, value, s=None, fd=None):
        # must set s (string repr) OR fd (fraction-digits)
        self.value = value
        self.s = s
        if s == None and fd is not None:
            s = str(value)
            self.s = s[:-fd] + "." + s[-fd:]

    def __str__(self):
        return self.s

    def __cmp__(self, other):
        if not isinstance(other, Decimal64Value):
            return -1
        if self.value < other.value:
            return -1;
        elif self.value == other.value:
            return 0;
        else:
            return 1

    def __eq__(self, other):
        if not isinstance(other, Decimal64Value):
            return False
        return self.value == other.value

    def __ne__(self, other):
        if not isinstance(other, Decimal64Value):
            return True
        return self.value != other.value

    def __lt__(self, other):
        if not isinstance(other, Decimal64Value):
            return True
        return self.value < other.value

    def __le__(self, other):
        if not isinstance(other, Decimal64Value):
            return True
        return self.value <= other.value

    def __gt__(self, other):
        if not isinstance(other, Decimal64Value):
            return False
        return self.value > other.value

    def __ge__(self, other):
        if not isinstance(other, Decimal64Value):
            return False
        return self.value >= other.value


class Decimal64TypeSpec(TypeSpec):
    def __init__(self, fraction_digits):
        TypeSpec.__init__(self, 'decimal64')
        self.fraction_digits = int(fraction_digits.arg)
        self.min = Decimal64Value(-9223372036854775808, fd=self.fraction_digits)
        self.max = Decimal64Value(9223372036854775807, fd=self.fraction_digits)

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
        return Decimal64Value(v, s=s0)

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
        TypeSpec.__init__(self, 'boolean')

    def str_to_val(self, errors, pos, str):
        if str == 'true': return True;
        elif str == 'false': return False
        else:
            err_add(errors, pos, 'TYPE_VALUE',
                    (str, self.definition, 'not a boolean'))
            return None

class StringTypeSpec(TypeSpec):
    def __init__(self):
        TypeSpec.__init__(self, 'string')

    def restrictions(self):
        return ['pattern', 'length']

class BinaryTypeSpec(TypeSpec):
    def __init__(self):
        TypeSpec.__init__(self, 'binary')

    def str_to_val(self, errors, pos, s):
        try:
            return base64.b64decode(s)
        except:
            err_add(errors, pos, 'TYPE_VALUE',
                    (s, '', 'bad base64 value'))

    def restrictions(self):
        return ['length']

class EmptyTypeSpec(TypeSpec):
    def __init__(self):
        TypeSpec.__init__(self, 'empty')

    def str_to_val(self, errors, pos, str):
        err_add(errors, pos, 'BAD_DEFAULT_VALUE', 'empty')
        return None

class IdentityrefTypeSpec(TypeSpec):
    def __init__(self, idbases):
        TypeSpec.__init__(self, 'identityref')
        self.idbases = idbases

    def str_to_val(self, errors, pos, s):
        if s.find(":") == -1:
            prefix = None
            name = s
        else:
            [prefix, name] = s.split(':', 1)
        if prefix is None or self.idbases[0].i_module.i_prefix == prefix:
            # check local identities
            pmodule = self.idbases[0].i_module
        else:
            # this is a prefixed name, check the imported modules
            pmodule = util.prefix_to_module(self.idbases[0].i_module, prefix,
                                            pos, errors)
            if pmodule is None:
                return None
        if name not in pmodule.i_identities:
            err_add(errors, pos, 'TYPE_VALUE',
                    (s, self.definition, 'identityref not found'))
            return None
        val = pmodule.i_identities[name]
        for idbase in self.idbases:
            my_identity = idbase.i_identity
            if not is_derived_from(val, my_identity):
                err_add(errors, pos, 'TYPE_VALUE',
                        (s, self.definition,
                         'identityref not derived from %s' % \
                         my_identity.arg))
                return None
        else:
            return val

def is_derived_from(a, b):
    if a == b:
        # an identity is not derived from itself
        return False
    else:
        return is_derived_from_or_self(a, b, [])

def is_derived_from_or_self(a, b, visited):
    # return True if a is derived from b
    if a == b:
        return True
    for p in a.search('base'):
        val = p.i_identity
        if val not in visited:
            visited.append(val)
            if is_derived_from_or_self(val, b, visited):
                return True
    return False

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
    return validate_ranges(errors, stmt.pos, ranges, type_)

def validate_ranges(errors, pos, ranges, type_):
    # make sure the range values are of correct type and increasing
    cur_lo = None
    for (lo, hi) in ranges:
        if lo != 'min' and lo != 'max' and lo != None:
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
    return (ranges, pos)

class RangeTypeSpec(TypeSpec):
    def __init__(self, base, range_spec):
        TypeSpec.__init__(self, base.name)
        self.base = base
        (ranges, ranges_pos) = range_spec
        self.ranges = ranges
        self.ranges_pos = ranges_pos
        if ranges != []:
            self.min = ranges[0][0]
            if self.min == 'min':
                self.min = base.min
            self.max = ranges[-1][1]
            if self.max == None: # single range
                self.max = ranges[-1][0]
            if self.max == 'max':
                self.max = base.max
        else:
            self.min = base.min
            self.max = base.max
        if hasattr(base, 'fraction_digits'):
            self.fraction_digits = base.fraction_digits

    def str_to_val(self, errors, pos, str):
        return self.base.str_to_val(errors, pos, str)

    def validate(self, errors, pos, val, errstr=''):
        if self.base.validate(errors, pos, val, errstr) == False:
            return False
        for (lo, hi) in self.ranges:
            if ((lo == 'min' or lo == 'max' or val >= lo) and
                ((hi is None and val == lo) or hi == 'max' or \
                     (hi is not None and val <= hi))):
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
        TypeSpec.__init__(self, base.name)
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
                ((hi is None and vallen == lo) or hi == 'max' or
                 (hi is not None and vallen <= hi))):
                return True
        err_add(errors, pos, 'TYPE_VALUE',
                (val, self.definition, 'length error' + errstr +
                 ' for length defined at ' + str(self.length_pos)))
        return False

    def restrictions(self):
        return self.base.restrictions()


def _validate_pattern_libxml2(errors, stmt, invert_match):
    try:
        import libxml2
        try:
            re = libxml2.regexpCompile(stmt.arg)
            return ('libxml2', re, stmt.pos, invert_match)
        except libxml2.treeError as v:
            err_add(errors, stmt.pos, 'PATTERN_ERROR', str(v))
            return None
    except ImportError:
    ## Do not report a warning in this case.  Maybe we should add some
    ## flag to turn on this warning...
    #        err_add(errors, stmt.pos, 'PATTERN_FAILURE',
    #                "Could not import python module libxml2 "
    #                    "(see http://xmlsoft.org for installation help)")
        return False

def _validate_pattern_lxml(errors, stmt, invert_match):
    try:
        import lxml.etree
        doc = StringIO(
            '<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">' \
            '  <xsd:element name="a" type="x"/>' \
            '    <xsd:simpleType name="x">' \
            '      <xsd:restriction base="xsd:string">' \
            '        <xsd:pattern value=%s/>' \
            '      </xsd:restriction>' \
            '     </xsd:simpleType>' \
            '   </xsd:schema>' % quoteattr(stmt.arg))
        try:
            sch = lxml.etree.XMLSchema(lxml.etree.parse(doc))
            return ('lxml', sch, stmt.pos, invert_match)
        except lxml.etree.XMLSchemaParseError as v:
            err_add(errors, stmt.pos, 'PATTERN_ERROR', str(v))
            return None
    except ImportError:
        return False

def validate_pattern_expr(errors, stmt):
    invert_match = False
    if stmt.search_one('modifier', arg='invert-match') is not None:
        invert_match = True
    ## check that it's syntactically correct
    # First try with lxml
    res = _validate_pattern_lxml(errors, stmt, invert_match)
    if res is not False:
        return res
    # Then try with libxml2
    res = _validate_pattern_libxml2(errors, stmt, invert_match)
    if res is not False:
        return res
    # Otherwise we can't validate patterns :(
    return None

class PatternTypeSpec(TypeSpec):
    def __init__(self, base, pattern_specs):
        TypeSpec.__init__(self, base.name)
        self.base = base
        self.res = pattern_specs

    def str_to_val(self, errors, pos, str):
        return self.base.str_to_val(errors, pos, str)

    def validate(self, errors, pos, val, errstr=''):
        if self.base.validate(errors, pos, val, errstr) == False:
            return False
        for (type_, re, re_pos, invert_match) in self.res:
            if type_ == 'libxml2':
                is_valid = re.regexpExec(val) == 1
            elif type_ == 'lxml':
                import lxml
                doc = StringIO('<a>%s</a>' % escape(val))
                is_valid = re.validate(lxml.etree.parse(doc))
            if ((not is_valid and not invert_match) or
                (is_valid and invert_match)):
                err_add(errors, pos, 'TYPE_VALUE',
                        (val, self.definition, 'pattern mismatch' + errstr +
                         ' for pattern defined at ' + str(re_pos)))
                return False
        return True

    def restrictions(self):
        return self.base.restrictions()

def validate_enums(errors, enums, stmt):
    # make sure all names and values given are unique
    names = {}
    values = {}
    next = 0
    for e in enums:
        # for derived enumerations, make sure the enum is defined
        # in the base
        stmt.i_type_spec.validate(errors, e.pos, e.arg)
        e.i_value = None
        value = e.search_one('value')
        if value is not None:
            try:
                x = int(value.arg)
                # for derived enumerations, make sure the value isn't changed
                oldval = stmt.i_type_spec.get_value(e.arg)
                if oldval is not None and oldval != x:
                    err_add(errors, value.pos, 'BAD_ENUM_VALUE',
                            (value.arg, oldval))
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
    def __init__(self):
        TypeSpec.__init__(self, 'enumeration')

    def get_value(self, val):
        return None

    def restrictions(self):
        return ['enum']

class EnumTypeSpec(TypeSpec):
    def __init__(self, base, enums):
        TypeSpec.__init__(self, base.name)
        self.base = base
        self.enums = [(e.arg, e.i_value) for e in enums]

    def validate(self, errors, pos, val, errstr = ''):
        if util.keysearch(val, 0, self.enums) == None:
            err_add(errors, pos, 'TYPE_VALUE',
                    (val, self.definition, 'enum not defined' + errstr))
            return False
        else:
            return True

    def get_value(self, val):
        r  = util.keysearch(val, 0, self.enums)
        if r is not None:
            return r[1]
        else:
            return None

    def restrictions(self):
        return self.base.restrictions()

def validate_bits(errors, bits, stmt):
    # make sure all names and positions given are unique
    names = {}
    values = {}
    next = 0
    for b in bits:
        # for derived bits, make sure the bit is defined
        # in the base
        stmt.i_type_spec.validate(errors, b.pos, [b.arg])
        position = b.search_one('position')
        if position is not None:
            try:
                x = int(position.arg)
                # for derived bits, make sure the position isn't changed
                oldpos = stmt.i_type_spec.get_position(b.arg)
                if oldpos is not None and oldpos != x:
                    err_add(errors, position.pos, 'BAD_BIT_POSITION',
                            (position.arg, oldpos))
                b.i_position = x
                if x < 0 or x > 4294967295:
                    raise ValueError
                if x >= next:
                    next = x + 1
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
    def __init__(self):
        TypeSpec.__init__(self, 'bits')

    def get_position(self, bit):
        return None

    def restrictions(self):
        return ['bit']

class BitTypeSpec(TypeSpec):
    def __init__(self, base, bits):
        TypeSpec.__init__(self, base.name)
        self.base = base
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

    def get_position(self, bit):
        r  = util.keysearch(bit, 0, self.bits)
        if r is not None:
            return r[1]
        else:
            return None

    def restrictions(self):
        return self.base.restrictions()

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

        def parse_identifier(s):
            m = syntax.re_keyword_start.match(s)
            if m is None:
                raise Abort
            s = s[m.end():]
            if m.group(2) is None:
                # no prefix
                return (m.group(3), s)
            else:
                prefix = m.group(2)
                mod = util.prefix_to_module(path.i_module, prefix,
                                            path.pos, errors)
                if mod is not None:
                    return ((m.group(2), m.group(3)), s)
                else:
                    raise Abort

        def parse_key_predicate(s):
            s = s[1:] # skip '['
            s = skip_space(s)
            (identifier, s) = parse_identifier(s)
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
                (xidentifier, s) = parse_identifier(s)
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

        def parse_descendant(s):
            dn = []
            # all '..'s are now parsed
            while len(s) > 0 and (not s[0].isspace()) and s[0] != ')':
                (identifier, s) = parse_identifier(s)
                dn.append(identifier)
                s = skip_space(s)
                if len(s) == 0:
                    break
                while len(s) > 0 and s[0] == '[':
                    (pred, s) = parse_key_predicate(s)
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
            (derefdn, s) = parse_descendant(s)
            s = skip_space(s)
            s = s[1:] # skip ')'
            s = skip_space(s)
            s = s[1:] # skip '/'

        (up, s) = parse_dot_dot(s)
        (dn, s) = parse_descendant(s)
        return (up, dn, derefup, derefdn)

    try:
        return parse_keypath(path.arg)
    except Abort:
        return None

class LeafrefTypeSpec(TypeSpec):
    def __init__(self):
        TypeSpec.__init__(self, 'leafref')
        self.require_instance = True

    def restrictions(self):
        return ['path', 'require-instance']

class InstanceIdentifierTypeSpec(TypeSpec):
    def __init__(self):
        TypeSpec.__init__(self, 'instance-identifier')
        self.require_instance = True

    def restrictions(self):
        return ['require-instance']

class PathTypeSpec(TypeSpec):
    def __init__(self, base, path_spec, path, pos):
        TypeSpec.__init__(self, base.name)
        self.require_instance = True
        self.base = base
        self.path_spec = path_spec
        self.path_ = path
        self.pos = pos

    def str_to_val(self, errors, pos, str_):
        if hasattr(self, 'i_target_node'):
            return self.i_target_node.search_one('type').\
                i_type_spec.str_to_val(errors, pos, str_)
        else:
            # if a default value is verified
            return str_

    def validate(self, errors, pos, val, errstr = ''):
        if hasattr(self, 'i_target_node'):
            return self.i_target_node.search_one('type').\
                i_type_spec.validate(errors, pos, val)
        else:
            # if a default value is verified
            return True

    def restrictions(self):
        return ['require-instance']

class UnionTypeSpec(TypeSpec):
    def __init__(self, types):
        TypeSpec.__init__(self, 'union')
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
  {'int8':IntTypeSpec('int8', -128, 127),
   'int16':IntTypeSpec('int16', -32768, 32767),
   'int32':IntTypeSpec('int32', -2147483648, 2147483647),
   'int64':IntTypeSpec('int64', -9223372036854775808, 9223372036854775807),
   'uint8':IntTypeSpec('uint8', 0, 255),
   'uint16':IntTypeSpec('uint16', 0, 65535),
   'uint32':IntTypeSpec('uint32', 0, 4294967295),
   'uint64':IntTypeSpec('uint64', 0, 18446744073709551615),
   'decimal64':TypeSpec('decimal64'),
   'string':StringTypeSpec(),
   'boolean':BooleanTypeSpec(),
   'enumeration':EnumerationTypeSpec(),
   'bits':BitsTypeSpec(),
   'binary':BinaryTypeSpec(),
   'leafref':LeafrefTypeSpec(),
   'identityref':TypeSpec('identityref'),
   'instance-identifier':InstanceIdentifierTypeSpec(),
   'empty':EmptyTypeSpec(),
   'union':TypeSpec('union'),
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

