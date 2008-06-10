#! /usr/bin/python

import sys
from pyang.main import Context, YangParser
from pyang.translators.dsdl import DSDLTranslator

ctx = Context()
p = YangParser(ctx, sys.argv[1])
yam = p.parse_module()
#etree = DSDLTranslator().translate(yam)
etree = DSDLTranslator().translate(yam, emit=["sch", "a", "dc"], debug=1)
etree.write(sys.stdout, "UTF-8")
