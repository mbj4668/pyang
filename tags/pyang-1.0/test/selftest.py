#!/usr/bin/env python

# check that some internal data structures are conistent

import sys
import glob
import subprocess


from pyang import util
from pyang import error
from pyang import grammar
from pyang import syntax
import pyang.translators.xsd as xsd

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
            print >> sys.stderr, "Error code: %s not used" % x
            found_error = True

def chk_stmts():
    global found_error
    stmtmaps = [(grammar.stmt_map, "grammar.stmt_map"),
                (xsd.yang_keywords, "xsd.yang_keywords"),
                (syntax.yin_map, "syntax.yin_map")]
    for (map, name) in stmtmaps:
        for stmt in map:
            targets = util.listsdelete((map,name), stmtmaps)
            for (tmap, tname) in targets: 
                if stmt not in tmap:
                    print >> sys.stderr, \
                        "Stmt %s in %s not found in %s" % \
                        (stmt, name, tname)
                    found_error = True
    if found_error:
        return
    for s in syntax.yin_map:
        (argname, yinelem) = syntax.yin_map[s]
        (xargname, xyinelem, xsdappinfo) = xsd.yang_keywords[s]
        if argname != xargname:
            print >> sys.stderr, \
                "Stmt %s argname mismatch in syntax.yin_map " \
                "and xsd.yang_keywords" % s
            found_error = True
        if yinelem != xyinelem:
            print >> sys.stderr, \
                "Stmt %s yinelem mismatch in syntax.yin_map " \
                "and xsd.yang_keywords" % s
            found_error = True
            

chk_error_codes()
chk_stmts()
if found_error:
    sys.exit(1)

