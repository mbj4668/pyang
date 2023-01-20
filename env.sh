#!/bin/sh

# source this file to get environment setup for the
# pyang below here

export PATH="$PWD/bin:$PATH"
export MANPATH="$PWD/man:$MANPATH"
export PYTHONPATH="$PWD:$PYTHONPATH"
export YANG_MODPATH="$PWD/modules:$YANG_MODPATH"
export PYANG_XSLT_DIR="$PWD/xslt"
export PYANG_RNG_LIBDIR="$PWD/schema"
export W="$PWD"
