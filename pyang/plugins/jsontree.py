"""JSON-Tree output plugin
Generates a json file that presents a tree-navigator
to the YANG module(s).
"""

import optparse
from pyang import plugin, statements, util
import json
import re

def pyang_plugin_init():
    plugin.register_plugin(JSONTreePlugin())

class JSONTreePlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['jsontree'] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--include-keys",
                                 dest="include_keys",
                                 action="store_true",
                                 help="""Include Key paths in each leaf node""")
        ]

        g = optparser.add_option_group("jsontree output specific options")
        g.add_options(optlist)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        emit_tree(modules, fd, ctx)

def emit_tree(modules, fd, ctx):
    nodes = []
    for id,module in enumerate(modules, start=1):
        pr = module.search_one('prefix')
        if pr is not None:
            prstr = pr.arg
        else:
            prstr = ""
        prefix = prstr

        node_name = module.arg

        descr = module.search_one('description')
        node_desc = None
        descrstring = "No description"
        if descr is not None:
            descrstring = descr.arg
            node_desc = descrstring

        chs = [ch for ch in module.i_children
                if ch.keyword in statements.data_definition_keywords]

        node  = {}
        children = []
        if len(chs) > 0:            
            children = print_children(chs, module, [node_name], [id], [], include_keys=ctx.opts.include_keys)

        rpcs = chs = [ch for ch in module.i_children if ch.keyword == 'rpc']
            
        rpc_node = {}
        rpc_children = []
        if len(rpcs) > 0:            
            rpc_children = print_children(rpcs, module, [node_name, f"{prefix}:rpcs"], [id, 2 if len(children) else 1], [], "RPC", include_keys=ctx.opts.include_keys)

        node["id"] = f"{id}"
        node["name"] = node_name
        node["description"] = node_desc
        node["path"] = f"{node_name}"
        node["schema"] = "module"
        node["prefix"] = prefix
        
        node = add_other_info(node, module)
        
        node["children"] = children
        
        if len(rpc_children) :
            rpc_node["id"] = f"{id}_2" if len(children) else f"{id}_1"
            rpc_node["name"] = f"{prefix}:rpcs"
            rpc_node["path"] = f"{node_name}/{prefix}:rpcs"
            rpc_node["schema"] = "module"
            rpc_node["prefix"] = prefix
            rpc_node["children"] = rpc_children
            node["children"] += [rpc_node]
        
        if len(children) :    
            nodes.append(node)

    modules = {"modules" : nodes}

    fd.write(json.dumps(modules))

def print_children(i_children, module, node_path, level_count, keys, additional_type=None, include_keys=False):
    children = []
    for id,ch in enumerate(i_children, start=1):
        child = print_node(ch, module, node_path, level_count+[id], keys, additional_type, include_keys=include_keys)
        if additional_type == "RPC" and type(child) == list :
            children.extend(child)
        else :
            children.append(child)
    return children

def add_other_info(node, module, debug=False) :
    other_substmts = {'real-time-change', 'presence', 'max-elements', 'revision', 'privilege',
            'auto-capital-convert', 'confirm-text', 'contact', 'namespace', 'prefix', 
            'mandatory', 'status', 'feature-id', 'reference-cell-type','when', 
            'min-elements', 'must', 'trouble-shooting', 'organization', 'import'}

    for substmt in module.substmts :
        extra = substmt.keyword if type(substmt.keyword) == str else substmt.keyword[-1]
        match = None
        for other_substmt in other_substmts :
            if extra.endswith(other_substmt) :
                match = other_substmt
                break
        if extra not in node and (substmt.keyword in other_substmts or match is not None) :
            if match == "feature-id" and substmt.arg == "N/A" :
                continue
            node[match] = substmt.arg
    
    return node

def print_node(item, module, node_path, level_count, keys, additional_type, include_keys=False):
    node = {}
    
    node_name = item.arg
    
    descr = item.search_one('description')
    node_desc = None
    if descr is not None:
        node_desc = ''.join([x for x in descr.arg if ord(x) < 128])
        
    node_config = False
    if item.i_config:
        node_config = True
    
    node_mandatory = None
    keyword = item.keyword

    if keyword  == 'choice' or (keyword == 'leaf' and not hasattr(item, 'i_is_key')) :
        m = item.search_one('mandatory')
        if m is None or m.arg == 'false':
            node_mandatory = False
        else:
            node_mandatory = True

    nkeys = []
    if keyword == 'list' and item.search_one('key') is not None:
        key_arg = item.search_one('key').arg
        for key in key_arg.split() :
            nkeys.append("/".join(node_path+[node_name, key]))
    
    idstring = "_".join([str(i) for i in level_count])
    
    debug = False

    node_type = {}
    node_type = resolve_node_type(item, node_type, debug=debug)

    children = []
    if hasattr(item, 'i_children'):
        chs = item.i_children
        children = print_children(chs, module, node_path+[node_name], level_count, keys+nkeys, additional_type, include_keys=include_keys)
    
    node["id"] = idstring
    node["name"] = node_name
    
    if node_desc is not None :
        node["description"] = node_desc

    node_path_str = "/".join(node_path+[node_name])
    if additional_type == "RPC" and "/input/" in node_path_str :
        node_path_str = node_path_str.replace("/input/", "/")
    if additional_type == "RPC" and "/output/" in node_path_str :
        node_path_str = node_path_str.replace("/output/", "/")
    node["path"] = node_path_str
    
    node["config"] = node_config
    
    if (keyword == 'leaf-list'or keyword == 'leaf') and node_mandatory is not None :
        node["mandatory"] = node_mandatory
    
    if keyword == 'leaf-list'or keyword == 'leaf' :
        if hasattr(item, 'i_is_key') :
            node["key"] = True
        else :
            node["key"] = False
            if len(keys) and include_keys:
                node["keys"] = keys
                # statements.get_xpath(item, prefix_to_module=True, with_keys=True).replace(":", "/").strip("/").replace("][", " & ")
    
    if keyword == 'leaf-list'or keyword == 'leaf' :
        node["type"] = node_type
    
    node["schema"] = keyword

    debug = False
    node = add_other_info(node, item, debug=debug)

    if len(children) :
        node["children"] = children
    else :
        if not (keyword == 'leaf-list' or keyword == 'leaf') :
            node["children"] = []
    if additional_type == "RPC" and node_name in ["input", "output"] :
        return children
    else :
        return node

def resolve_node_type(node, node_type, union=False, debug=False):
    max_value = {
        'int8' : 127,
        'int16' : 32767,
        'int32' : 2147483647,
        'int64' : 9223372036854775807,
        'uint8' : 255,
        'uint16' : 65535,
        'uint32' : 4294967295,
        'uint64' : 18446744073709551615,
        'decimal64' : 9223372036854775807
    }

    min_value = {
        'int8' : -128,
        'int16' : -32768,
        'int32' : -2147483648,
        'int64' : -9223372036854775808,
        'uint8' : 0,
        'uint16' : 0,
        'uint32' : 0,
        'uint64' : 0,
        'decimal64' : -9223372036854775808
    }
    
    def resolve_typedef(node) :
        nonlocal node_type
        if union :
            type_stmt = node
        else :
            type_stmt = node.search_one('type')
        node_type["name"] = node.arg
        if type_stmt is not None :
            prefix, name = util.split_identifier(type_stmt.arg)
            typedef = None
            if prefix is None or type_stmt.i_module.i_prefix == prefix:
                pmodule = node.i_module
                typedef = statements.search_typedef(type_stmt, name)
            else:
                err = []
                pmodule = util.prefix_to_module(type_stmt.i_module, prefix, type_stmt.pos, err)
                if pmodule is not None:
                    typedef = statements.search_typedef(pmodule, name)
            if typedef is not None:
                node_type = resolve_node_type(typedef, node_type, debug=debug)
            else :
                node_type["base"] = type_stmt.arg
    
    def create_bound(val, limit_map, keyword, is_decimal, fd):
        val = val.strip()
        if val and val != keyword:
            if is_decimal:
                val = str(float(val))
                if "." in val and len(val.split(".")[1]) < fd:
                    val += "0" * (fd - len(val.split(".")[1]))
            else:
                val = str(int(str(val).split(".")[0]))
        else:
            if node_type["base"] in limit_map:
                val = str(limit_map[node_type["base"]])
            if is_decimal and fd:
                val = val[:-fd] + "." + val[-fd:]
        return val

    def fill_node_type(node):
        nonlocal node_type
        if union :
            type_stmt = node
        else :
            type_stmt = node.search_one('type')
        if ":" not in node.arg :
            node_type["name"] = node.arg
        if type_stmt is not None:
            if type_stmt.arg == 'leafref':
                node_type = resolve_node_type(node.i_leafref.i_target_node, node_type)
                # p = type_stmt.search_one('path')
                # if p is not None:
                #     target = []
                #     up = []
                #     par = node
                #     rmod = None
                #     path_arg = p.arg
                #     for group in re.findall(r"\[[^]]*\]", path_arg) :
                #         path_arg = path_arg.replace(group, "")
                #     for name in path_arg.split('/'):
                #         prefix, name = util.split_identifier(name)
                #         if prefix is None or node.i_module.i_prefix == prefix:
                #             if name == ".." :
                #                 up.append(name)
                #             else :
                #                 if len(name) :
                #                     target.append(name)
                #         else :
                #             rind = p.arg.rindex(":")
                #             rmod = p.arg[:rind].rindex("/")
                #             rmod = p.arg[rmod+1:rind]
                #             break
                #     if rmod is not None :
                #         path_arg = p.arg
                #         modind = p.arg.index(rmod)
                #         path_arg = path_arg[modind:]
                #         path_arg = path_arg.replace(f"{rmod}:", "")
                #         for group in re.findall(r"\[[^]]*\]", path_arg) :
                #             path_arg = path_arg.replace(group, "")
                #         err = []
                #         pmodule = util.prefix_to_module(type_stmt.i_module, rmod, type_stmt.pos, err)
                #         par = pmodule
                #         target = path_arg.split("/")

                #     else :
                #         if len(up) :
                #             while up :
                #                 if par is not None and hasattr(par, "parent") and par.parent is not None :
                #                     par = par.parent
                #                     up.pop()
                #                 else :
                #                     break
                #         else :
                #             while par is not None and hasattr(par, "parent") and par.parent is not None :
                #                 par = par.parent

                #     child = par
                #     for sub in target :
                #         if child is not None and hasattr(child, 'i_children'):
                #             chs = child.i_children
                #             next = None
                #             for ch in chs:
                #                 if ch.arg == sub:
                #                     next = ch
                #                     break
                #             if next is not None :
                #                 child = next
                #                 continue
                #         if child is not None :
                #             for augment in child.search('augment'):
                #                 next = None
                #                 if augment is not None and hasattr(augment, 'i_children') :
                #                     for chs in augment.i_children :
                #                         if chs.arg == sub:
                #                             next = chs
                #                             break
                #                     if next is not None :
                #                         child = next
                #                         break

                #     if child is not None and child is not node :
                #         node_type = resolve_node_type(child, node_type)
                        
            elif node_type["base"] == 'enumeration':
                enums = []
                for enum in type_stmt.substmts:
                    enums.append(enum.arg)
                if len(enums) :
                    node_type["enum"] = enums
                
            elif node_type["base"] == 'union':
                uniontypes = type_stmt.search('type')
                node_sub_type = []
                for uniontype in uniontypes :
                    node_sub_type.append(resolve_node_type(uniontype, {"name" : uniontype.arg}, True, debug=False))
                if len(node_sub_type) :
                    node_type["type"] = node_sub_type

            elif node_type["base"] == 'decimal64' :
                fraction_digits = type_stmt.search_one('fraction-digits')
                if fraction_digits is not None :
                    node_type["fraction-digits"] = int(fraction_digits.arg)
                elif "fraction-digits" not in node_type :
                    node_type["fraction-digits"] = 1

            typerange = type_stmt.search_one('range')
            if typerange is not None:
                node_type["range"] = []
                is_decimal = "decimal" in node_type["base"]
                fd = node_type.get("fraction-digits", 0)

                for text in typerange.arg.split("|"):
                    text = text.replace("..", ",")
                    if "," in text:
                        mn, mx = text.split(",")
                    elif text:
                        mn = mx = text
                    else:
                        mn = mx = ""
                    mn = create_bound(mn, min_value, "min", is_decimal, fd)
                    mx = create_bound(mx, max_value, "max", is_decimal, fd)
                    node_type["range"].append({"min": mn, "max": mx, "text": f"{mn} .. {mx}"})
                # node_type["range"] = []
                # texts = typerange.arg
                # for text in texts.split("|") :
                #     range = {}
                #     text = text.replace("..",",")
                #     min = max = ""
                #     if "," in text :
                #         min, max = text.split(",")
                #     elif len(text) :
                #         min = max = text
                #     if "decimal" in node_type["base"] :
                #         if len(min.strip()) and min.strip() != "min" :
                #             min = str(float(min))
                #             if "." in min and len(min.split(".")[1]) < node_type["fraction-digits"] :
                #                 min+="0"*(node_type["fraction-digits"]-len(min.split(".")[1]))
                #         else :
                #             if node_type["base"] in min_value :
                #                 min = str(min_value[node_type["base"]])
                #             if "fraction-digits" in node_type :
                #                 min = min[:-1*node_type["fraction-digits"]] + "." + min[-1*node_type["fraction-digits"]:]
                #         if len(max.strip()) and max.strip() != "max" :
                #             max = str(float(max))
                #             if "." in max and len(max.split(".")[1]) < node_type["fraction-digits"] :
                #                 max+="0"*(node_type["fraction-digits"]-len(max.split(".")[1]))
                #         else :
                #             if node_type["base"] in max_value :
                #                 max = str(max_value[node_type["base"]])
                #             if "fraction-digits" in node_type :
                #                 max = max[:-1*node_type["fraction-digits"]] + "." + max[-1*node_type["fraction-digits"]:]
                #         range["min"] = min
                #         range["max"] = max
                #         range["text"] = f"{min} .. {max}"
                #         node_type["range"].append(range)
                #     else :
                #         if len(min.strip()) and min.strip() != "min" :
                #             min = str(int(str(min).split(".")[0]))
                #         else :
                #             if node_type["base"] in min_value :
                #                 min = str(min_value[node_type["base"]])
                #         if len(max.strip()) and max.strip() != "max" :
                #             max = str(int(str(max).split(".")[0]))
                #         else :
                #             if node_type["base"] in max_value :
                #                 max = str(max_value[node_type["base"]])
                #         range["min"] = min
                #         range["max"] = max
                #         range["text"] = f"{min} .. {max}"
                #         node_type["range"].append(range)
            
            length = type_stmt.search_one('length')
            if length is not None:
                node_type["length"] = [length.arg]

            patterns = type_stmt.search('pattern')
            if patterns is not None:
                for pattern in patterns :
                    if "pattern" not in node_type :
                        node_type["pattern"] = []
                    node_type["pattern"] += [pattern.arg]
            
        default = node.search_one('default')
        if default is not None :
            node_type["default"] = default.arg

        if "base" in node_type and node_type["base"] == 'string' :
            if "length" not in node_type :
                node_type["length"] = []
            if "pattern" not in node_type :
                node_type["pattern"] = []

        if "range" not in node_type and "base" in node_type:
            if node_type["base"] in min_value or node_type["base"] in max_value :
                node_type["range"] = []
                is_decimal = "decimal" in node_type["base"]
                fd = node_type.get("fraction-digits", 0)

                mn = create_bound("min", min_value, "min", is_decimal, fd)
                mx = create_bound("max", max_value, "max", is_decimal, fd)
                node_type["range"].append({"min": mn, "max": mx, "text": f"{mn} .. {mx}"})
                # node_type["range"] = []
                # range = {}
                # min = "min"
                # max = "max"
                # if "decimal" in node_type["base"] :
                #     if node_type["base"] in min_value :
                #         min = str(min_value[node_type["base"]])
                #     if "fraction-digits" in node_type :
                #         min = min[:-1*node_type["fraction-digits"]] + "." + min[-1*node_type["fraction-digits"]:]

                #     if node_type["base"] in max_value :
                #         max = str(max_value[node_type["base"]])
                #     if "fraction-digits" in node_type :
                #         max = max[:-1*node_type["fraction-digits"]] + "." + max[-1*node_type["fraction-digits"]:]

                #     range["min"] = min
                #     range["max"] = max
                #     range["text"] = f"{min} .. {max}"
                #     node_type["range"].append(range)
                # else :
                #     if node_type["base"] in min_value :
                #         min = str(min_value[node_type["base"]])

                #     if node_type["base"] in max_value :
                #         max = str(max_value[node_type["base"]])

                #     range["min"] = min
                #     range["max"] = max
                #     range["text"] = f"{min} .. {max}"
                #     node_type["range"].append(range)

    resolve_typedef(node)
    fill_node_type(node)

    return node_type