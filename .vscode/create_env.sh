#!/bin/sh

# This script creates .env file at the root of the repository corresponding to
# the environment created when sourcing env.sh at the root of the repository
# It is expected that this script is run from the root of the repository

#shellcheck source=../env.sh
. ./env.sh

{
  echo "PATH=\"$PATH\""
  echo "MANPATH=\"$MANPATH\""
  echo "PYTHONPATH=\"$PYTHONPATH\""
  echo "YANG_MODPATH=\"$YANG_MODPATH\""
  echo "PYANG_XSLT_DIR=\"$PYANG_XSLT_DIR\""
  echo "PYANG_RNG_LIBDIR=\"$PYANG_RNG_LIBDIR\""
  echo "W=\"$W\""
} > ./.env
