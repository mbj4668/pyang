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

            # set namespace
            YANGEditOption("--yang-edit-namespace",
                           dest="yang_edit_namespace",
                           metavar="NAMESPACE",
                           help="Set YANG namespace to the supplied value"),

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
            YANGEditOption("--yang-edit-previous-revision-date",
                           dest="yang_edit_previous_revision_date",
                           type="date",
                           metavar="PREVDATE",
                           help="Delete any revisions later than "
                           "the supplied yyyy-mm-dd"),
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
            "yang-version": ctx.opts.yang_edit_yang_version,
            "namespace": ctx.opts.yang_edit_namespace
        }
        
        meta = {
            "organization": ctx.opts.yang_edit_organization,
            "contact": ctx.opts.yang_edit_contact,
            "description": ctx.opts.yang_edit_description,
        }

        revision = {
            "olddate": ctx.opts.yang_edit_previous_revision_date,
            "newdate": ctx.opts.yang_edit_revision_date,
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

    def emit_stmt_hook(self, ctx, stmt, level):
        keyword = stmt.keyword
        replstmts = None

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
            allrevs = stmt.parent.search("revision")
            lastrev = stmt == allrevs[-1]
            replstmts = self._set_revision_details(ctx, stmt, lastrev)

        return replstmts

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
        (newarg, ignore) = get_arg_value(self._meta[stmt.keyword], stmt.arg)
        if newarg is not None:
            stmt.arg = newarg

    # XXX note that this logic relies on there already being at least one
    #     revision statement; --lint checks this so it should be OK
    def _set_revision_details(self, ctx, stmt, lastrev):
        # the logic is quite tricky; here's what we want to achieve:
        # * "olddate" is the date of the oldest revision to be retained; if not
        #   supplied, any existing revisions are deleted
        # * if "newdate" is supplied, it's the date of the next published
        #   revision and is to be inserted at the start of any remaining
        #   revisions 
        # * reuse rather than delete the oldest revision statement, purely in
        #   order to retain any blank lines after it

        # default action is to do nothing
        action = ""
        #sys.stderr.write("revision %s (lastrev %s)\n" % (stmt.arg, lastrev))
        
        # determine whether to delete this old revision
        olddate = self._revision.get("olddate", None)
        if olddate is None or stmt.arg > olddate:
            action = "delete"
            #sys.stderr.write("-> delete (olddate %s)\n" % olddate)

        # determine whether to insert the new revision
        newdate = self._revision.get("newdate", None)
        if newdate is not None and (action != "delete" or lastrev):
            action = "replace" if action == "delete" else "insert"
            #sys.stderr.write("-> %s (newdate %s)\n" % (action, newdate))
        
        # if deleting, return an empty list
        replstmts = None
        if action == "delete":
            replstmts = []

        # replace and insert logic is quite similar:
        # * if replacing, modify this statement and return a list containing
        #   only it
        # * if inserting, create a new statement and return a list containing
        #   the new and the original statement
        elif action == "replace" or action == "insert":
            if action == "replace":
                revstmt = stmt
                revstmt.arg = newdate
            else:
                revstmt = statements.Statement(stmt.top, stmt.parent, None,
                                               "revision", newdate)

            other_keywords = set(self._revision.keys()) - \
                             set(["olddate", "newdate"])
            for keyword in other_keywords:
                update_or_add_stmt(revstmt, keyword, self._revision[keyword])

            if action == "replace":
                replstmts = [revstmt]
            else:
                replstmts = [revstmt, stmt]

            self._revision_done = True            

        #sys.stderr.write("= %s\n" % [s.arg for s in replstmts])
        return replstmts

def get_arg_value(arg, currarg=None):
    if arg is None or arg[0] not in ["%", "@"]:
        return (arg, True)
    else:
        replace = False
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
                    elif spec.startswith("%SUBST/"):
                        (ignore, old, new) = spec.split("/")
                        if currarg is None:
                            if argval == "":
                                argval = None
                        else:
                            argval = currarg.replace(old, new)
                        replace = True
                    else:
                        argval += spec
                elif spec[0] == "@":
                    argval += open(spec[1:], "r").read().rstrip()
            return (argval, replace)
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

# XXX need proper insertion in canonical order; currently just appending
#     (apart from hack noted below)
def update_or_add_stmt(stmt, keyword, arg, index=None):
    child = stmt.search_one(keyword)
    currarg = child.arg if child else None
    (argval, replace) = get_arg_value(arg, currarg)
    if argval is None:
        child = None
    elif child:
        if not replace and child.arg and child.arg != argval and \
           child.arg != "TBD":
            sys.stderr.write("%s: not replacing existing %s '%s' with "
                             "'%s'\n" % (child.pos, keyword, child.arg,
                                         argval))
        else:
            child.arg = argval
    else:
        child = statements.Statement(stmt.top, stmt, None, keyword, argval)
        if index is None: index = len(stmt.substmts)
        # XXX this hack ensures that "reference" is always last
        if index > 0 and stmt.substmts[index-1].keyword == "reference":
            index -= 1
        stmt.substmts.insert(index, child)
    return child

# XXX is there a proper function for this?
def delete_stmt(parent, stmt):
    if stmt in parent.substmts:
        idx = parent.substmts.index(stmt)
        del parent.substmts[idx]
    del stmt
