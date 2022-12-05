#!/bin/sh

# source this file to get environment setup for the
# pyang below here

export MANPATH="$PWD/man:$MANPATH"
export PYTHONPATH="$PWD:$PYTHONPATH"
export YANG_MODPATH="$PWD/modules:$YANG_MODPATH"
export PYANG_XSLT_DIR="$PWD/xslt"
export PYANG_RNG_LIBDIR="$PWD/schema"
export W="$PWD"

if ! pyang --help &> /dev/null
then
    alias pyang="$PWD/pyang/scripts/pyang_tool.py"
    alias json2xml="$PWD/pyang/scripts/json2xml.py"
    alias yang2html="$PWD/pyang/scripts/yang2html.py"
fi