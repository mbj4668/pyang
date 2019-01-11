from . import xpath_lexer
from . import xpath_parser
from .error import err_add
from .util import prefix_to_module, search_data_node, data_node_up

core_functions = {
    'last': ([], 'number'),
    'position': ([], 'number'),
    'count': (['node-set'], 'number'),
    'id': (['object'], 'node-set'),
    'local-name': (['node-set', '?'], 'string'),
    'namespace-uri': (['node-set', '?'], 'string'),
    'name': (['node-set', '?'], 'string'),
    'string': (['object'], 'string'),
    'concat': (['string', 'string', 'string', '*'], 'string'),
    'starts-with': (['string', 'string'], 'boolean'),
    'contains': (['string', 'string'], 'boolean'),
    'substring-before': (['string', 'string'], 'string'),
    'substring-after': (['string', 'string'], 'string'),
    'substring': (['string', 'number', 'number', '?'], 'string'),
    'string-length': (['string', '?'], 'number'),
    'normalize-space': (['string', '?'], 'string'),
    'translate': (['string', 'string', 'string'], 'string'),
    'boolean': (['object'], 'boolean'),
    'not': (['boolean'], 'boolean'),
    'true': ([], 'boolean'),
    'false': ([], 'boolean'),
    'lang': (['string'], 'boolean'),
    'number': (['object'], 'number'),
    'sum': (['node-set'], 'number'),
    'floor': (['number'], 'number'),
    'ceiling': (['number'], 'number'),
    'round': (['number'], 'number'),
    }

yang_xpath_functions = {
    'current': ([], 'node-set')
    }

yang_1_1_xpath_functions = {
    'bit-is-set': (['node-set', 'string'], 'boolean'),
    'enum-value': (['string'], 'number'),
    'deref': (['node-set'], 'node-set'),
    'derived-from': (['node-set', 'string'], 'boolean'),
    'derived-from-or-self': (['node-set', 'string'], 'boolean'),
    're-match': (['string', 'string'], 'boolean'),
    }

extra_xpath_functions = {
    'deref': (['node-set'], 'node-set'), # pyang extension for 1.0
    }

def add_prefix(prefix, s):
    "Add `prefix` to all unprefixed names in `s`"
    # tokenize the XPath expression
    toks = xpath_lexer.scan(s)
    # add default prefix to unprefixed names
    toks2 = [_add_prefix(prefix, tok) for tok in toks]
    # build a string of the patched expression
    ls = [x.value for x in toks2]
    return ''.join(ls)

def _add_prefix(prefix, tok):
    if tok.type == 'name':
        m = re_ncname.match(tok.value)
        if m.group(2) == None:
            tok.value = prefix + ':' + tok.value
    return tok

## TODO: validate must/when after deviate

# node is the initial context node
def v_xpath(ctx, stmt, node):
    try:
        q = xpath_parser.parse(stmt.arg)
        #print "** q", q
        chk_xpath_expr(ctx, stmt.i_orig_module, stmt.pos, node, node, q)
    except xpath_lexer.XPathError as e:
        err_add(ctx.errors, stmt.pos, 'XPATH_SYNTAX_ERROR', e.msg)
    except SyntaxError as e:
        err_add(ctx.errors, stmt.pos, 'XPATH_SYNTAX_ERROR', e.msg)

# mod is the (sub)module where the stmt is defined, which we use to
# resolve prefixes.
def chk_xpath_expr(ctx, mod, pos, initial, node, q):
    if type(q) == type([]):
        chk_xpath_path(ctx, mod, pos, initial, node, q)
    elif type(q) == type(()):
        if q[0] == 'absolute':
            chk_xpath_path(ctx, mod, pos, initial, 'root', q[1])
        elif q[0] == 'relative':
            chk_xpath_path(ctx, mod, pos, initial, node, q[1])
        elif q[0] == 'union':
            for qa in q[1]:
                chk_xpath_path(ctx, mod, pos, initial, node, qa)
        elif q[0] == 'comp':
            chk_xpath_expr(ctx, mod, pos, initial, node, q[2])
            chk_xpath_expr(ctx, mod, pos, initial, node, q[3])
        elif q[0] == 'arith':
            chk_xpath_expr(ctx, mod, pos, initial, node, q[2])
            chk_xpath_expr(ctx, mod, pos, initial, node, q[3])
        elif q[0] == 'bool':
            chk_xpath_expr(ctx, mod, pos, initial, node, q[2])
            chk_xpath_expr(ctx, mod, pos, initial, node, q[3])
        elif q[0] == 'negative':
            chk_xpath_expr(ctx, mod, pos, initial, node, q[1])
        elif q[0] == 'function_call':
            chk_xpath_function(ctx, mod, pos, initial, node, q[1], q[2])
        elif q[0] == 'path_expr':
            chk_xpath_expr(ctx, mod, pos, initial, node, q[1])
        elif q[0] == 'path': # q[1] == 'filter'
            chk_xpath_expr(ctx, mod, pos, initial, node, q[2])
            chk_xpath_expr(ctx, mod, pos, initial, node, q[3])
        elif q[0] == 'var':
            # NOTE: check if the variable is known; currently we don't
            # have any variables in YANG xpath expressions
            err_add(ctx.errors, pos, 'XPATH_VARIABLE', q[1])
        elif q[0] == 'literal':
            # kind of hack to detect qnames, and mark the prefixes
            # as being used in order to avoid warnings.
            s = q[1]
            if s[0] == s[-1] and s[0] in ("'", '"'):
                s = s[1:-1]
                i = s.find(':')
                # make sure there is just one : present
                if i != -1 and s[i + 1:].find(':') == -1:
                    prefix = s[:i]
                    # we don't want to report an error; just mark the
                    # prefix as being used.
                    my_errors = []
                    prefix_to_module(mod, prefix, pos, my_errors)
                    for (pos0, code, arg) in my_errors:
                        if code == 'PREFIX_NOT_DEFINED':
                            err_add(ctx.errors, pos0,
                                    'WPREFIX_NOT_DEFINED', arg)

def chk_xpath_function(ctx, mod, pos, initial, node, func, args):
    signature = None
    if func in core_functions:
        signature = core_functions[func]
    elif func in yang_xpath_functions:
        signature = yang_xpath_functions[func]
    elif (mod.i_version != '1' and func in yang_1_1_xpath_functions):
        signature = yang_1_1_xpath_functions[func]
    elif ctx.strict and func in extra_xpath_functions:
        err_add(ctx.errors, pos, 'STRICT_XPATH_FUNCTION', func)
        return None
    elif not(ctx.strict) and func in extra_xpath_functions:
        signature = extra_xpath_functions[func]

    if signature is None:
        err_add(ctx.errors, pos, 'XPATH_FUNCTION', func)
        return None

    # check that the number of arguments are correct
    nexp = len(signature[0])
    nargs = len(args)
    if (nexp == nargs):
        pass
    elif (nexp == 0 and nargs != 0):
        err_add(ctx.errors, pos, 'XPATH_FUNC_ARGS',
                (func, nexp, nargs))
    elif (signature[0][-1] == '?' and nargs == (nexp - 1)):
        pass
    elif signature[0][-1] == '?':
        err_add(ctx.errors, pos, 'XPATH_FUNC_ARGS',
                (func, "%s-%s" % (nexp-1, nexp), nargs))
    elif (signature[0][-1] == '*' and nargs >= (nexp - 1)):
        pass
    elif signature[0][-1] == '*':
        err_add(ctx.errors, pos, 'XPATH_FUNC_ARGS',
                (func, "at least %s" % (nexp-1), nargs))
    elif nexp != nargs:
        err_add(ctx.errors, pos, 'XPATH_FUNC_ARGS',
                (func, nexp, nargs))

    # FIXME implement checks from check_function()

    # check the arguments - FIXME check type
    for arg in args:
        chk_xpath_expr(ctx, mod, pos, initial, node, arg)
    return signature[1]

def chk_xpath_path(ctx, mod, pos, initial, node, path):
    if len(path) == 0:
        return
    head = path[0]
    if head[0] == 'var':
        # check if the variable is known as a node-set
        # currently we don't have any variables, so this fails
        err_add(ctx.errors, pos, 'XPATH_VARIABLE', q[1])
    elif head[0] == 'function_call':
        func = head[1]
        args = head[2]
        rettype = chk_xpath_function(ctx, mod, pos, initial, node, func, args)
        if rettype is not None:
            # known function, check that it returns a node set
            if rettype != 'node-set':
                err_add(ctx.errors, pos, 'XPATH_NODE_SET_FUNC', func)
        if func == 'current':
            chk_xpath_path(ctx, mod, pos, initial, initial, path[1:])
    elif head[0] == 'step':
        axis = head[1]
        nodetest = head[2]
        preds = head[3]
        node1 = None
        if node is None:
            # we can't check the path
            pass
        elif axis == 'self':
            pass
        elif axis == 'child' and nodetest[0] == 'name':
            prefix = nodetest[1]
            name = nodetest[2]
            if prefix is None:
                pmodule = initial.i_module
            else:
                pmodule = prefix_to_module(mod, prefix, pos, ctx.errors)
            if pmodule is not None:
                if node == 'root':
                    children = pmodule.i_children
                elif hasattr(node, 'i_children'):
                    children = node.i_children
                else:
                    children = []
                child = search_data_node(children, pmodule.i_modulename, name)
                if child is None and node == 'root':
                    err_add(ctx.errors, pos, 'XPATH_NODE_NOT_FOUND2',
                            (pmodule.i_modulename, name, pmodule.arg))
                elif child is None and node.i_module is not None:
                    err_add(ctx.errors, pos, 'XPATH_NODE_NOT_FOUND1',
                            (pmodule.i_modulename, name,
                             node.i_module.i_modulename, node.arg))
                elif child is None:
                    err_add(ctx.errors, pos, 'XPATH_NODE_NOT_FOUND2',
                            (pmodule.i_modulename, name, node.arg))
                else:
                    node1 = child
        elif axis == 'parent' and nodetest == ('node_type', 'node'):
            p = data_node_up(node)
            if p is None:
                err_add(ctx.errors, pos, 'XPATH_PATH_TOO_MANY_UP', ())
            else:
                node1 = p
        else:
            # we can't validate the steps on other axis, but we can validate
            # functions etc.
            pass
        for p in preds:
            chk_xpath_expr(ctx, mod, pos, initial, node1, p)
        chk_xpath_path(ctx, mod, pos, initial, node1, path[1:])


# all_functions = []
# all_functions.extend(xpath.core_functions)
# all_functions.extend(yang_xpath_functions)
# all_functions.extend(yang_1_1_xpath_functions)
# all_functions.extend(extra_xpath_functions)
and_or_func = []
#    found = re_and_or.findall(func)
#    if len(found) > 0:
#        and_or_func.append(func)

def v_xpath_old(ctx, stmt):
    try:
        args = set()
        no_new_line = stmt.arg.replace('\n', ' ')
        dict_to_return = {}
        for i, func in enumerate(and_or_func):
            replace_and_or = 'replaceAndOr_num{}'.format(i)
            no_new_line = no_new_line.replace(func, replace_and_or)
            dict_to_return[replace_and_or] = func

        args.update(re.split(r'(?<!-)\band\b(?!-)|(?<!-)\bor\b(?!-)',
                             no_new_line))
        for arg in args:
            if sys.version < '3':
                for key, val in dict_to_return.iteritems():
                    arg = arg.replace(key, val)
            else:
                for key, val in dict_to_return.items():
                    arg = arg.replace(key, val)
            toks = xpath.tokens(arg)
            axis = False
            for tok in toks:
                if tok[0] == 'axis':
                    # TODO resolve xpath axis
                    axis = True
                    break
            checked = False
            # Do not compare function types if function exists
            # TODO compare function types
            function_exists = False
            for (x, (tokname, s)) in enumerate(toks):
                if tokname == 'name' or tokname == 'prefix-match':
                    i = s.find(':')
                    if i != -1:
                        prefix = s[:i]
                        prefix_to_module(stmt.i_module, prefix, stmt.pos,
                                         ctx.errors)
                elif tokname == 'literal':
                    # kind of hack to detect qnames, and mark the prefixes
                    # as being used in order to avoid warnings.
                    if s[0] == s[-1] and s[0] in ("'", '"'):
                        s = s[1:-1]
                        i = s.find(':')
                        # make sure there is just one : present
                        if i != -1 and s[i + 1:].find(':') == -1:
                            prefix = s[:i]
                            # we don't want to report an error; just mark the
                            # prefix as being used.
                            my_errors = []
                            prefix_to_module(stmt.i_module, prefix, stmt.pos,
                                             my_errors)
                            for (pos, code, arg) in my_errors:
                                if code == 'PREFIX_NOT_DEFINED':
                                    err_add(ctx.errors, pos,
                                            'WPREFIX_NOT_DEFINED', arg)
                elif ctx.lax_xpath_checks == True:
                    pass
                elif tokname == 'variable':
                    err_add(ctx.errors, stmt.pos, 'XPATH_VARIABLE', s)
                elif tokname == 'function':
                    function_exists = True
                    if not (s in xpath.core_functions or
                            s in yang_xpath_functions or
                            (stmt.i_module.i_version != '1' and
                             s in yang_1_1_xpath_functions) or
                            s in extra_xpath_functions):
                        err_add(ctx.errors, stmt.pos, 'XPATH_FUNCTION', s)
                        checked = True
                    else:
                        if not axis:
                            checked = check_function(toks, x, stmt.copy(),
                                                     ctx, checked)
                if (not checked and 'enum-value' not in arg and
                    'bit-is-set' not in arg):
                    if (tokname in ['.', '..', '/', 'current', 'deref', 'name']
                        and not axis):
                        checked = True
                        check_basic_path(stmt.copy(), toks, ctx, x,
                                         function_exists=function_exists)
    except SyntaxError as e:
        err_add(ctx.errors, stmt.pos, 'XPATH_SYNTAX_ERROR', e)
    except AttributeError as e:
        err_add(ctx.errors, stmt.pos, 'XPATH_MISSING_NODE', e)


def check_deref(func_toks, stmt, ctx):
    path = ''
    for tok in func_toks[2:-1]:
        path += tok[1]
    stmts = check_path(path, stmt, ctx)
    if stmts is None:
        return None
    return stmts[0]


def check_basic_path(stmt, toks, ctx, x,
                     return_stmt=False, function_exists=False):
    comparator = ['=', '<', '>', '!=', '>=', '<=']
    special_toks = ['+', '-', '*', ' / ', ' mod ', ' div ', '|']

    predicate = False
    paths_left = {}
    paths_right = {}
    new_toks = []
    new_arg = ''
    path = ''
    left_side = True
    in_func = False
    is_deref = False
    func_toks = []
    left_bracket = 0
    for y, tok in enumerate(toks[x:]):
        if tok[0] == 'function' and tok[1] != 'current':
            function_exists = True
            left_bracket = 0
            in_func = True
            func_toks.append(tok)
            if tok[1] == 'deref':
                is_deref = True
            continue
        if in_func:
            func_toks.append(tok)
            if tok[0] == '(':
                left_bracket += 1
            elif tok[0] == ')':
                left_bracket -=1
            if left_bracket == 0:
                if is_deref:
                    stmt = check_deref(func_toks, stmt, ctx)
                    if stmt is None:
                        return None
                    path += '.'
                else:
                    if check_function(func_toks, 0, stmt, ctx, False) is None:
                        return None
                in_func = False
            continue
        if predicate:
            if tok[0] == ']':
                predicate = False
                check_basic_path(stmt, xpath.tokens(new_arg), ctx, 0)
                continue
            new_toks.append(tok)
            new_arg += tok[1]
            continue
        if tok[0] == '[':
            predicate = True
            new_toks.extend(toks[: y])
            new_toks.append(('/', '/'))
            new_arg = path + '/'
            continue
        if tok[0] == 'whitespace':
            continue
        if tok[0] in ['literal', 'number']:
            if left_side:
                paths_left[tok[1]] = 'literal'
            else:
                paths_right[tok[1]] = 'literal'
            continue
        if tok[0] in special_toks:
            if len(path) > 0:
                if left_side:
                    paths_left[path] = 'path'
                else:
                    paths_right[path] = 'path'
                path = ''
            continue
        elif tok[0] in comparator:
            if len(path) > 0:
                if left_side:
                    paths_left[path] = 'path'
                else:
                    paths_right[path] = 'path'
                path = ''
            left_side = False
            continue
        path += tok[1]

    if len(path) > 0 and len(path.strip().replace(')', '')) > 0:
        if left_side:
            paths_left[path] = 'path'
        else:
            paths_right[path] = 'path'

    comparing_value = ''
    if sys.version < '3':
        for value, path_or_literal in paths_left.iteritems():
            if path_or_literal == 'path':
                comparing_value = value
                break
    else:
        for value, path_or_literal in paths_left.items():
            if path_or_literal == 'path':
                comparing_value = value
                break
    if comparing_value == '':
        if sys.version < '3':
            for value, path_or_literal in paths_right.iteritems():
                if path_or_literal == 'path':
                    comparing_value = value
                    break
        else:
            for value, path_or_literal in paths_right.items():
                if path_or_literal == 'path':
                    comparing_value = value
                    break
        del paths_right[comparing_value]
    else:
        del paths_left[comparing_value]

    path_stmts = check_path(comparing_value, stmt, ctx)
    if path_stmts is None:
        return None
    if len(paths_left) == 0 and len(paths_right) == 0:
        # In case of single path in substatement path was already checked
        # so we can skip this
        if return_stmt:
            return path_stmts

    else:
        paths_left.update(paths_right)
        if sys.version < '3':
            iteritems = paths_left.iteritems()
        else:
            iteritems = paths_left.items()
        for value, path_or_literal in iteritems:
            if path_or_literal == 'literal':
                value = value.replace("'", '').replace('"', '').strip()
                for path_stmt in path_stmts:
                    type = get_type_of_typedef(path_stmt, ctx)
                    check_type(path_stmt.search_one('type'), type,
                               value, ctx)
            else:
                path_stmts2 = check_path(value, stmt, ctx)
                if path_stmts2 is None:
                    return None
                for path_stmt in path_stmts:
                    for path_stmt2 in path_stmts2:
                        types = get_type_of_typedef(path_stmt, ctx, True)
                        types2 = get_type_of_typedef(path_stmt2, ctx, True)
                        if not isinstance(types, list):
                            types = [types]
                        if not isinstance(types2, list):
                            types2 = [types2]
                        found = False
                        for type in types:
                            for type2 in types2:
                                if type == type2 or function_exists:
                                    found = True
                                elif ((type.startswith('uint') and
                                       type2.startswith('uint')) or
                                      (type.startswith('int') and
                                       type2.startswith('int'))):
                                    found = True
                        if not found:
                            raise SyntaxError(
                                'Types in path condition "{}" does '.format(stmt.arg) +
                                'not equal')


def get_type_of_typedef(path_stmt, ctx, check_union=False):
    if path_stmt.keyword == 'identity':
        return 'identityref'
    elif path_stmt.keyword == 'refine':
        path_stmt = check_path(path_stmt.arg, path_stmt.parent, ctx)
        if path_stmt is None:
            return None
        else:
            path_stmt = path_stmt[0]
    try:
        type_stmt = path_stmt.search_one('type')
        name = type_stmt.i_type_spec.name
        if name == 'leafref':
            return get_type_of_typedef(type_stmt.i_type_spec.i_target_node, ctx, check_union)
        elif name == 'union' and check_union:
            ret = []
            for t in type_stmt.search('type'):
                ret.append(t.arg)
            return ret
        else:
            return name
    except AttributeError:
        return path_stmt.search_one('type').arg


def check_type(stmt, type, literal, ctx):
    try:
        if stmt is not None:
            if stmt.arg == 'leafref':
                stmt = stmt.i_type_spec.i_target_node.search_one('type')
        if type.startswith('int'):
            # int can be compared with decimal value
            float(literal)
        elif type.startswith('uint'):
            if literal.startswith('-'):
                raise Exception

            float(literal)
        elif type == 'decimal64':
            float(literal)
        elif type == 'enumeration':
            enums = stmt.i_type_spec.enums
            found = False
            for enum in enums:
                if enum[1] == literal or enum[0] == literal:
                    found = True
                    break
            if not found:
                raise Exception
        elif type == 'boolean':
            if literal not in ['true', 'false']:
                raise Exception
        elif type == 'bits':
            bits = stmt.i_type_spec.bits
            found = False
            if len(literal) == 0:
                found = True
            else:
                for bit in bits:
                    if bit[0] == literal:
                        found = True
                        break
            if not found:
                raise Exception
        elif type == 'empty':
            raise Exception
        elif type == 'binary':
            if re.match('^(0*1*)*$', literal) is None:
                raise Exception
        elif type == 'union':
            types = stmt.search('type')
            found = False
            for type in types:
                try:
                    check_type(type, type.arg, literal, ctx)
                    found = True
                    break
                except SyntaxError:
                    pass
            if not found:
                type_list = []
                for type in types:
                    type_list.append(type.arg)
                type = ' or '.join(type_list)
                raise Exception
    except Exception:
        raise SyntaxError('Literal {} from path is not of type {}'.\
                          format(literal, type))


def find_grouping_uses(containers_lists, substmts, uses_name,
                       container_list=None):
    for substmt in substmts:
        try:
            if substmt.keyword in ['list', 'container', 'augment', 'grouping']:
                containers_lists = find_grouping_uses(containers_lists,
                                                      substmt.substmts,
                                                      uses_name, substmt)
            elif substmt.keyword == 'uses':
                if substmt.arg == uses_name:
                    containers_lists.add(container_list)
                else:
                    containers_lists = find_grouping_uses(
                        containers_lists,
                        substmt.i_grouping.substmts, uses_name,
                        container_list)
        except:
            pass
    return containers_lists


def check_function(tokens, pos, stmt, ctx, checked):
    if tokens[pos][1] in ['name', 'count', 'local-name']:
        parameters = check_and_return_parameters(0, tokens[pos + 2:],
                                                 tokens[pos][1])
        for param in parameters:
            if '/' in param:
                check_basic_path(stmt, xpath.tokens(param.strip()), ctx, 0)
    elif tokens[pos][1] in ['contains']:
        parameters = check_and_return_parameters(2, tokens[pos + 2:],
                                                 tokens[pos][1])
        for param in parameters:
            if '/' in param:
                check_basic_path(stmt, xpath.tokens(param.strip()), ctx, 0)
    elif tokens[pos][1] in ['derived-from-or-self', 'derived-from']:
        parameters = check_and_return_parameters(2, tokens[pos + 2:],
                                                 tokens[pos][1])
        instance_id = parameters[1].replace('\"', '').replace('\'', '').strip()
        check_identity(instance_id, stmt, ctx)
        path_stmts = check_basic_path(stmt, xpath.tokens(parameters[0].strip()),
                                      ctx, 0, True)
        if path_stmts is None:
            return True
        for path_stmt in path_stmts:
            if get_type_of_typedef(path_stmt, ctx) != 'identityref':
                raise SyntaxError('Resolved XPath "{}" is not of type ' +
                                  'identity-ref'.format(stmt.arg))
    elif tokens[pos][1] == 'enum-value':
        parameters = check_and_return_parameters(1, tokens[pos + 2:],
                                                 tokens[pos][1])
        path = ''
        add_before_enum = pos - 1
        separator = '/'
        if add_before_enum < 0:
            add_before_enum = 0
            separator = ''
        for value in tokens[:add_before_enum]:
            path += value[1]
        path += separator + parameters[0]
        enum_stmts = check_path(path, stmt, ctx)
        if enum_stmts is None:
            return None
        for enum_stmt in enum_stmts:
            enum = enum_stmt.search_one('type')
            if enum is None:
                SyntaxError('Resolved XPath statement "{}" is not of type ' +
                            'enum'.format(stmt.arg))
            enum = enum.i_type_spec
            if enum.name == 'enumeration':
                found = False
                param = None
                for t in tokens[pos + 2:]:
                    if t[0] == 'number':
                        param = int(t[1])
                        break
                    elif t[0] == ']':
                        raise SyntaxError('End bracket "]" found before ' +
                                          'enum number value in XPath'.\
                                          format(stmt.arg))
                if param is not None:
                    for enum_tuple in enum.enums:
                        if enum_tuple[1] == param:
                            found = True
                            break
                    if not found:
                        raise SyntaxError('Not existing enum in XPath {}'.\
                                          format(stmt.arg))
            else:
                SyntaxError('Resolved XPath statement "{}" is not of ' +
                            'type enum'.format(stmt.arg))
    elif tokens[pos][1] == 're-match':
        parameters = check_and_return_parameters(2, tokens[pos + 2:],
                                                 tokens[pos][1])
        path = parameters[0].strip()
        if path[0] in ['"', "'"]:
            return None
        path_stmts = check_path(path, stmt, ctx)
        if path_stmts is None:
            return None
        for path_stmt in path_stmts:
            type = get_type_of_typedef(path_stmt, ctx)
            if type != 'string':
                raise SyntaxError('XPath "{}" must be resolved with a ' +
                                  'node of type string'.format(stmt.arg))
    elif tokens[pos][1] == 'bit-is-set':
        parameters = check_and_return_parameters(2, tokens[pos + 2:],
                                                 tokens[pos][1])
        path = ''
        add_before_bit = pos - 1
        separator = '/'
        if add_before_bit < 0:
            add_before_bit = 0
            separator = ''
        for value in tokens[:add_before_bit]:
            path += value[1]
        path += separator + parameters[0]
        bit_stmts = check_path(path, stmt, ctx)
        if bit_stmts is None:
            return None
        for bit_stmt in bit_stmts:
            bits = bit_stmt.search_one('type')
            bits = bits.i_type_spec
            if bits.name == 'bits':
                found = False
                param = parameters[1].replace('\"', '').\
                        replace('\'', '').strip()
                for bits_tuple in bits.bits:
                    if bits_tuple[0] == param:
                        found = True
                        break
                if not found:
                    raise SyntaxError('Not existing bit in XPath "{}"'.\
                                      format(stmt.arg))
            else:
                raise SyntaxError('Resolved XPath statement "{}" is not ' +
                                  'of type bit'.format(stmt.arg))
    else:
        return checked
    return True


def check_path(path, stmt, ctx):

    def resolve_special_keywords(data_holding_stmt, data_holding_stmts, x):
        if data_holding_stmt.keyword in ['case', 'choice', 'uses', 'action']:
            data_holding_stmts[x] = data_holding_stmt.parent
            data_holding_stmt = data_holding_stmts[x]
            data_holding_stmt = resolve_special_keywords(data_holding_stmt,
                                                         data_holding_stmts, x)
        elif data_holding_stmt.keyword == 'grouping':
            root_children = data_holding_stmt.i_module.substmts
            if len(root_children) > 0:
                data_holding_stmts.extend(
                    list(find_grouping_uses(set(), root_children,
                                            data_holding_stmt.arg)))
                if len(data_holding_stmts) > 1:
                    data_holding_stmts.remove(data_holding_stmt)
                    data_holding_stmt = data_holding_stmts[x]
                    data_holding_stmt = resolve_special_keywords(
                        data_holding_stmt, data_holding_stmts, x)
        elif data_holding_stmt.keyword == 'augment':
            try:
                if data_holding_stmt.i_target_node is None:
                    err_add(ctx.errors, data_holding_stmt.pos, 'NODE_NOT_FOUND',
                            (data_holding_stmt.i_modulename,
                             data_holding_stmt.arg))
                    return None
                else:
                    data_holding_stmts[x] = data_holding_stmt.i_target_node
                    data_holding_stmt = data_holding_stmts[x]
                    data_holding_stmt = resolve_special_keywords(
                        data_holding_stmt, data_holding_stmts, x)
            except AttributeError:
                # TODO investigate why augmentation`s target node
                # is not set at all
                return None
        elif data_holding_stmt.keyword == 'deviate':
            data_holding_stmts[x] = data_holding_stmt.parent.i_target_node
            data_holding_stmt = data_holding_stmts[x]
            data_holding_stmt = resolve_special_keywords(
                data_holding_stmt, data_holding_stmts, x)
        return data_holding_stmt

    def find_refine_node(refinement, stmt_copy):
        # parse the path into a list of two-tuples of (prefix,identifier)
        pstr = '/' + refinement.arg
        path = [(m[1], m[2]) \
                    for m in syntax.re_schema_node_id_part.findall(pstr)]
        node = stmt_copy.parent
        # recurse down the path
        for (prefix, identifier) in path:
            module = prefix_to_module(stmt_copy.i_module, prefix,
                                      refinement.pos, ctx.errors)
            if hasattr(node, 'i_children'):
                if module is None:
                    return None
                child = search_child(node.i_children, module.i_modulename,
                                     identifier)
                if child is None:
                    err_add(ctx.errors, refinement.pos, 'NODE_NOT_FOUND',
                            (module.i_modulename, identifier))
                    return None
                node = child
            else:
                err_add(ctx.errors, refinement.pos, 'BAD_NODE_IN_REFINE',
                        (module.i_modulename, identifier))
                return None
        return node

    path = path.strip()
    while path.startswith('('):
        path = path[1:]
    while path.endswith(')'):
        if path.endswith('current()'):
            break
        path = path[:-1]
    if path == '':
        return None
    parts = path.split('/')
    if parts[0] == '':
        if ':' in parts[1]:
            prefix = parts[1].split(':')[0]
            data_holding_stmts = prefix_to_module(stmt.i_module,
                                                  prefix, stmt.pos, ctx.errors)
            if data_holding_stmts is None:
                return None
        else:
            data_holding_stmts = stmt.i_module
        parts.remove(parts[0])
    elif stmt.keyword in ['must', 'when']:
        data_holding_stmts = stmt.parent
    else:
        data_holding_stmts = stmt.copy()
    if data_holding_stmts is None:
        raise AttributeError('Wrong XPath "{}"'.format(stmt.arg))
    data_holding_stmts = [data_holding_stmts]
    stmts_to_remove = set()
    if(len(parts) == 1):
        modules = []
        if ':' in parts[0]:
            prefix = parts[0].split(':')[0]
            m = prefix_to_module(stmt.i_module, prefix, stmt.pos, ctx.errors)
            if m is None:
                return None
            else:
                modules.append(m)
        else:
            modules.append(stmt.i_module)
            if sys.version < '3':
                for key, val in ctx.modules.iteritems():
                    if val.keyword == 'submodule':
                        modules.append(val)
            else:
                for key, val in ctx.modules.items():
                    if val.keyword == 'submodule':
                        modules.append(val)
        for mod in modules:
            list_indentity_ref = mod.search('identity')
            for id_ref in list_indentity_ref:
                if id_ref.arg == parts[0]:
                    return [id_ref]
    for part in parts:
        part = part.split(':')[-1]
        resolve_special_once = False
        for x, data_holding_stmt in enumerate(data_holding_stmts):
            if not resolve_special_once:
                data_holding_stmt = resolve_special_keywords(
                    data_holding_stmt, data_holding_stmts, x)
                if data_holding_stmt is None:
                    return None
                resolve_special_once = True

            if '..' == part:
                if data_holding_stmt.keyword == 'refine':
                    # TODO implement refine
                    return None
                if data_holding_stmt.parent is None:
                    raise AttributeError('Too many ".." in XPath "{}"'.\
                                         format(stmt.arg))
                else:
                    data_holding_stmts[x] = data_holding_stmt.parent
                    continue
            elif part in ['current()', '.']:
                continue
            else:
                child_found = False
                if data_holding_stmt.keyword in ['leaf', 'leaf-list']:
                    raise AttributeError('Searching for "{}" in leaf or ' +
                                         'leaf-list statement "{}". ' +
                                         'Leaf or leaf-list statement does ' +
                                         'not contain any children'
                                      .format(part, data_holding_stmt.arg))
                elif data_holding_stmt.keyword == 'refine':
                    data_holding_stmt = find_refine_node(
                        data_holding_stmt, data_holding_stmt.parent)
                    if data_holding_stmt is None:
                        err_add(ctx.errors, data_holding_stmt.pos,
                                'BAD_NODE_IN_REFINE',
                                (data_holding_stmt.i_modulename,
                                 data_holding_stmt.arg))
                        return None
                for child_stmt in data_holding_stmt.i_children:
                    child_received = check_choice(child_stmt, part)
                    if child_received is not None:
                        data_holding_stmts[x] = child_received
                        child_found = True
                        break
                if not child_found:
                    stmts_to_remove.add(x)

    if len(stmts_to_remove) > 0:
        stmts_to_remove = list(stmts_to_remove)
        stmts_to_remove.reverse()
        for stmt_to_remove in stmts_to_remove:
            del data_holding_stmts[stmt_to_remove]
    if len(data_holding_stmts) == 0:
        raise AttributeError('XPath for "{}" does not exist'.format(stmt.arg))
    return data_holding_stmts


def check_choice(child_stmt, part):
    if child_stmt.keyword == 'choice':
        for choice_child_stmt in child_stmt.i_children:
            if choice_child_stmt.keyword == 'case':
                for case_child_stmt in choice_child_stmt.i_children:
                    ret = check_choice(case_child_stmt, part)
                    if ret is not None:
                        return ret
            else:
                if choice_child_stmt.arg == part:
                    return choice_child_stmt
    elif child_stmt.arg == part:
        return child_stmt
    else:
        return None


def check_identity(instance_id, stmt, ctx):
    prefix_name = instance_id.split(':')
    search_stmts = []
    if len(prefix_name) == 2:
        name = prefix_name[1]
        prefix = prefix_name[0]
        if sys.version < '3':
            for key, val in ctx.modules.iteritems():
                if val.i_prefix == prefix:
                    search_stmts.append(val)
        else:
            for key, val in ctx.modules.items():
                if val.i_prefix == prefix:
                    search_stmts.append(val)
        if len(search_stmts) == 0:
            err_add(ctx.errors, stmt.pos, 'WPREFIX_NOT_DEFINED', (prefix))
            return
    else:
        search_stmts.append(stmt.i_module)
        if sys.version < '3':
            for key, val in ctx.modules.iteritems():
                if val.keyword == 'submodule':
                    search_stmts.append(val)
        else:
            for key, val in ctx.modules.items():
                if val.keyword == 'submodule':
                    search_stmts.append(val)
        name = prefix_name[0]

    exist = False

    for search_stmt in search_stmts:
        list_indentity_ref = search_stmt.search('identity')
        for id_ref in list_indentity_ref:
            if id_ref.arg == name:
                exist = True
    if not exist:
        err_add(ctx.errors, stmt.pos, 'IDENTITY_NOT_FOUND',
                (name, stmt.i_module.arg))


def check_and_return_parameters(expected_count, tokens, func_name):
    parameters = []
    brackets = 1
    parameter = []
    x = 0
    if tokens[x][1] == '(':
        x += 1

    while brackets:
        if tokens[x][1] == ')':
            parameter.append(tokens[x][1])
            brackets -= 1
        elif tokens[x][1] == '(':
            parameter.append(tokens[x][1])
            brackets += 1
        elif tokens[x][1] == ',':
            parameters.append(''.join(parameter))
            parameter = []
        else:
            parameter.append(tokens[x][1])
        x += 1

    if len(parameter) > 0:
        parameters.append(''.join(parameter[:-1]))
    if expected_count > 0:
        if len(parameters) != expected_count:
            raise SyntaxError('Expected {} arguments in function "{}", ' +
                              'but received {}'.format(expected_count,
                                                       func_name,
                                                       len(parameters)))
    return parameters
