"""YANG edit plugin
Edit YANG (controlled by options):
* Add import/input revision-date statements
* Update latest revision statement to last Git commit date
* <more>
"""

import copy
import optparse
import re
import subprocess
import sys

from pyang import error
from pyang import plugin
from pyang import statements
from pyang.translators import yang

# XXX should this really be a translator rather than plugin?

def pyang_plugin_init():
    plugin.register_plugin(YANGEditPlugin())

def check_date(option, opt, value):
    if not re.match("^\d{4}-\d{2}-\d{2}$", value):
        raise optparse.OptionValueError(
            "option %s: invalid yyyy-mm-dd date: %s" % (opt, value))
    return value

class YANGEditOption(optparse.Option):
    TYPES = optparse.Option.TYPES + ("date",)
    TYPE_CHECKER = copy.copy(optparse.Option.TYPE_CHECKER)
    TYPE_CHECKER["date"] = check_date

class YANGEditPlugin(yang.YANGPlugin):
    # XXX generic code should check all option groups for settings not
    #     associated with the current format
    def add_opts(self, optparser):
        optlist = [
            # set header info
            YANGEditOption("--yang-edit-yang-version",
                           dest="yang_edit_yang_version",
                           metavar="VERSION",
                           help="Set YANG version to the supplied value"),

            # set imported/included module/submodule revision dates
            YANGEditOption("--yang-edit-update-import-dates",
                           dest="yang_edit_update_import_dates",
                           default=False,
                           action="store_true",
                           help="Set import/include revision-date "
                           "statements to match imported/included "
                           "modules/submodules"),

            # set meta info
            YANGEditOption("--yang-edit-organization",
                           dest="yang_edit_organization",
                           metavar="ORGANIZATION",
                           help="Set module/submodule organization "
                           "to the supplied value"),
            YANGEditOption("--yang-edit-contact",
                           dest="yang_edit_contact",
                           metavar="CONTACT",
                           help="Set module/submodule contact "
                           "to the supplied value"),
            YANGEditOption("--yang-edit-description",
                           dest="yang_edit_description",
                           metavar="DESCRIPTION",
                           help="Set module/submodule description "
                           "to the supplied value"),

            # set revision info
            YANGEditOption("--yang-edit-revision-date",
                           dest="yang_edit_revision_date",
                           type="date",
                           metavar="DATE",
                           help="Set most recent revision date "
                           "to the supplied yyyy-mm-dd"),
            YANGEditOption("--yang-edit-revision-description",
                           dest="yang_edit_revision_description",
                           metavar="DESCRIPTION",
                           help="Set most recent revision description "
                           "to the supplied value"),
            YANGEditOption("--yang-edit-revision-reference",
                           dest="yang_edit_revision_reference",
                           metavar="REFERENCE",
                           help="Set most recent revision reference "
                           "to the supplied value"),
            ]
        g = optparser.add_option_group(
            "YANG edit specific options")
        g.add_options(optlist)

    def add_output_format(self, fmts):
        fmts["yang-edit"] = self
        # XXX this is a bit tricky; need this here in addition to in the
        #     base class; actually not, because change ctx.keep_comments
        #     directly (see below)
        self.handle_comments = True

    # XXX is this acceptable, or should there be direct base class support?
    # XXX should warnings be output if these needed to be changed?
    def setup_fmt(self, ctx):
        # XXX it's too late to change the ctx.opts.keep_comments; that's why
        #     we change ctx.keep_comments directly; naughty?
        ctx.keep_comments = True    
        ctx.opts.yang_canonical = False
        ctx.opts.yang_keep_blank_lines = True

    # XXX don't really want to raise emit errors? would prefer to report and
    #     continue?
    def emit(self, ctx, modules, fd):
        update_import_dates = ctx.opts.yang_edit_update_import_dates

        header = {
            "yang-version": ctx.opts.yang_edit_yang_version
        }
        
        meta = {
            "organization": ctx.opts.yang_edit_organization,
            "contact": ctx.opts.yang_edit_contact,
            "description": ctx.opts.yang_edit_description,
        }

        revision = {
            "arg": ctx.opts.yang_edit_revision_date,
            "description": ctx.opts.yang_edit_revision_description,
            "reference": ctx.opts.yang_edit_revision_reference,
        }
        
        hooks = YANGEditEmitHooks(update_import_dates, header, meta, revision)
        module = modules[0]
        yang.emit_yang(ctx, hooks, module, fd)

class YANGEditEmitHooks(yang.YANGEmitHooks):
    def __init__(self, update_import_dates, header, meta, revision):
        self._update_import_dates = update_import_dates

        self._header = header
        self._meta = meta

        self._revision = revision
        self._revision_done = False

    # XXX if adding statements should place them in the canonical location;
    #     currently are just appending them
    def emit_stmt_hook(self, ctx, stmt, level):
        keyword = stmt.keyword

        if level == 0:
            if keyword in ["module", "submodule"]:
                self._set_header_details(ctx, stmt)

        elif level != 1:
            pass

        elif self._update_import_dates and keyword in ["import", "include"]:
            self._update_import_date(ctx, stmt)

        elif keyword in self._meta.keys():
            self._set_meta_details(ctx, stmt)

        elif keyword == "revision" and not self._revision_done:
            self._set_revision_details(ctx, stmt)
            self._revision_done = True

    def _update_import_date(self, ctx, stmt):
        imprev = stmt.search_one("revision-date")
        imprevdate = imprev.arg if imprev else None

        impmod = ctx.get_module(stmt.arg, imprevdate)
        impmodrev = impmod.search_one("revision") if impmod else None
        impmodrevdate = impmodrev.arg if impmodrev else None

        if not imprev or impmodrevdate > imprevdate:
            update_or_add_stmt(stmt, "revision-date", impmodrevdate)

    def _set_header_details(self, ctx, stmt):
        for keyword in self._header.keys():
            update_or_add_stmt(stmt, keyword, self._header[keyword], 0)

    def _set_meta_details(self, ctx, stmt):
        newarg = get_arg_value(self._meta[stmt.keyword], stmt.arg)
        if newarg is not None:
            stmt.arg = newarg

    def _set_revision_details(self, ctx, stmt):
        newarg = self._revision.get("arg", None)
        if newarg is not None:
            newest = get_newest_submodule(ctx, stmt.top, 0)
            if newarg < newest[1]:
                raise error.EmitError("Revision %s is older than newest "
                                      "included submodule %s@%s" % \
                                      (newarg, newest[0], newest[1]))
            stmt.arg = newarg

        other_keywords = set(self._revision.keys()) - set(["arg"])
        for keyword in other_keywords:
            update_or_add_stmt(stmt, keyword, self._revision[keyword])

def get_arg_value(arg, currarg=None):
    if arg is None or arg[0] not in ["%", "@"]:
        return arg
    else:
        try:
            argval = ""
            specs = arg.split("+")
            for spec in specs:
                if argval != "":
                    argval += "\n\n"
                if spec[0] not in ["%", "@"]:
                    argval += spec
                elif spec[0] == "%":
                    if spec == "%SUMMARY":
                        summary = get_arg_summary(currarg)
                        if summary:
                            argval += summary
                    else:
                        argval += spec
                elif spec[0] == "@":
                    argval += open(spec[1:], "r").read().rstrip()
            return argval
        except IOError as e:
            raise error.EmitError(str(e))

def get_arg_summary(arg):
    lines = arg.splitlines()
    summary = ""
    for line in lines:
        if line.strip() == "":
            break
        if summary != "":
            summary += "\n"
        summary += line
    return summary if summary else "TBD"

# XXX need proper insertion in canonical order
def update_or_add_stmt(stmt, keyword, arg, pos=None):
    child = stmt.search_one(keyword)
    currarg = child.arg if child else None
    argval = get_arg_value(arg, currarg)
    if argval is None:
        child = None
    elif child:
        if child.arg and child.arg != argval and child.arg != "TBD":
            sys.stderr.write("%s: not replacing existing %s '%s' with "
                             "'%s'\n" % (child.pos, keyword, child.arg,
                                         argval))
        else:
            child.arg = argval
    else:
        child = statements.Statement(stmt.top, stmt, None, keyword, argval)
        if pos is None: pos = len(stmt.substmts)
        stmt.substmts.insert(pos, child)
    return child

def get_newest_submodule(ctx, mod, level, newest=None):
    if newest is None:
        newest = (None, "0000-00-00")

    if level > 0:
        rev_stmt = mod.search_one("revision")
        if rev_stmt and rev_stmt.arg > newest[1]:
            newest = (mod.arg, rev_stmt.arg)

    for inc_stmt in mod.search("include"):
        inc_rev_date_stmt = inc_stmt.search_one("revision-date")
        inc_rev_date = inc_rev_date_stmt.arg if inc_rev_date_stmt else None
        mod = ctx.get_module(inc_stmt.arg, inc_rev_date)
        if mod:
            newest = get_newest_submodule(ctx, mod, level + 1, newest)

    return newest
