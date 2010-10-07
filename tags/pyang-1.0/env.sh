#!/bin/sh

# source this file to get environment setup for the
# pyang below here

p=`pwd`
export PATH=$p/bin:$PATH
export MANPATH=$p/man:$MANPATH
export PYTHONPATH=$p:$PYTHONPATH
export YANG_MODPATH=$p/modules:$YANG_MODPATH
export PYANG_XSLT_DIR=$p/xslt
export PYANG_RNG_LIBDIR=$p/schema
export W=$p
