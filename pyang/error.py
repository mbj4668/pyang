import copy

### struct to keep track of position for error messages

class Position(object):
    def __init__(self, ref):
        self.ref = ref
        self.line = 0
        self.top_name = None
    def __str__(self):
        return self.ref + ':' + str(self.line)

### Exceptions

class Abort(Exception):
    """used for non-recoverable errors to abort parsing"""
    pass

class Eof(Exception):
    """raised by tokenizer when end of file is detected"""
    pass

### error codes

error_codes = \
    {
    'READ_ERROR':
      (1,
       'read error: %s'),
    'EOF_ERROR':
      (1,
       'premature end of file'),
    'EXPECTED_QUOTED_STRING':
      (1,
       'expected quoted string after \'+\' operator'),
    'UNKNOWN_KEYWORD':
      (1,
       'unknown keyword "%s"'),
    'INCOMPLETE_STATEMENT':
      (1,
       'unterminated statement definition for keyword "%s", looking at %s'),
    'EXPECTED_KEYWORD':
      (1,
       'expected keyword "%s"'),
    'UNEXPECTED_KEYWORD':
      (1,
       'unexpected keyword "%s"'),
    'UNKNOWN_KEYWORD':
      (1,
       'unknown keyword "%s"'),
    'UNEXPECTED_KEYWORD_1':
      (1,
       'unexpected keyword "%s", expected "%s"'),
    'UNEXPECTED_KEYWORD_N':
      (1,
       'unexpected keyword "%s", expected one of %s'),
    'UNEXPECTED_TOKEN':
      (1,
       'unexpected token "%s"'),
    'UNEXPECTED_TOKEN_1':
      (1,
       'unexpected token "%s", expected "%s"'),
    'UNEXPECTED_TOKEN_N':
      (1,
       'unexpected token "%s", expected one of %s'),
    'EXPECTED_ARGUMENT':
      (1,
       'expected an argument for keyword "%s"'),
    'UNEXPECTED_ARGUMENT':
      (1,
       'did not expect an argument, got "%s"'),
    'TRAILING_GARBAGE':
      (2,
       'trailing garbage after module'),
    'BAD_VALUE':
      (1,
       'bad value "%s" (should be %s)'),
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
       'prefix "%s" is not defined (reported only once)'),
    'NODE_NOT_FOUND':
      (1,
       'node %s:%s is not found'),
    'BAD_NODE_IN_AUGMENT':
      (1,
       'node %s:%s cannot be augmented'),
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
       'the node "%s" is not found in the grouping'),
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
       'enumeration at %s'),
    'ENUM_VALUE':
      (1,
       'the enumeration value "%s" is not an 32 bit integer'),
    'DUPLICATE_BIT_POSITION':
      (1,
       'the position "%d" has already been used for the bit at %s'),
    'BIT_POSITION':
      (1,
       'the position value "%s" is not valid'),
    'NEED_KEY':
      (1,
       'the list needs at least one key'),
    'NEED_KEY_USES':
      (1,
       'the list at "%s" needs at least one key because it is used as config'),
    'BAD_KEY':
      (1,
       'the key "%s" does not reference an existing leaf'),
    'BAD_UNIQUE':
      (1,
       'the unique argument "%s" does not reference an existing leaf'),
    'BAD_UNIQUE_PART':
      (1,
       'the identifier "%s" in the unique argument does not reference '
       'an existing container or list'),
    'DUPLICATE_KEY':
      (1,
       'the key "%s" must not be listed more than once'),
    'DUPLICATE_UNIQUE':
      (3,
       'the leaf "%s" occurs more than once in the unique expression'),
    'PATTERN_ERROR':
      (2,
       'syntax error in pattern: %s'),
    'PATTERN_FAILURE':
      (3,
       'could not verify pattern: %s'),
    'KEYREF_TOO_MANY_UP':
      (1,
       'the keyref path for %s at %s has too many ".."'),
    'KEYREF_IDENTIFIER_NOT_FOUND':
      (1,
       '%s:%s in the keyref path for %s at %s is not found'),
    'KEYREF_IDENTIFIER_BAD_NODE':
      (1,
       '%s:%s in the keyref path for %s at %s references a %s node'),
    'KEYREF_BAD_PREDICATE':
      (1,
       '%s:%s in the keyref path for %s at %s has a predicate, '
       'but is not a list'),
    'KEYREF_BAD_PREDICATE_PTR':
      (1,
       '%s:%s in the keyref path\'s predicate for %s at %s is compared '
       'with a leaf that is not a correct keyref'),
    'KEYREF_NOT_LEAF_KEY':
      (1,
       'the keyref path for %s at %s does not refer to a key leaf in a list'),
    'KEYREF_NO_KEY':
      (1,
       '%s:%s in the keyref path for %s at %s is not the name of a key leaf'),
    'KEYREF_MULTIPLE_KEYS':
      (1,
       '%s:%s in the keyref path for %s at %s is referenced more than once'),
    'KEYREF_BAD_CONFIG':
      (1,
       'the keyref path for %s at %s is config but refers to a non-config key'),
    'DUPLICATE_CHILD_NAME':
      (1,
       'there is already a child node to "%s" at %s with the name "%s" '
       'defined at %s'),
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
       'the type %s (defined at %s) cannot be part of a union'),
    'BAD_TYPE_IN_KEY':
      (1,
       'the type %s cannot be part of a key, used by leaf %s'),
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
    'DUPLICATE_MODULE':
      (1,
       'duplicate module %s found (conflicts with %s)'),
    'MISSING_ARGUMENT_ATTRIBUTE':
      (1,
       'missing argument attribute "%s"'),
    'MISSING_ARGUMENT_ELEMENT':
      (1,
       'missing argument element "%s" for "%s"'),
    'UNEXPECTED_ATTRIBUTE':
      (1,
       'unexpected attribute %s'),
    'INVALID_CONFIG':
      (2,
       'config true cannot be set when the parent is config false'),

    'UNUSED_IMPORT':
      (4,
       'imported module %s not used'),

    'UNUSED_TYPEDEF':
      (4,
       'typedef %s not used'),

    'UNUSED_GROUPING':
      (4,
       'grouping %s not used'),

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

def is_warning(level):
    return not is_error(level)

def is_error(level):
    return level < 4

