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
    'concat': (['string', 'string', '*'], 'string'),
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

def add_extra_xpath_function(name, input_params, output_param):
    extra_xpath_functions[name] = (input_params, output_param)

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

# node is the initial context node or None if it is not known
def v_xpath(ctx, stmt, node):
    try:
        if hasattr(stmt, 'i_xpath') and stmt.i_xpath is not None:
            q = stmt.i_xpath
        else:
            q = xpath_parser.parse(stmt.arg)
            stmt.i_xpath = q
        if node is not None:
            chk_xpath_expr(ctx, stmt.i_orig_module, stmt.pos, node, node, q)
    except xpath_lexer.XPathError as e:
        err_add(ctx.errors, stmt.pos, 'XPATH_SYNTAX_ERROR', e.msg)
        stmt.i_xpath = None
    except SyntaxError as e:
        err_add(ctx.errors, stmt.pos, 'XPATH_SYNTAX_ERROR', e.msg)
        stmt.i_xpath = None

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
