#!/bin/bash
set -e

# since virtualenv manipulates env vars it is better to keep all
# the dependent tasks runing inside a single process.

## setup ---------------------------------------------------------------------
# install virtualenv
[ -d .test-env ] || \
    virtualenv --system-site-packages --always-copy .test-env > /dev/null
# activate it
source .test-env/bin/activate
# Install pytest
pip install pytest > /dev/null
# Build pyang from source and install it using pip
current_dir=$PWD
cd ../../..
rm -f dist/*.whl
python setup.py bdist_wheel > /dev/null
pip install -I dist/*.whl > /dev/null
cd $current_dir

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