"""Copyright 2019 Cisco Systems
Flattens provided YANG schema and outputs XPath attributes in CSV format.

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
--flatten-flag
    Output flag indicator. Based on data type/properties, outputs associated flag.
--flatten-description
    Output the description.
--flatten-data-keywords
    Flatten all data keywords instead of only data definition keywords.
--flatten-filter-keyword <choice>
    Filter output to only desired keywords. Keywords specified are what will be displayed in output.
    Can be specified more than once.
--flatten-filter-primitive <choice>
    Filter output to only desired primitive types. Primitives specified are what will be displayed in output.
    Can be specified more than once.
--flatten-filter-flag <choice>
    Filter output to flag.
    ["ro", "rw", "w", "x", "n", "u"]
--flatten-csv-dialect <choice>
    CSV dialect for output.
    ["excel", "excel-tab", "unix"]
--ignore-no-primitive
    Ignore error if primitive is missing.

Examples
--------
pyang -f flatten --flatten-no-header *.yang
    Just emit the XPaths.
pyang -f flatten --flatten-filter-primitive uint64 --flatten-filter-primitive string *.yang
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
                "--flatten-deviated",
                dest="flatten_deviated",
                action="store_true",
                help="Output deviated nodes.",
            ),
            optparse.make_option(
                "--flatten-data-keywords",
                dest="flatten_data_keywords",
                action="store_true",
                help="Flatten all data keywords instead of only data definition keywords.",
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
                choices=["excel", "excel-tab", "unix"],
            ),
            optparse.make_option(
                "--ignore-no-primitive",
                dest="ignore_no_primitive",
                help="Ignore error if primitive is missing.",
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
        if ctx.opts.flatten_flag:
            self.__field_names.append("flag")
        if ctx.opts.flatten_type:
            self.__field_names.append("type")
        if ctx.opts.flatten_description:
            self.__field_names.append("description")
        if ctx.opts.flatten_deviated:
            self.__field_names.append("deviated")
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
            fd, fieldnames=self.__field_names, dialect=ctx.opts.flatten_csv_dialect
        )
        if not ctx.opts.flatten_no_header:
            output_writer.writeheader()
        for module in modules:
            self.output_module(ctx, module, output_writer)

    def output_module(
        self, ctx, module, output_writer, parent_deviated=False, override_flag=None
    ):
        module_children = (
            child
            for child in getattr(module, "i_children", [])
            if child.keyword in self.__keywords
        )
        for child in module_children:
            self.output_child(ctx, child, output_writer, parent_deviated, override_flag)
        # If we are flattening deviations, need to traverse deviated tree as well.
        if ctx.opts.flatten_deviated:
            deviated_module_children = (
                child
                for child in getattr(module, "i_not_supported", [])
                if child.keyword in self.__keywords
            )
            for child in deviated_module_children:
                self.output_child(
                    ctx, child, output_writer, parent_deviated, override_flag
                )

    def output_child(
        self, ctx, child, output_writer, parent_deviated=False, override_flag=None
    ):
        deviated = getattr(child, "i_this_not_supported", False) or parent_deviated
        # Keys map to self.__field_names for CSV output
        output_content = {"xpath": statements.get_xpath(child, prefix_to_module=True)}
        # Sometimes we won't have the full set of YANG models...
        # Handle whether to error out or just set as "nil" for primitive type
        try:
            primitive_type = statements.get_primitive_type(child) or "nil"
        except Exception as e:
            if ctx.opts.ignore_no_primitive:
                primitive_type = "nil"
            else:
                raise e
        # To handle inputs and outputs we're going to have an override flag.
        # input children should flag as w all the way through.
        flag, override_flag = (
            (override_flag, override_flag) if override_flag else self.get_flag(child)
        )
        # Set the output content based on the options specified
        if ctx.opts.flatten_keyword:
            output_content["keyword"] = child.keyword
        if ctx.opts.flatten_type:
            output_content["type"] = statements.get_qualified_type(child) or "nil"
        if ctx.opts.flatten_primitive_type:
            output_content["primitive_type"] = primitive_type
        if ctx.opts.flatten_flag:
            output_content["flag"] = flag
        if ctx.opts.flatten_description:
            output_content["description"] = statements.get_description(child)
        if ctx.opts.flatten_deviated:
            output_content["deviated"] = "deviated" if deviated else "present"
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
                ctx.opts.flatten_filter_flag and flag != ctx.opts.flatten_filter_flag,
                child.keyword in {"input", "output"},
            ]
        )
        if not any(output_filters):
            # We want to traverse the entire tree for output
            # Simply don't output what we don't want, don't stop processing
            output_writer.writerow(output_content)
        if hasattr(child, "i_children"):
            self.output_module(ctx, child, output_writer, deviated, override_flag)

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
            # raise Exception("Unable to determine flag for %s!" % statements.get_xpath(node, prefix_to_module=True))
            return "ro", None
