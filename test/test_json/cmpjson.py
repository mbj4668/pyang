#! /usr/bin/env python

# This program compares two JSON files given as parameters

import codecs
import sys
import json

if len(sys.argv) != 3:
    sys.stderr.write("Usage: cmpjson.py json_file_1 json_file_2\n")
    sys.exit(1)

fa = codecs.open(sys.argv[1], encoding="utf-8")
fb = codecs.open(sys.argv[2], encoding="utf-8")

a = json.load(fa)
b = json.load(fb)

if a != b:
    sys.stderr.write("JSON documents from %s and %s differ.\n" % tuple(sys.argv[1:3]))
    sys.exit(2)

sys.exit(0)
