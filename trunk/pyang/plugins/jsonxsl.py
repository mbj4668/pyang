"""JSON XSL output plugin

This plugin takes a YANG data model and produces an XSL stylesheet
that translates datastore contents from XML to JSON.
"""

import os
import xml.etree.ElementTree as ET

from pyang import plugin
from pyang import statements

ss = ET.Element("stylesheet",
                {"version": "1.0",
                 "xmlns": "http://www.w3.org/1999/XSL/Transform",
                 "xmlns:nc": "urn:ietf:params:xml:ns:netconf:base:1.0",
                 "xmlns:en": "urn:ietf:params:xml:ns:netconf:notification:1.0"})
"""Root element of the output XSLT stylesheet."""

def pyang_plugin_init():
    plugin.register_plugin(JsonXslPlugin())

class JsonXslPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['jsonxsl'] = self

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        emit_json_xsl(modules, fd)

def emit_json_xsl(modules, fd):
    """Main control function.

    Set up the top-level parts of the stylesheet, the process
    recursively all nodes in all data trees, and finally emit the
    serialized stylesheet.
    """
    tree = ET.ElementTree(ss)
    ET.SubElement(ss, "output", method="text")
    xsltdir = os.environ.get("PYANG_XSLT_DIR",
                             "/usr/local/share/yang/xslt")
    ET.SubElement(ss, "include", href=xsltdir + "/jsonxsl-templates.xsl")
    ET.SubElement(ss, "strip-space", elements="*")
    nsmap = ET.SubElement(ss, "template", name="nsuri-to-module")
    ET.SubElement(nsmap, "param", name="uri")
    choo = ET.SubElement(nsmap, "choose")
    for module in modules:
        ns_uri = module.search_one("namespace").arg
        ss.attrib["xmlns:" + module.i_prefix] = ns_uri
        when = ET.SubElement(choo, "when", test="$uri='" + ns_uri + "'")
        xsl_text(module.i_modulename, when)
        process_module(module)
    tree.write(fd, encoding="utf-8", xml_declaration=True)

def process_module(yam):
    """Process data nodes, RPCs and notifications in a single module."""
    for ch in yam.i_children[:]:
        if ch.keyword == "rpc":
            process_rpc(ch)
        elif ch.keyword == "notification":
            process_notification(ch)
        else:
            continue
        yam.i_children.remove(ch)
    process_children(yam, "//nc:*")

def process_rpc(rpc):
    """Process input and output parts of `rpc`."""
    p = "/nc:rpc/" + qname(rpc)
    tmpl = xsl_template(p)
    xsl_calltemplate("container", tmpl)
    inp = rpc.search_one("input")
    if inp is not None:
        process_children(inp, p)
    outp = rpc.search_one("output")
    if outp is not None:
        process_children(outp, "/nc:rpc-reply")

def process_notification(ntf):
    """Process event notification `ntf`."""
    p = "/en:notification/" + qname(ntf)
    tmpl = xsl_template(p)
    ct = xsl_calltemplate("container", tmpl)
    if ntf.arg == "eventTime":            # local name collision
        xsl_withparam("nsid", ntf.i_module.i_modulename + ":", ct)
    process_children(ntf, p)

def process_children(node, path):
    """Process all children of `node`.

    `path` is the Xpath of `node` which is used in the 'select'
    attribute of XSLT templates.
    """
    chs = node.i_children
    for ch in chs:
        if ch.keyword in ["choice", "case"]:
            process_children(ch, path)
            continue
        p = path + "/" + qname(ch)
        tmpl = xsl_template(p)
        ct = xsl_calltemplate(ch.keyword, tmpl)
        if [c.arg for c in chs].count(ch.arg) > 1:
            xsl_withparam("nsid", ch.i_module.i_modulename + ":", ct)
        if ch.keyword in ["leaf", "leaf-list"]:
            type_param(ch, ct)
        elif ch.keyword != "anyxml":
            process_children(ch, p)

def type_param(node, ct):
    """Resolve the type of a leaf or leaf-list node for JSON.
    """
    while 1:
        tstat = node.search_one("type")
        if tstat.arg == "leafref":
            node = tstat.i_type_spec.i_target_node
            continue
        if tstat.i_typedef is None:
            break
        node = tstat.i_typedef
    t = tstat.arg
    if t in ["boolean", "int8", "int16", "int32", "int64",
             "uint8", "uint16", "uint32", "uint64", "decimal64"]:
        typ = "unquoted"
    elif t == "empty":
        typ = "empty"
    elif t == "instance-identifier":
        typ = "instance-identifier"
    elif t == "identityref":
        typ = "identityref"
    elif t == "string":
        typ = "string"
    else:
        typ = "other"
    xsl_withparam("type", typ, ct)

def qname(node):
    """Return the qualified name of `node`.

    In JSON, namespace identifiers are YANG module names.
    """
    return node.i_module.i_prefix + ":" + node.arg

def xsl_template(name):
    """Construct an XSLT 'template' element matching `name`."""
    return ET.SubElement(ss, "template" , match = name) 

def xsl_text(text, parent):
    """Construct an XSLT 'text' element containing `text`.

    `parent` is this element's parent.
    """
    res = ET.SubElement(parent, "text")
    res.text = text
    return res

def xsl_calltemplate(name, parent):
    """Construct an XSLT 'call-template' element.

    `parent` is this element's parent.
    `name` is the name of the template to be called.
    """
    return ET.SubElement(parent, "call-template", name=name)

def xsl_withparam(name, value, parent):
    """Construct an XSLT 'with-param' element.

    `parent` is this element's parent.
    `name` is the parameter name.
    `value` is the parameter value.
    """
    res = ET.SubElement(parent, "with-param", name=name)
    res.text = value
    return res
