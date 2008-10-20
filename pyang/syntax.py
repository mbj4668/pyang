"""Description of YANG & YIN syntax."""

import re

### Regular expressions - constraints on arguments

# keywords and identifiers
identifier = r"[_A-Za-z][._\-A-Za-z0-9]*"
prefix = identifier
keyword = '((' + prefix + '):)?(' + identifier + ')'

re_keyword = re.compile(keyword)
re_keyword_start = re.compile('^' + keyword)

pos_decimal = r"[1-9][0-9]*"
nonneg_decimal = r"(0|[1-9])[0-9]*"
decimal_ = r"[-+]?" + nonneg_decimal 
float_ = decimal_ + r"\.[0-9]+(E[-+]?[0-9]+)?$"
length_str = '((min|max|[0-9]+)\s*' \
             '(\.\.\s*' \
             '(min|max|[0-9]+)\s*)?)'
length_expr = length_str + '(\|\s*' + length_str + ')*'
re_length_part = re.compile(length_str)
range_str = '((\-INF|min|max|((\+|\-)?[0-9]+(\.[0-9]+)?))\s*' \
            '(\.\.\s*' \
            '(INF|min|max|(\+|\-)?[0-9]+(\.[0-9]+)?)\s*)?)'
range_expr = range_str + '(\|\s*' + range_str + ')*'
re_range_part = re.compile(range_str)

re_identifier = re.compile("^" + identifier + "$")


# path and unique
node_id = keyword
rel_path_keyexpr = r"(\.\./)+(" + node_id + "/)*" + node_id
path_key_expr = r"(current\(\)/" + rel_path_keyexpr + ")"
path_equality_expr = node_id + r"\s*=\s*" + path_key_expr
path_predicate = r"\[\s*" + path_equality_expr + r"\s*\]"
absolute_path_arg = "(/" + node_id + "(" + path_predicate + ")*)+"
descendant_path_arg = node_id + "(" + path_predicate + ")?" + absolute_path_arg
relative_path_arg = r"(\.\./)*" + descendant_path_arg
path_arg = "(" + absolute_path_arg + "|" + relative_path_arg + ")"
absolute_schema_nodeid = "(/" + node_id + ")+"
descendant_schema_nodeid = node_id + "(" + absolute_schema_nodeid + ")?"
unique_arg = descendant_schema_nodeid + "(\s+" + descendant_schema_nodeid + ")*"
augment_arg = "(" + absolute_schema_nodeid + "|" + descendant_schema_nodeid + ")"
key_arg = identifier + "(\s+" + identifier + ")*"
re_schema_node_id_part = re.compile('/' + node_id)

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

# Date
date = r"[1-2][0-9]{3}-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])"

re_nonneg_decimal = re.compile("^" + nonneg_decimal + "$")
re_decimal = re.compile("^" + decimal_ + "$")
re_uri = re.compile("^" + uri + "$")
re_boolean = re.compile("^(true|false)$")
re_version = re.compile("^1$")
re_date = re.compile("^" + date +"$")
re_status = re.compile("^(current|obsolete|deprecated)$")
re_key = re.compile("^" + key_arg + "$")
re_length = re.compile("^" + length_expr + "$")
re_range = re.compile("^" + range_expr + "$")
re_pos_decimal = re.compile(r"^(unbounded|" + pos_decimal + r")$")
re_ordered_by = re.compile(r"^(user|system)$")
re_node_id = re.compile("^" + node_id + "$")
re_path = re.compile("^" + path_arg + "$")
re_unique = re.compile("^" + unique_arg + "$")
re_augment = re.compile("^" + augment_arg + "$")

arg_type_map = {
    "identifier": lambda s: re_identifier.search(s) is not None,
    "non-negative-decimal": lambda s: re_nonneg_decimal.search(s) is not None,
    "decimal": lambda s: re_decimal.search(s) is not None,
    "uri": lambda s: re_uri.search(s) is not None,
    "boolean": lambda s: re_boolean.search(s) is not None,
    "version": lambda s: re_version.search(s) is not None,
    "date": lambda s: re_date.search(s) is not None,
    "status-arg": lambda s: re_status.search(s) is not None,
    "key-arg": lambda s: re_key.search(s) is not None,
    "length-arg": lambda s: re_length.search(s) is not None,
    "range-arg": lambda s: re_range.search(s) is not None,
    "max-value": lambda s: re_pos_decimal.search(s) is not None,
    "ordered-by-arg": lambda s: re_ordered_by.search(s) is not None,
    "identifier-ref": lambda s: re_node_id.search(s) is not None,
    "path-arg": lambda s: re_path.search(s) is not None,
    "unique-arg": lambda s: re_unique.search(s) is not None,
    "augment-arg": lambda s: re_augment.search(s) is not None,
    }
"""Argument type definitions.

Regular expressions for all argument types except plain string that
are checked directly by the parser.
"""

def add_arg_type(arg_type, regexp):
    """Add a new arg_type to the map.
    Used by extension plugins to register their own argument types."""
    arg_type_map[arg_type] = regexp

yin_map = {
    "anyxml": (False, "name"),
    "argument": (False, "name"),
    "augment": (False, "target-node"),
    "belongs-to": (False, "module"),
    "bit": (False, "name"),
    "case": (False, "name"),
    "choice": (False, "name"),
    "config": (False, "value"),
    "contact": (True, "info"),
    "container": (False, "name"),
    "default": (False, "value"),
    "description": (True, "text"),
    "enum": (False, "name"),
    "error-app-tag": (False, "value"),
    "error-message": (True, "value"),
    "extension": (False, "name"),
    "grouping": (False, "name"),
    "import": (False, "module"),
    "include": (False, "module"),
    "input": (None, None),
    "key": (False, "value"),
    "leaf": (False, "name"),
    "leaf-list": (False, "name"),
    "length": (False, "value"),
    "list": (False, "name"),
    "mandatory": (False, "value"),
    "max-elements": (False, "value"),
    "min-elements": (False, "value"),
    "module": (False, "name"),
    "must": (False, "condition"),
    "namespace": (False, "uri"),
    "notification": (False, "name"),
    "ordered-by": (False, "value"),
    "organization": (True, "info"),
    "output": (None, None),
    "path": (False, "value"),
    "pattern": (False, "value"),
    "position": (False, "value"),
    "prefix": (False, "value"),
    "presence": (False, "value"),
    "range": (False, "value"),
    "reference": (False, "info"),
    "revision": (False, "date"),
    "rpc": (False, "name"),
    "status": (False, "value"),
    "submodule": (False, "name"),
    "type": (False, "name"),
    "typedef": (False, "name"),
    "unique": (False, "tag"),
    "units": (False, "name"),
    "uses": (False, "name"),
    "value": (False, "value"),
    "when": (False, "condition"),
    "yang-version": (False, "value"),
    "yin-element": (False, "value"),
    }
"""Mapping of statements to the YIN representation of their arguments.

The values are pairs whose first component specifies whether the
argument is stored in a subelement and the second component is the
name of the attribute or subelement carrying the argument. See YANG
draft, Appendix B.
"""
