#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
"""
tests for PYANG data files
"""
import os
import sys

# hack to handle pip 10 internals
try:
    import pip.locations as locations
except ImportError:
    import pip._internal.locations as locations

from pyang.context import Context
from pyang.repository import FileRepository

EXISTING_MODULE = 'ietf-yang-types'

DEFAULT_OPTIONS = {
    'format': 'yang',
    'verbose': True,
    'list_errors': True,
    'print_error_code': True,
    'yang_remove_unused_imports': True,
    'yang_canonical': True,
    'trim_yin': False,
    'keep_comments': True,
    'features': [],
    'deviations': [],
    'path': []
}
"""Default options for pyang command line"""


class objectify(object):
    """Utility for providing object access syntax (.attr) to dicts"""

    def __init__(self, *args, **kwargs):
        for entry in args:
            self.__dict__.update(entry)

        self.__dict__.update(kwargs)

    def __getattr__(self, _):
        return None

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value


def create_context(path='.', *options, **kwargs):
    """Generates a pyang context

    Arguments:
        path (str): location of YANG modules.
        *options: list of dicts, with options to be passed to context.
        **kwargs: similar to ``options`` but have a higher precedence.

    Returns:
        pyang.Context: Context object for ``pyang`` usage
    """

    opts = objectify(DEFAULT_OPTIONS, *options, **kwargs)
    repo = FileRepository(path, no_path_recurse=opts.no_path_recurse)
    ctx = Context(repo)
    ctx.opts = opts

    return ctx


def test_can_find_modules_with_pip_install():
    """
    context should find the default installed modules even when pyang
        is installed using pip
    """

    # remove obfuscation from env vars
    if os.environ.get('YANG_INSTALL'):
        del os.environ['YANG_INSTALL']

    if os.environ.get('YANG_MODPATH'):
        del os.environ['YANG_MODPATH']

    ctx = create_context()
    module = ctx.search_module(None, EXISTING_MODULE)
    assert module is not None


def test_can_find_modules_when_prefix_differ(monkeypatch):
    """
    context should find the default installed modules, without the help
        of environment variables, even of the pip install location
        differs from ``sys.prefix``
    """

    # store pip location.
    # monkeypatching sys.prefix will side_effect scheme.
    try:
        scheme = locations.distutils_scheme('pyang')
        monkeypatch.setattr(
            locations, 'distutils_scheme', lambda *_: scheme)
    except:
        print("cannot get scheme from pip, skipping")
        return

    # simulate #225 description
    monkeypatch.setattr(sys, 'prefix', '/usr')

    # remove obfuscation from env vars
    if os.environ.get('YANG_INSTALL'):
        del os.environ['YANG_INSTALL']

    if os.environ.get('YANG_MODPATH'):
        del os.environ['YANG_MODPATH']

    ctx = create_context()
    module = ctx.search_module(None, EXISTING_MODULE)
    assert module is not None
