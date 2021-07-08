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
    out = p.stdout.read().decode('utf-8').rstrip('\n')
    err = p.stderr.read().decode('utf-8').rstrip('\n')
    retcode = p.returncode
    return retcode, out, err


def chk_error_codes():
    found_error = False
    # Plugins are not loaded and their error codes are not defined
    # Moreover, some plugins set up their codes in setup_ctx, which requires
    # e.g. option parsing and repository setup done as in the pyang script.
    # They also create new 'statements', which do not have yin_map entries.
    # Invoking the pyang error code listing function should list them all.
    retcode, out, err = oscmd(
        ['pyang', '--list-errors', '--lint', '--ieee', '--ietf'])
    if retcode:
        sys.stderr.write('Cannot list errors from pyang\n')
        if err:
            for line in err.split('\n'):
                sys.stderr.write('[pyang] %s\n' % line)
        found_error = True
        listed_codes = set()
    else:
        error_categories = ('Error:', 'Minor Error:', 'Warning:')
        listed_codes = set(line.strip().split()[-1] for line in out.split('\n')
                           if line.startswith(error_categories))
        for code in error.error_codes:
            if code not in listed_codes:
                sys.stderr.write('Error code: %s not listed by pyang\n' % code)
                found_error = True

    files = glob.glob("../pyang/*.py") + glob.glob("../pyang/*/*.py")
    all_codes = sorted(set(error.error_codes) | listed_codes)
    for code in all_codes:
        if code.endswith("_v1.1"):
            continue
        retcode, out, _ = oscmd(['grep', '-e', r'\b%s\b' % code, '--'] + files)
        # A used error code has has inner newlines in output for 2+ occurences
        if retcode or out.count('\n') == 0:
            sys.stderr.write("Error code: %s not used\n" % code)
            if err:
                for line in err.split('\n'):
                    sys.stderr.write('[grep] %s\n' % line)
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


def main():
    return any([
        chk_error_codes(),
        chk_stmts(),
    ])

sys.exit(main())
