#! /usr/bin/python

import sys
import pyang
from pyang.translators import dsdl

repos = pyang.FileRepository()
ctx = pyang.Context(repos)

try:
    filename = sys.argv[1]
    fd = file(filename)
    text = fd.read()
except IOError, ex:
    sys.stderr.write("error %s: %s\n" % (filename, str(ex)))
    sys.exit(1)

yam = ctx.add_module(filename, text)

#etree = DSDLTranslator().translate(yam)
etree = dsdl.DSDLTranslator().translate(yam, emit=["sch", "a", "dc"], debug=0)
etree.write(sys.stdout, "UTF-8")
