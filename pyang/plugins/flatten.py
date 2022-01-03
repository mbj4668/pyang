"""Copyright 2019 Cisco Systems
Flattens provided YANG module and outputs the schema nodes and some of their
properties in CSV format.


Arguments
---------
--flatten-no-header
    Do not emit the CSV header.
--flatten-keyword
    Output the keyword.
--flatten-type
    Output the top-level type. This will resolve to a module-prefixed type.
--flatten-primitive-type
    Output the primitive type. This resolves to a YANG type such as uint64.
--flatten-use-as-primitive
    Defines prefixes and specific types which will be used as primitive types. 
    Multiple may be used by adding this option multiple times.
--flatten-enumerations
    Output containing the enumeration options for the type with their 
    corresponding ordering values
--flatten-field-values-delimiter
    When using --flatten-enumerations or --flatten-expand-union-types the 
    character provided here will be used to separate the individual values
    within the field
--flatten-expand-union-types
    Shows the types and primitive types inside unions instead of 'union'. 
    Individual types are separated by --flatten-field-values-delimiter
--flatten-flag
    Output flag indicator. Based on data type/properties, outputs associated
    flag.
--flatten-description
    Output the description.
--flatten-keys
    Output whether the XPath is identified as a key.
--flatten-keys-in-xpath
    Output the XPath with keys in path.
--flatten-prefix-in-xpath
    Output the XPath with prefixes instead of modules.
--flatten-qualified-in-xpath
    Output the qualified XPath i.e. /module1:root/module1:node/module2:node/...
--flatten-qualified-module-and-prefix-path
    Output an XPath with both module and prefix i.e. /module1:prefix1:root/...
    This is NOT a colloquial syntax of XPath. Emitted separately.
--flatten-deviated
    Output deviated nodes in the schema as well.
--flatten-data-keywords
    Flatten all data keywords instead of only data definition keywords.
--flatten-filter-keyword <choice>
    Filter output to only desired keywords. Keywords specified are what will
    be displayed in output.
    Can be specified more than once.
--flatten-filter-primitive <choice>
    Filter output to only desired primitive types. Primitives specified are
    what will be displayed in output.
    Can be specified more than once.
--flatten-filter-flag <choice>
    Filter output to flag.
    ["ro", "rw", "w", "x", "n", "u"]
--flatten-csv-dialect <choice>
    CSV dialect for output.
    ["excel", "excel-tab", "unix"]
--flatten-ignore-no-primitive
    Ignore error if primitive is missing.
--flatten-status
    Output the status statement value.
--flatten-resolve-leafref
    Output the XPath of the leafref target.

Examples
--------
pyang -f flatten --flatten-no-header *.yang
    Just emit the XPaths.
pyang -f flatten --flatten-filter-primitive uint64
    --flatten-filter-primitive string *.yang
    Only output uint64 and string typed elements.
pyang -f flatten --flatten-filter-keyword container *.yang
    Only output containers.
"""

import optparse
import csv

from pyang import plugin
from pyang import statements, types


def pyang_plugin_init():
    plugin.register_plugin(FlattenPlugin())


class FlattenPlugin(plugin.PyangPlugin):
    def __init__(self):
        plugin.PyangPlugin.__init__(self, "flatten")
        csv.register_dialect('excel-semicolon', delimiter=';')

    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts["flatten"] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option(
                "--flatten-no-header",
                dest="flatten_no_header",
                action="store_true",
                help="Do not emit the CSV header.",
            ),
            optparse.make_option(
                "--flatten-keyword",
                dest="flatten_keyword",
                action="store_true",
                help="Output the keyword.",
            ),
            optparse.make_option(
                "--flatten-type",
                dest="flatten_type",
                action="store_true",
                help="Output the top-level type.",
            ),
            optparse.make_option(
                "--flatten-primitive-type",
                dest="flatten_primitive_type",
                action="store_true",
                help="Output the primitive type.",
            ),
            optparse.make_option(
                "--flatten-use-as-primitive",
                dest="flatten_use_as_primitive",
                action="append",
                default=[],
                help="Defines prefixes and specific types which will be used "+
                     "as primitive types. Multiple may be used by adding this "+
                     "option multiple times.",
            ),
            optparse.make_option(
                "--flatten-enumerations",
                dest="flatten_enumerations",
                action="store_true",
                help="Output containing the enumeration options for "+
                "the type with their corresponding ordering values.",
            ),
            optparse.make_option(
                "--flatten-field-values-delimiter",
                dest="flatten_field_values_delimiter",
                default="|",
                help="When using --flatten-primitive-enums or " +
                "--flatten-expand-union-types the character provided here " +
                "will be used to separate the individual values within the "+
                "field",
            ),
            optparse.make_option(
                "--flatten-expand-union-types",
                dest="flatten_expand_union",
                action="store_true",
                help="Shows the types and primitive types inside unions instead"
                " of 'union'. Individual types are separated by"
                " --flatten-field-values-delimiter",
            ),
            optparse.make_option(
                "--flatten-flag",
                dest="flatten_flag",
                action="store_true",
                help="Output flag property.",
            ),
            optparse.make_option(
                "--flatten-description",
                dest="flatten_description",
                action="store_true",
                help="Output the description.",
            ),
            optparse.make_option(
                "--flatten-keys",
                dest="flatten_keys",
                action="store_true",
                help="Output the key names if specified.",
            ),
            optparse.make_option(
                "--flatten-keys-in-xpath",
                dest="flatten_keys_in_xpath",
                action="store_true",
                help="Output the XPath with keys in path.",
            ),
            optparse.make_option(
                "--flatten-prefix-in-xpath",
                dest="flatten_prefix_in_xpath",
                action="store_true",
                help="Output the XPath with prefixes instead of modules.",
            ),
            optparse.make_option(
                "--flatten-prefix-in-types",
                dest="flatten_prefix_in_types",
                action="store_true",
                help="When the output is a qualified type use prefix to qualify",
            ),
            optparse.make_option(
                "--flatten-qualified-in-xpath",
                dest="flatten_qualified_in_xpath",
                action="store_true",
                help="Output the XPath with qualified in path /module1:root/module1:node/module2:node/...",
            ),
            optparse.make_option(
                "--flatten-qualified-module-and-prefix-path",
                dest="flatten_qualified_module_and_prefix_path",
                action="store_true",
                help="Output an XPath with both module and prefix i.e. /module1:prefix1:root/...",
            ),
            optparse.make_option(
                "--flatten-deviated",
                dest="flatten_deviated",
                action="store_true",
                help="Output deviated nodes.",
            ),
            optparse.make_option(
                "--flatten-data-keywords",
                dest="flatten_data_keywords",
                action="store_true",
                help="Flatten all data keywords instead of only"
                "data definition keywords.",
            ),
            optparse.make_option(
                "--flatten-filter-keyword",
                dest="flatten_filter_keyword",
                help="Filter output to only desired keywords.",
                action="append",
                choices=list(statements.data_keywords),
            ),
            optparse.make_option(
                "--flatten-filter-primitive",
                dest="flatten_filter_primitive",
                help="Filter output to only desired primitive types.",
                action="append",
                choices=list(types.yang_type_specs.keys()),
            ),
            optparse.make_option(
                "--flatten-filter-flag",
                dest="flatten_filter_flag",
                help="Filter output to flags.",
                choices=["ro", "rw", "w", "x", "n", "u"],
            ),
            optparse.make_option(
                "--flatten-csv-dialect",
                dest="flatten_csv_dialect",
                default="excel",
                help="CSV dialect for output.",
                choices=["excel", "excel-tab", "excel-semicolon", "unix"],
            ),
            optparse.make_option(
                "--flatten-ignore-no-primitive",
                dest="ignore_no_primitive",
                help="Ignore error if primitive is missing.",
                action="store_true",
            ),
            optparse.make_option(
                "--flatten-status",
                dest="flatten_status",
                help="Output the status statement value.",
                action="store_true",
            ),
            optparse.make_option(
                "--flatten-resolve-leafref",
                dest="flatten_resolve_leafref",
                help="Output the XPath of the leafref target.",
                action="store_true",
            ),
        ]
        g = optparser.add_option_group("Flatten output specific options")
        g.add_options(optlist)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False
        self.__field_names = ["xpath"]
        if ctx.opts.flatten_keyword:
            self.__field_names.append("keyword")
        if ctx.opts.flatten_primitive_type:
            self.__field_names.append("primitive_type")
        if ctx.opts.flatten_enumerations:
            self.__field_names.append("enumerations")
        if ctx.opts.flatten_flag:
            self.__field_names.append("flag")
        if ctx.opts.flatten_type:
            self.__field_names.append("type")
        if ctx.opts.flatten_description:
            self.__field_names.append("description")
        if ctx.opts.flatten_keys:
            self.__field_names.append("key")
        if ctx.opts.flatten_deviated:
            self.__field_names.append("deviated")
        if ctx.opts.flatten_qualified_module_and_prefix_path:
            self.__field_names.append("mod_prefix_path")
        if ctx.opts.flatten_status:
            self.__field_names.append("status")
        if ctx.opts.flatten_resolve_leafref:
            self.__field_names.append("resolved_leafref")
        self.__field_names_set = set(self.__field_names)
        # Slipping input and output into data keywords
        # rpc input/output may have children - we want to traverse them.
        self.__keywords = (
            statements.data_keywords + ["input", "output"]
            if ctx.opts.flatten_data_keywords
            else statements.data_definition_keywords
        )

    def emit(self, ctx, modules, fd):
        output_writer = csv.DictWriter(
            fd,
            fieldnames=self.__field_names,
            dialect=ctx.opts.flatten_csv_dialect,
        )
        if not ctx.opts.flatten_no_header:
            output_writer.writeheader()
        for module in sorted(modules, key=lambda m: m.arg):
            self.output_module(ctx, module, output_writer)

    def output_module(
        self,
        ctx,
        module,
        output_writer,
        parent_deviated=False,
        override_flag=None,
        known_keys=None,
    ):
        module_children = [
            child
            for child in getattr(module, "i_children", [])
            if child.keyword in self.__keywords
        ]
        if ctx.opts.flatten_deviated:
            deviated_module_children = [
                child
                for child in getattr(module, "i_not_supported", [])
                if child.keyword in self.__keywords
            ]
            module_children = module_children + deviated_module_children
        module_children = sorted(
            module_children,
            key=lambda child: statements.get_xpath(
                child,
                prefix_to_module=(not ctx.opts.flatten_prefix_in_xpath),
                qualified=ctx.opts.flatten_qualified_in_xpath,
            ),
        )
        for child in module_children:
            self.output_child(
                ctx,
                child,
                output_writer,
                parent_deviated,
                override_flag,
                known_keys,
            )

    def output_child(
        self,
        ctx,
        child,
        output_writer,
        parent_deviated=False,
        override_flag=None,
        known_keys=None,
    ):
        deviated = (
            getattr(child, "i_this_not_supported", False) or parent_deviated
        )
        # Keys map to self.__field_names for CSV output
        output_content = {
            "xpath": statements.get_xpath(
                child,
                prefix_to_module=(not ctx.opts.flatten_prefix_in_xpath),
                qualified=ctx.opts.flatten_qualified_in_xpath,
                with_keys=ctx.opts.flatten_keys_in_xpath,
            )
        }
        delim = ctx.opts.flatten_field_values_delimiter
        expand_unions = ctx.opts.flatten_expand_union
        enum_list = []
        leafref_list = []
        # Sometimes we won't have the full set of YANG models...
        # Handle whether to error out or just set as "nil" for primitive type
        # When the primitive type is an enumeration returns both type and 
        # enumeration options. Else the options are None
        try:
            primitive_type_obj = statements.get_primitive_type(
                child.search_one("type"), ctx.opts.flatten_use_as_primitive,
                ctx.opts.flatten_prefix_in_types ) or None
            primitive_type = statements.get_qualified_type(primitive_type_obj,
                                ctx.opts.flatten_prefix_in_types)
            # flatten_use_as_primitive prevents the resolution of enumeration
            # values under the types for those prefixes. May need to make an
            # extra call to get_primitive_type to get them or return the real
            # primitive type as well.
            
            statements.get_enum_values(primitive_type_obj,enum_list)
            if expand_unions and primitive_type == 'union':
                primitive_types = []
                statements.get_union_types(primitive_type_obj,enum_list, 
                            leafref_list, delim, primitive_types, True,
                            ctx.opts.flatten_use_as_primitive,
                            ctx.opts.flatten_prefix_in_types )
                primitive_types.sort()
                primitive_type = delim.join(primitive_types)
        except Exception as e:
            if ctx.opts.ignore_no_primitive:
                primitive_type = ''
            else:
                raise e
        # To handle inputs and outputs we're going to have an override flag.
        # input children should flag as w all the way through.
        flag, override_flag = (
            (override_flag, override_flag)
            if override_flag
            else self.get_flag(child)
        )
        child_keys = set(statements.get_keys(child))
        # Set the output content based on the options specified
        if ctx.opts.flatten_keyword:
            output_content["keyword"] = child.keyword
        if ctx.opts.flatten_type:
            output_content["type"] = statements.get_qualified_type(child.search_one('type'),
                            ctx.opts.flatten_prefix_in_types)  or ''
            if ( output_content["type"] == 'union' and 
                    ctx.opts.flatten_expand_union):
                union_types = []
                statements.get_union_types(child.search_one('type'), [], [], delim, 
                                union_types, False, ctx.opts.flatten_use_as_primitive,
                                ctx.opts.flatten_prefix_in_types )
                union_types.sort()
                output_content["type"] = delim.join(union_types)
        if ctx.opts.flatten_primitive_type:
            output_content["primitive_type"] = primitive_type
        if ctx.opts.flatten_enumerations:
            output_content["enumerations"] =  delim.join(enum_list) 
        if ctx.opts.flatten_flag:
            output_content["flag"] = flag
        if ctx.opts.flatten_description:
            output_content["description"] = statements.get_description(child)
        if ctx.opts.flatten_keys:
            if not known_keys:
                output_content["key"] = None
            else:
                child_name = child.arg
                output_content["key"] = (
                    "key" if child_name in known_keys else None
                )
        if ctx.opts.flatten_deviated:
            output_content["deviated"] = "deviated" if deviated else "present"
        if ctx.opts.flatten_qualified_module_and_prefix_path:
            output_content["mod_prefix_path"] = self.get_mod_prefix_path(
                child, ctx.opts.flatten_keys_in_xpath
            )
        if ctx.opts.flatten_status:
            # If no status is specified, the default is "current".
            status = "current"
            status_statement = child.search_one("status")
            if status_statement is not None:
                status = status_statement.arg
            output_content["status"] = status
        if ctx.opts.flatten_resolve_leafref:
            if primitive_type == "leafref":
                
                output_content["resolved_leafref"] = statements.get_xpath(
                    child.i_leafref.i_target_node,
                    prefix_to_module=(not ctx.opts.flatten_prefix_in_xpath),
                    qualified=ctx.opts.flatten_qualified_in_xpath,
                    with_keys=ctx.opts.flatten_keys_in_xpath,
                )
            else:
# TODO handle all the settings above for this case. The problem with unions not having an i_target_node needs to be fixed first

                output_content["resolved_leafref"] = delim.join(leafref_list)
        if set(output_content.keys()) != self.__field_names_set:
            raise Exception("Output keys do not match CSV field names!")
        # Filters are specified as a positive in the command line arguments
        # In this case we're negating compared to what we want to output
        # Final statement: Always ignore input/output, children will be printed.
        output_filters = set(
            [
                ctx.opts.flatten_filter_keyword
                and child.keyword not in ctx.opts.flatten_filter_keyword,
                ctx.opts.flatten_filter_primitive
                and primitive_type not in ctx.opts.flatten_filter_primitive,
                ctx.opts.flatten_filter_flag
                and flag != ctx.opts.flatten_filter_flag,
                child.keyword in {"input", "output"},
            ]
        )
        if not any(output_filters):
            # We want to traverse the entire tree for output
            # Simply don't output what we don't want, don't stop processing
            output_writer.writerow(output_content)
        if hasattr(child, "i_children"):
            self.output_module(
                ctx, child, output_writer, deviated, override_flag, child_keys
            )

    def get_flag(self, node, parent_flag=None):
        """Pulled from tree plugin.
        Removed mode argument, directly derive from keyword.
        Returns the current flag, and override flag if necessary.
        TODO: Determine no mode arg affect. Might be invalid.
        TODO: Determine default flag. "ro"?
        """
        if node.keyword == "input":
            return "w", "w"
        elif node.keyword in ("rpc", "action", ("tailf-common", "action")):
            return "x", None
        elif node.keyword == "notification":
            return "n", None
        elif node.keyword == "uses":
            return "u", None
        elif node.i_config == True:
            return "rw", None
        elif node.i_config == False or node.keyword == "notification":
            return "ro", None
        elif node.keyword == "output":
            return "ro", "ro"
        else:
            # Default to ro, clear up with Martin
            # raise Exception("Unable to determine flag for %s!" %
            #    statements.get_xpath(node, prefix_to_module=True))
            return "ro", None

    def get_mod_prefix_path(self, stmt, with_keys=False):
        """Duplicate statements.mk_path_str,
        but output module and prefix both in path.
        """
        resolved_names = statements.mk_path_list(stmt)
        xpath_elements = []
        for index, resolved_name in enumerate(resolved_names):
            module_name, prefix, node_name, node_keys = resolved_name
            xpath_element = "%s:%s:%s" % (module_name, prefix, node_name)
            if with_keys and node_keys:
                for node_key in node_keys:
                    xpath_element = "%s[%s]" % (xpath_element, node_key)
            xpath_elements.append(xpath_element)
        return "/%s" % "/".join(xpath_elements)
