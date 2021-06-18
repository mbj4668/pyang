# pyang #

[![Release](https://img.shields.io/github/v/release/mbj4668/pyang)](https://github.com/mbj4668/pyang/releases) [![Build Status](https://github.com/mbj4668/pyang/actions/workflows/run-tests/badge.svg)](https://github.com/mbj4668/pyang/actions)

## Overview ##

pyang is a YANG validator, transformator and code generator, written
in python. It can be used to validate YANG modules for correctness, to
transform YANG modules into other formats, and to write plugins to
generate code from the modules.

YANG ([RFC 7950](http://tools.ietf.org/html/rfc7950)) is a data modeling language for NETCONF ([RFC 6241](http://tools.ietf.org/html/rfc6241)), developed by the IETF [NETMOD](http://www.ietf.org/html.charters/netmod-charter.html) WG.

## Documentation ##

See [Documentation](https://github.com/mbj4668/pyang/wiki/Documentation).

## Installation ##

- **1 PyPI**

Pyang can be installed from [PyPI](https://pypi.python.org/pypi):

```sh
# pip install pyang
```

- **2 Source**

```sh
  git clone https://github.com/mbj4668/pyang.git
  cd pyang
  python setup.py install
  (this might require root access)
```


To install in a different location, run:

```sh
  python setup.py install --prefix=/usr/local
```

If you do this, it is recommended to set the environment variable
**YANG_INSTALL** to the prefix directory.  This ensures that pyang will
find standard YANG modules. In addition, make sure that **PYTHONPATH** is set
to something as follows:

```sh
export PYTHONPATH=/usr/local/lib/python2.7/site-packages
```

or whatever version of python you are running.


Run locally without installing

```sh
export PATH=`pwd`/bin:$PATH
export MANPATH=`pwd`/man:$MANPATH
export PYTHONPATH=`pwd`:$PYTHONPATH
export YANG_MODPATH=`pwd`/modules:$YANG_MODPATH
export PYANG_XSLT_DIR=`pwd`/xslt
export PYANG_RNG_LIBDIR=`pwd`/schema
```

or:

```sh
source ./env.sh
```

## Compatibility ##

pyang is compatible with the following IETF RFCs:

  * [RFC 6020: YANG - A Data Modeling Language for the Network Configuration Protocol (NETCONF)](https://tools.ietf.org/html/rfc6020)
  * [RFC 6087: Guidelines for Authors and Reviewers of YANG Data Model Documents](https://tools.ietf.org/html/rfc6087)
  * [RFC 6110: Mapping YANG to Document Schema Definition Languages and Validating NETCONF Content](https://tools.ietf.org/html/rfc6110)
  * [RFC 6643: Translation of Structure of Management Information Version 2 (SMIv2) MIB Modules to YANG Modules](https://tools.ietf.org/html/rfc6643)
  * [RFC 7950: The YANG 1.1 Data Modeling Languages](https://tools.ietf.org/html/rfc7950)
  * [RFC 7952: Defining and Using Metadata with YANGs](https://tools.ietf.org/html/rfc7952)
  * [RFC 8040: RESTCONF Protocols](https://tools.ietf.org/html/rfc8040)
  * [RFC 8407: Guidelines for Authors and Reviewers of Documents Containing YANG Data Models](https://tools.ietf.org/html/rfc8407)
  * [RFC 8791: YANG Data Structure Extensions](https://tools.ietf.org/html/rfc8791)

## Features ##

  * Validate YANG modules.
  * Convert YANG modules to YIN, and YIN to YANG.
  * Translate YANG data models to DSDL schemas, which can be used for
    validating various XML instance documents. See
    [InstanceValidation](https://github.com/mbj4668/pyang/wiki/InstanceValidation).
  * Translate YANG data models to XSD.
  * Generate UML diagrams from YANG models. See
    [UMLOutput](https://github.com/mbj4668/pyang/wiki/UMLOutput) for
    an example.
  * Generate compact tree representation of YANG models for quick
    visualization. See
    [TreeOutput](https://github.com/mbj4668/pyang/wiki/TreeOutput) for
    an example.
  * Generate a skeleton XML instance document from the data model.
  * Schema-aware translation of instance documents encoded in XML to
    JSON and vice-versa. See
    [XmlJson](https://github.com/mbj4668/pyang/wiki/XmlJson).
  * Plugin framework for simple development of other outputs, such as
    code generation.

## Usage ##

```sh
pyang -h
```

or

```sh
man pyang
```

## Code structure ##

* **bin/**
  Executable scripts.

* **pyang/**
  Contains the pyang library code.

* **pyang/__init__.py**
  Initialization code for the pyang library.

* **pyang/context.py**
  Defines the Context class, which represents a parsing session

* **pyang/repository.py**
  Defines the Repository class, which is used to access modules.

* **pyang/syntax.py**
  Generic syntax checking for YANG and YIN statements.
  Defines regular expressions for argument checking of core
  statements.

* **pyang/grammar.py**
  Generic grammar for YANG and YIN.
  Defines chk_module_statements() which validates a parse tree
  according to the grammar.

* **pyang/statements.py**
  Defines the generic Statement class and all validation code.

* **pyang/yang_parser.py**
  YANG tokenizer and parser.

* **pyang/yin_parser.py**
  YIN parser.  Uses the expat library for XML parsing.

* **pyang/types.py**
  Contains code for checking built-in types.

* **pyang/plugin.py**
  Plugin API.  Defines the class PyangPlugin which all plugins
  inherits from. All output handlers are written as plugins.

* **pyang/plugins/**
  Directory where plugins can be installed.  All plugins in this
  directory are automatically initialized when the library is
  initialized.

* **pyang/translators/**
  Contains output plugins for YANG, YIN, XSD, and DSDL translation.

* **xslt**
  Contains XSLT style sheets for generating RELAX NG, Schematron and
  DSRL schemas and validating instance documents. Also included is the
  free implementation of ISO Schematron by Rick Jelliffe from
  http://www.schematron.com/ (files iso_schematron_skeleton_for_xslt1.xsl,
  iso_abstract_expand.xsl and iso_svrl_for_xslt1.xsl).

* **schema**
  Contains RELAX NG schemas and pattern libraries.



