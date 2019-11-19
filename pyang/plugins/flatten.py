"""Flattens provided YANG schema and outputs XPath attributes as CSV.
"""

import optparse
import sys
import csv
import pdb

from pyang import plugin
from pyang import statements


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
                "--flatten-type",
                dest="flatten_type",
                action="store_true",
                help="Output the type.",
            ),
            optparse.make_option(
                "--flatten-permission",
                dest="flatten_permission",
                action="store_true",
                help="Output config property.",
            ),
            optparse.make_option(
                "--flatten-description",
                dest="flatten_description",
                action="store_true",
                help="Output the description.",
            ),
            optparse.make_option(
                "--flatten-filter-leaves",
                dest="flatten_filter_leaves",
                action="store_true",
                help="Output filter to only leaves.",
            ),
            optparse.make_option(
                "--flatten-filter-permission",
                dest="flatten_filter_permission",
                help="Output filter to ro or rw.",
            ),
            optparse.make_option(
                "--flatten-csv-dialect",
                dest="flatten_csv_dialect",
                default="excel",
                help="CSV dialect for output.",
            ),
        ]
        g = optparser.add_option_group("Flatten output specific options")
        g.add_options(optlist)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        output_writer = csv.writer(fd, dialect=ctx.opts.flatten_csv_dialect)
        for module in modules:
            self.output_module(ctx, module, output_writer)

    def output_module(self, ctx, module, output_writer):
        if not hasattr(module, "i_children"):
            return
        module_children = (
            child
            for child in module.i_children
            if child.keyword in statements.data_definition_keywords
        )
        for child in module_children:
            xpath = statements.get_xpath(child, prefix_to_module=True)
            primitive_type = statements.get_primitive_type(child)
            permission = "rw" if getattr(child, "i_config", False) else "ro"
            output_content = [xpath]
            if ctx.opts.flatten_type:
                output_content.append(primitive_type)
            if ctx.opts.flatten_permission:
                output_content.append(permission)
            if ctx.opts.flatten_description:
                output_content.append(statements.get_description(child))
            if not any(
                [
                    ctx.opts.flatten_filter_leaves and not primitive_type,
                    ctx.opts.flatten_filter_permission
                    and permission != ctx.opts.flatten_filter_permission,
                ]
            ):
                output_writer.writerow(output_content)
            if hasattr(child, "i_children"):
                self.output_module(ctx, child, output_writer)
