"""opc_ua output plugin
1) Invoke with:
>pyang -f opc_ua <file.yang> > <file.uml>
"""

from pyang import error
from pyang import plugin


def pyang_plugin_init():
    plugin.register_plugin(OPCUAPlugin())


yang_to_opcua_data_type = {
    "binary": "ByteString",
    "bits": "BitFieldMaskDataType",
    "boolean": "Boolean",
    "decimal64": "Double",
    "empty": "BaseObjectType",
    "enumeration": "EnumValueType",
    "int8": "SByte",
    "int16": "Int16",
    "int32": "Int32",
    "int64": "Int64",
    "string": "String",
    "uint8": "Byte",
    "uint16": "UInt16",
    "uint32": "UInt32",
    "uint64": "UInt64",
    "date-and-time": "DateTime",
    "union": "Union"
}


class OPCUAPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['opc_ua'] = self

    def pre_validate(self, ctx, modules):
        module = modules[0]
        self.mods = [module.arg] + [i.arg for i in module.search('include')]

    def emit(self, ctx, modules, fd):
        for epos, etag, eargs in ctx.errors:
            if ((epos.top is None or epos.top.arg in self.mods) and
                    error.is_error(error.err_level(etag))):
                self.fatal("%s contains errors" % epos.top.arg)

        opc_ua_doc = OPCUAEmitter(ctx)
        opc_ua_doc.emit(modules, fd)

    def fatal(self, exitCode=1):
        raise error.EmitError(self, exitCode)


def convert_to_camel_case(text):
    return ''.join(word.capitalize() for word in text.split('-'))


class OPCUAEmitter:
    def __init__(self, ctx):
        self._ctx = ctx

    def emit(self, modules, fd):
        for module in modules:
            self.emit_module_header(module, fd)
            for s in module.substmts:
                self.emit_stmt(module, s, fd)
            self.emit_uml_footer(module, fd)

            # print('!!!!!!!!!! Substatements !!!!!!!!!')
            # for s in module.substmts:
            #     print(f'Statemet {s}')
            #     if s.keyword == 'container':
            #         print('!!!!!!!!!!! Substatements !!!!!!!!!!')
            #         for substmt in s.substmts:
            #             print(f'sub - {substmt}')
            #             if substmt.keyword == 'leaf':
            #                 val = substmt.search_one('type')
            #                 print(f'Type of substatement - {val}')
            #                 print(f'Value of substatement - {val.arg}')

    def emit_stmt(self, mod, stmt, fd):
        if stmt.keyword == 'container':
            self.emit_container(stmt, fd, 4)

        elif stmt.keyword == 'leaf' or stmt.keyword == 'leaf-list':
            self.emit_leaf(stmt, fd, 4)

        elif stmt.keyword == 'typedef':
            self.emit_typedef(stmt, fd, 4)

        elif stmt.keyword == 'rpc':
            self.emit_rpc(stmt, fd, 4)

        elif stmt.keyword == 'grouping':
            self.emit_grouping(stmt, fd, 4)

        elif stmt.keyword == 'list':
            self.emit_list(stmt, fd, 4)

    def emit_child_stmt(self, parent, node, fd, num_spaces):
        if node.keyword == 'leaf' or node.keyword == 'leaf-list':
            if parent.keyword == 'rpc':
                self.emit_leaf(node, fd, num_spaces + 2, is_rpc=True)
            else:
                self.emit_leaf(node, fd, num_spaces + 2, is_rpc=False)

        elif node.keyword == 'container':
            self.emit_container(node, fd, num_spaces + 2)

        elif node.keyword == 'rpc':
            self.emit_rpc(node, fd, num_spaces + 2)

        elif node.keyword == 'uses':
            parent_name = node.arg
            self.emit_uses(node, fd, num_spaces + 2, parent_name)

        elif node.keyword == 'list':
            self.emit_list(node, fd, num_spaces + 2)

    def emit_module_header(self, module, fd):
        namespace = 'http://opcfoundation.org/UA/default/'
        namespace_name = ''
        version = '1.0'
        prefix = ''
        if module.search_one('namespace') is not None:
            namespace = module.search_one('namespace').arg
        if module.search_one('revision') is not None:
            version = module.search_one('revision').arg
        if module.search_one('prefix') is not None:
            prefix = module.search_one('prefix').arg

        if len(namespace.split("/")) > 1:
            namespace_name = namespace.split("/")[-2]
        else:
            namespace_name = namespace.split(":")[-1]
        fd.write('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<opc:ModelDesign\n'
                 '    xmlns:uax="http://opcfoundation.org/UA/2008/02/Types.xsd"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    xmlns:ua="http://opcfoundation.org/UA/"\n'
                 '    xmlns:opc="http://opcfoundation.org/UA/ModelDesign.xsd"\n'
                 '    xmlns:xsd="http://www.w3.org/2001/XMLSchema"\n'
                 '    xmlns=\"%s\"\n'
                 '    TargetNamespace=\"%s\"\n'
                 '    TargetVersion=\"%s\">\n\n' % (namespace, namespace, version))

        fd.write('    <opc:Namespaces>\n'
                 '        <opc:Namespace Name=\"%s\" Prefix=\"%s\" XmlPrefix=\"%s\">%s</opc:Namespace>\n'
                 '    </opc:Namespaces>\n\n' % (namespace_name, prefix, prefix, namespace))

    def emit_uml_footer(self, module, fd):
        fd.write('</opc:ModelDesign>')

    def emit_container(self, node, fd, num_space):
        spaces = ' ' * num_space
        container_name = node.arg
        fd.write(
            f'{spaces}<opc:ObjectType SymbolicName="{convert_to_camel_case(container_name)}Type" BaseType="ua:BaseObjectType">\n'
            f'{" " * (num_space + 2)}<opc:Children>\n')

        for s in node.substmts:
            self.emit_child_stmt(node, s, fd, num_space + 4)

        fd.write(f'{" " * (num_space + 2)}</opc:Children>\n'
                 f'{spaces}</opc:ObjectType>\n\n'
                 f'{spaces}<opc:Object SymbolicName="{convert_to_camel_case(container_name)}" TypeDefinition="{convert_to_camel_case(container_name)}Type">\n'
                 f'{" " * (num_space + 2)}<opc:Children>\n'
                 f'{" " * (num_space + 4)}<opc:References>\n'
                 f'{" " * (num_space + 6)}<opc:Reference IsInverse="true">\n'
                 f'{" " * (num_space + 8)}<opc:ReferenceType>SignalTo</opc:ReferenceType>\n'
                 f'{" " * (num_space + 6)}</opc:Reference>\n'
                 f'{" " * (num_space + 4)}</opc:References>\n'
                 f'{" " * (num_space + 2)}</opc:Children>\n'
                 f'{spaces}</opc:Object>\n')

    def emit_leaf(self, node, fd, num_space, is_rpc=False):
        spaces = ' ' * num_space
        leaf_name = node.arg
        leaf_type = yang_to_opcua_data_type.get(node.search_one('type').arg, 'Unknown OPC UA data type')
        leaf_default_value = None
        leaf_description = None
        leaf_property = 'Property'

        if node.search_one('config') is not None and node.search_one('config').arg == 'true':
            leaf_property = 'Variable'

        if is_rpc:
            leaf_property = 'Argument'

        if node.search_one('default') is not None:
            leaf_default_value = node.search_one('default').arg

        if node.search_one('description') is not None:
            leaf_description = node.search_one('description').arg

        fd.write(
            f'{spaces}<opc:{leaf_property} SymbolicName="{convert_to_camel_case(leaf_name)}" DataType="{leaf_type}" AccessLevel="Read"> \n')
        if leaf_default_value is not None:
            fd.write(
                f'{spaces}  <opc:DefaultValue> <uax:{leaf_type}>{leaf_default_value}</uax:{leaf_type}> </opc:DefaultValue>\n')
        if leaf_description is not None:
            fd.write(f'{spaces}  <opc:Description>{leaf_description}</opc:Description>\n')
        fd.write(f'{spaces}</opc:{leaf_property}>\n')

    def emit_rpc(self, node, fd, num_space):
        spaces = ' ' * num_space
        rpc_name = node.arg
        fd.write(
            f'\n{spaces}<opc:Method SymbolicName="{convert_to_camel_case(rpc_name)}" ModellingRule="Mandatory">\n')

        for stmt in node.substmts:
            if stmt.keyword == 'input':
                for s in stmt.substmts:
                    fd.write(f'{" " * (num_space + 2)}<opc:InputArguments>\n')
                    self.emit_child_stmt(node, s, fd, num_space + 4)
                    fd.write(f'{" " * (num_space + 2)}</opc:InputArguments>\n')

            elif stmt.keyword == 'output':
                for s in stmt.substmts:
                    fd.write(f'{" " * (num_space + 2)}<opc:OutputArguments>\n')
                    self.emit_child_stmt(node, s, fd, num_space + 4)
                    fd.write(f'{" " * (num_space + 2)}</opc:OutputArguments>\n')

        fd.write(f'{spaces}</opc:Method>\n\n')

    def emit_typedef(self, node, fd, num_space):
        spaces = ' ' * num_space
        typedef_name = node.arg
        typedef_default_value = None
        typedef_description = None
        typedef_type = None

        if node.search_one('default') is not None:
            typedef_default_value = node.search_one('default').arg

        if node.search_one('description') is not None:
            typedef_description = node.search_one('description').arg

        if node.search_one('type') is not None:
            if node.search_one('type').arg == 'enumeration':
                typedef_type = 'Enumeration'
                fd.write(
                    f'{spaces}<opc:DataType SymbolicName="{convert_to_camel_case(typedef_name)}Type" BaseType="ua:{typedef_type}"> \n'
                    f'{spaces}  <opc:Fields>\n')

                for stmt in node.substmts:
                    enum_names = stmt.search('enum')
                    k = 0
                    for s in stmt.substmts:
                        fd.write(f'{spaces}    <opc:Field Name="{enum_names[k]}" ')
                        k += 1
                        if s.search_one('value') is not None:
                            value = s.search_one('value').arg
                            fd.write(f' Identifier="{value}" ')
                        if s.search_one('description') is not None:
                            desc = s.search_one('description').arg
                            fd.write(f' Description="{desc}" ')
                        fd.write('/>\n')
                fd.write(f'{spaces}  </opc:Fields>\n'
                         f'{spaces}</opc:DataType>\n')
                return

            else:
                typedef_type = yang_to_opcua_data_type.get(node.search_one('type').arg, "Unknown OpcUa data type")
                if typedef_type != 'Unknown OpcUa data type':
                    yang_to_opcua_data_type[typedef_type] = typedef_type

        fd.write(
            f'{spaces}<opc:DataType SymbolicName="{convert_to_camel_case(typedef_name)}" BaseType="ua:{typedef_type}"> \n')
        if typedef_default_value is not None:
            fd.write(
                f'{spaces}  <opc:DefaultValue> <uax:{typedef_type}>{typedef_default_value}</uax:{typedef_type}> </opc:DefaultValue>\n')
        if typedef_description is not None:
            fd.write(f'{spaces}  <opc:Description>{typedef_description}</opc:Description>\n')
        fd.write(f'{spaces}</opc:DataType>\n')

    def emit_uses(self, node, fd, num_space, parent_name):
        spaces = ' ' * num_space
        grouping_name = node.arg
        fd.write(
            f'{spaces}<opc:Object SymbolicName="{convert_to_camel_case(parent_name)}" TypeDefinition="{convert_to_camel_case(grouping_name)}Type">\n'
            f'{spaces}</opc:Object>\n')

    def emit_list(self, node, fd, num_space):
        spaces = ' ' * num_space
        list_name = node.arg

        fd.write(
            f'{spaces}<opc:ObjectType SymbolicName="{convert_to_camel_case(list_name)}EntryType" BaseType="ua:BaseObjectType">\n'
            f'{" " * (num_space + 2)}<opc:Children>\n')

        for s in node.substmts:
            self.emit_child_stmt(node, s, fd, num_space + 4)

        fd.write(f'{" " * (num_space + 2)}</opc:Children>\n'
                 f'{spaces}</opc:ObjectType>\n'
                 f'{spaces}<opc:ObjectType SymbolicName="{convert_to_camel_case(list_name)}Type" BaseType="ua:BaseObjectType">\n'
                 f'{" " * (num_space + 2)}<opc:Children>\n'
                 f'{" " * (num_space + 4)}<opc:ReferenceType TypeDefinition="{convert_to_camel_case(list_name)}EntryType"/>\n'
                 f'{" " * (num_space + 2)}</opc:Children>\n'
                 f'{spaces}</opc:ObjectType>\n')

    def emit_grouping(self, node, fd, num_space):
        spaces = ' ' * num_space
        grouping_name = node.arg
        fd.write(
            f'{spaces}<opc:ObjectType SymbolicName="{convert_to_camel_case(grouping_name)}Type" BaseType="ua:BaseObjectType">\n'
            f'{" " * (num_space + 2)}<opc:Children>\n')

        for s in node.substmts:
            self.emit_child_stmt(node, s, fd, num_space + 2)

        fd.write(f'{" " * (num_space + 2)}</opc:Children>\n'
                 f'{spaces}</opc:ObjectType>\n\n')
