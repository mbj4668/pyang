---
title: YANG2DSDL
section: 1
header: User Manual
footer: yang2dsdl-_VERSION_
date: _DATE_
---
# NAME

yang2dsdl - translates YANG data models to DSDL schemas and validates
instance documents.

# SYNOPSIS

**yang2dsdl** [-t *target*] [-d *dir*] [-b *basename*] [-j] [-x] [-c]
[-v *instance*] *file*...

**yang2dsdl** -L [-t *target*] [-d *dir*] [-b *basename*] [-j] [-x]
      [-c] [-v *instance*] *file*...

**yang2dsdl** -s [-t *target*] [-d *dir*] [-b *basename*] [-j] [-x] [-c]
[-v *instance*]

**yang2dsdl** -h

# DESCRIPTION

This shell script facilitates the translation of a data model
described by one or more input YANG modules to DSDL schemas (RELAX NG,
Schematron and DSRL) for a selected instance XML document type, as
described in **RFC 6110**. Optionally,
the script can validate an instance document of the given type against
the schemas.

The input YANG module(s) may be given either directly as *file*
parameter(s) on the command line, or indirectly through a server
&lt;hello&gt; message which also declares capabilities and features
supported by the server. The latter alternative is indicated by the
**-L** switch, and only one *file* parameter may be given in this
case.

Input YANG module(s) may be expressed in YANG or YIN syntax. The
output DSDL schemas are written to the directory *dir* (current
directory by default). Unless the option **-s** is used, this
directory must be writable.

Metadata annotations are also supported, if they are defined and used
as described in **RFC 7952**.


The script can be executed by any shell interpreter compatible with
POSIX.2, such as **bash**(1) or **dash**(1).

The *target* argument specifies the type of the target instance
document. Supported values are:

data
:   Datastore contents (configuration and state
    data) encapsulated in &lt;nc:data&gt; document
    element.

config
:   A configuration datastore contents encapsulated in
    &lt;nc:config&gt; document element.

get-reply
:   A complete NETCONF message containing a reply to the
    &lt;nc:get&gt; operation.

get-data-reply
:   A complete NETCONF message containing a reply to the
    &lt;ncds:get-data&gt; operation.

get-config-reply
:   A complete NETCONF message containing a reply to the
    &lt;nc:get-config&gt; operation.

edit-config
:   A complete NETCONF message containing an &lt;nc:edit-config&gt;
    request. Only the RELAX NG schema is generated for this target.

rpc
:   An RPC request defined in an input YANG module.

rpc-reply
:   An RPC reply defined in an input YANG module.

notification
:   An event notification defined in an input YANG module.


The output schemas are contained in the following four files whose
names depend on the arguments *basename* and *target*:

*basename*-*target*.rng
:    RELAX NG schema for the target document type.

*basename*-gdefs-config.rng, *basename*-gdefs-edit.rng, *basename*-gdefs.rng
:   Auxiliary RELAX NG schema containing global named pattern
    definitions. The first is generated for "config" and
    "get-config-reply" targets, the second for "edit-config" and the
    third for the remaining targets.

*basename*-*target*.sch
:   Schematron schema for the target document type. Not generated for
    the "edit-config" target.

*basename*-*target*.dsrl
:   DSRL schema for the target document type. Not generated for the
    "edit-config" target.

Optional validation of an XML document stored in the file
*instance* proceeds as follows:

1. Grammatical and datatype constraints are checked using the RELAX NG
   schema.

2. The DSRL schema is used for adding default values together with
   ancestor containers to the instance document where necessary.

3. Semantic constraints are checked using the Schematron schema. The
   skeleton implementation of **ISO Schematron** by Rick Jelliffe is
   included in the distribution and used for this purpose.

Steps 3 and 3 are not performed for the "edit-config" target, or if
step 1 reports any errors.

Option **-s** may be used together with **-v** for validating an
instance document without generating the schemas. This assumes that
the schemas are already present in the directory selected by the
**-d** option (current directory by default). In this case, the
basename of the schemas must be specified using **-b** *basename* and
the input YANG modules need not be given. Also, if the DSRL or
Schematron schema is missing, the corresponding step is skipped.

The script uses programs from the libxml2 suite - **xmllint**(1) for
RELAX NG validation and **xsltproc**(1) for performing XSLT
transformations. Alternatively, **jing**(1) can be used for RELAX NG
validation (option **-j**). If necessary, the script could be easily
modified for use with other RELAX NG validators and/or XSLT1
processors supporting EXSLT.

# OPTIONS

**-b** *basename*
:   Specifies the basename of files in which the output schemas are
    stored. The default is the concatenation of the names of all input
    YANG modules connected with the underscore character "_". This
    option is mandatory if **-s** is used.

**-d** *dir*
:   Specifies the directory for output files. By default they are
    stored in the current directory.

**-h**
:   Displays help screen and exits.

**-j**
:   Uses **jing**(1) for RELAX NG validation
    instead of the default **xmllint**(1).

**-L**
:   Interpret the *file* parameter as the name of a file containing a
    server &lt;hello&gt; message. In this case, exactly one *file*
    parameter must be given.

**-s**
:   Performs just validation, without (re)generating the schemas. This
    option is only allowed together with **-v** and **-b** *basename*
    must also be specified.

**-t** *target*
:   Specifies the target XML document type using one of the following
    strings as explained above: **data** (default), **config**,
    **get-reply**, **get-data-reply**, **get-config-reply**,
    **edit-config**, **rpc**, **rpc-reply** or **notification**.

**-v** *instance*
:   Validates an instance XML document contained in file *instance*.

**-x**
:   Try to translate modules written in unsupported YANG versions.  If
    the module doesn't use any constructs introduced after YANG
    version 1, this may work.  This option may produce unexpected
    results.  Use at own risk.

**-c**
:   Use only definitions with status "current" in the YANG module.

# FILES

/usr/local/share/yang/xslt/gen-relaxng.xsl
:   XSLT stylesheet generating RELAX NG schemas.

/usr/local/share/yang/xslt/gen-schematron.xsl
:   XSLT stylesheet generating DSRL schemas.

/usr/local/share/yang/xslt/gen-common.xsl
:   Common templates for all three XSLT generators.

/usr/local/share/yang/xslt/dsrl2xslt.xsl
:   Translates a subset of DSRL containing only specification of
    default contents to an XSLT stylesheet.

/usr/local/share/yang/xslt/svrl2text.xsl
:   Translates an SVRL report to plain text.

/usr/local/share/yang/schema/relaxng-lib.rng
:   RELAX NG library of common NETCONF elements.

/usr/local/share/yang/schema/edit-config-attributes.rng
:   RELAX NG definitions of &lt;edit-config&gt; attributes.

# ENVIRONMENT VARIABLES

**PYANG_XSLT_DIR**
:   Alternative directory for XSLT stylesheets. The default is
    installation dependent.

**PYANG_RNG_LIBDIR**
:   Alternative directory for the RELAX NG library. The default is
    installation dependent.

**XSLT_OPTS**
:   Options to pass to the XSLT processor when generating the DSDL
    schemas. This is mainly useful for debugging.

# EXAMPLES

    $ yang2dsdl -v dhcp-data.xml dhcp.yang

This command generates the DSDL schemas for the datastore contents
(default *data* target) as defined by dhcp.yang module and validates
an instance document stored in the dhcp-data.xml file.

    $ yang2dsdl -t rpc rpc-rock.yang

This command generates DSDL schemas for the choice of input
parts (requests) of all RPC operations defined in the module
rpc-rock.yang.

# DIAGNOSTICS

**yang2dsdl** return codes have the following meaning:

0
:   No error (normal termination)

1
:   Error in input parameters

2
:   Error in DSDL schema generation

3
:   Instance validation failed


# BUGS

1. The logic of command-line arguments may not be able to distinguish
   replies to different RPC requests, for example if the replies have
   the same top-level element.

# SEE ALSO

**pyang**(1), **xsltproc**(1), **xmllint**(1), **RFC 61110**.


# AUTHOR

**Ladislav Lhotka** &lt;lhotka@nic.cz&gt;\
CZ.NIC
