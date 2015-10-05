#!/usr/bin/env python

# check that some internal data structures are conistent

import sys
import glob
import subprocess


from pyang import util
from pyang import error
from pyang import grammar
from pyang import syntax

def oscmd(cmd):
    p = subprocess.Popen(cmd, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    res = p.stdout.read()
    err = p.stderr.read()
    retcode = p.returncode
    if len(res) > 0 and res[-1] == '\n':
        res = res[:-1]
    if len(err) > 0 and err[-1] == '\n':
        err = err[:-1]
    return (retcode, res, err)

found_error = False

def chk_error_codes():
    global found_error
    files = glob.glob("../pyang/*.py") + glob.glob("../pyang/*/*.py")
    del files[files.index('../pyang/error.py')]
    filesstr = ' '.join(files)
    for x in error.error_codes:
        (retcode, res, err) = oscmd('grep %s %s' % (x, filesstr))
        if retcode != 0:
            sys.stderr.write("Error code: %s not used" % x)
            found_error = True

def chk_stmts():
    stmtmaps = [(grammar.stmt_map, "grammar.stmt_map"),
                (syntax.yin_map, "syntax.yin_map")]
    for (map, name) in stmtmaps:
        for stmt in map:
            targets = util.listsdelete((map,name), stmtmaps)
            for (tmap, tname) in targets:
                if stmt not in tmap:
                    sys.stderr.write("Stmt %s in %s not found in %s" % \
                                         (stmt, name, tname))


chk_error_codes()
chk_stmts()
if found_error:
    sys.exit(1)

