---
title: JSON2XML
section: 1
header: User Manual
footer: json2xml-_VERSION_
date: _DATE_
---
# NAME

json2xml - translates JSON documents conforming to a YANG data
model into XML.

# SYNOPSIS

**json2xml** [-t target] [-o *output_file*] *driver_file* *json_file*

**json2xml** -h | -\-help


# DESCRIPTION

This program translates *json_file* into XML using the procedure
specified in **RFC 7951**.

The translation uses a second input file, *driver_file*, which
contains a concise JSON representation of the YANG data model to which
*json_file* should conform, at least structurally. Normally,
*driver_file* is obtained as the *jtox* output of **pyang**.

Using \"-\" (hyphen) in place of *json_file* instructs the program to
read a JSON document from the standard input.

The *target* argument specifies the document (root) element for the
output XML document. This encapsulation is necessary because the input
JSON document may contain multiple JSON objects at the top
level. Supported values for the *target* argument are:

data
:   The document element will be &lt;nc:data&gt;. This is the default.

config
:   The document element will be &lt;nc:data&gt;.

The XML prefix \"nc\" represents the standard NETCONF namespace with URI
\"urn:ietf:params:xml:ns:netconf:base:1.0\".

# OPTIONS

**-t** *target*, **target** *target*
:    Specifies the target type of the output XML document,
     i.e., its document element. The default is **data**.

**-o** *output_file*, **-\-output** *output_file*
:    Write output to *output_file* instead of the standard output.

**-h**, **-\-help**
:    Displays help screen and exits.

# EXAMPLES

    $ pyang -f jtox -o dhcp.jtox dhcp.yang

    $ json2xml -o dhcp-data.xml dhcp.jtox dhcp-data.json

The first command generates the driver file dhcp.jtox, which is then
used for translating JSON file dhcp-data.json to XML file
dhcp-data.xml.

# DIAGNOSTICS

**json2xml** return codes have the following meaning:

0
:   No error (normal termination)

1
:   One of the input files cannot be read

2
:   Error in command line arguments

3
:   JSON to XML translation failed

# SEE ALSO

**RFC 7951**, **pyang**(1)


# AUTHOR

**Ladislav Lhotka** &lt;lhotka@nic.cz&gt;\
CZ.NIC
