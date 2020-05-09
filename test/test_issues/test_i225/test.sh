#!/bin/bash
set -e

# since virtualenv manipulates env vars it is better to keep all
# the dependent tasks runing inside a single process.

current_dir=$PWD
## setup ---------------------------------------------------------------------
# install virtualenv
exec 6>&1 7>&2 >.test-env.log 2>&1

setup_failed() {
    exec >&6 2>&7 6>&- 7>&-
    echo
    echo "Virtualenv setup failed, with output:"
    echo "====================================="
    cat $current_dir/.test-env.log
    echo "====================================="
    echo "Virtual env setup failure output ends"
    echo
    exit 1
}
trap setup_failed ERR

[ -d .test-env ] || \
    virtualenv --system-site-packages --always-copy .test-env
# activate it
source .test-env/bin/activate
# Install pytest
pip install pytest
# Build pyang from source and install it using pip
cd ../../..
rm -f dist/*.whl
python setup.py bdist_wheel
pip install -I dist/*.whl
cd $current_dir
trap - ERR
exec >&6 2>&7 6>&- 7>&-
echo "Virtualenv setup succeeded"

## tests ---------------------------------------------------------------------
py.test test_*.py

## teardown ------------------------------------------------------------------
# deactivate virtualenv
deactivate
# remove it
rm -Rf .test-env
# cleanup build
cd ../../..
rm -Rf pyang.egg-info .cache build/*.whl
cd $current_dir
rm -f .test-env.log
