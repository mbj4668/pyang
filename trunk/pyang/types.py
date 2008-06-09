"""YANG built-in types"""

import re

from error import err_add
from debug import dbg

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

def is_base_type(typename):
    return typename in yang_type_specs

