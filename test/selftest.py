#!/usr/bin/env python

# check that some internal data structures are conistent

import sys
import glob
import subprocess

from pyang import error
from pyang import grammar
from pyang import syntax


def oscmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    out = p.stdout.read().rstrip('\n')
    err = p.stderr.read().rstrip('\n')
    retcode = p.returncode
    return retcode, out, err


def chk_error_codes():
    found_error = False
    files = glob.glob("../pyang/*.py") + glob.glob("../pyang/*/*.py")
    # FIXME: plugins are not loaded and their error codes are not defined
    # Moreover, some plugins set up their codes in setup_ctx, which requires
    # e.g. option parsing and repository setup done as in the pyang script.
    # They also create new 'statements', which do not have yin_map entries.
    for code in error.error_codes:
        retcode, out, _ = oscmd(['grep', '-e', r'\b%s\b' % code, '--'] + files)
        # A used error code has its definition and uses - inner newlines in out
        if retcode or out.count('\n') == 0:
            sys.stderr.write("Error code: %s not used\n" % code)
            found_error = True
    return found_error


def chk_stmts():
    found_error = False
    stmt_maps = [(set(grammar.stmt_map), "grammar.stmt_map"),
                 (set(syntax.yin_map), "syntax.yin_map")]
    for stmt_map, name in stmt_maps:
        for test_map, test_name in stmt_maps:
            if test_map is not stmt_map:
                for stmt in stmt_map - test_map:
                    sys.stderr.write("Stmt %s in %s not found in %s\n"
                                     % (stmt, name, test_name))
                    found_error = True
    return found_error


if __name__ == '__main__':
    found_error = any([
        chk_error_codes(),
        chk_stmts(),
    ])
    if found_error:
        sys.exit(1)
