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
                 "xmlns:nc": "urn:ietf:params:xml:ns:netconf:base:1.0"})

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
        process_children(module, "//nc:*")
    tree.write(fd, encoding="utf-8", xml_declaration=True)

def process_children(node, path):
    chs = node.i_children
    for ch in chs:
        if ch.keyword in ["choice", "case"]:
            process_children(ch, path)
            continue
        p = path + "/" + qname(ch)
        tmpl = xsl_template(p)
        nt = xsl_calltemplate(ch.keyword, tmpl)
        if [c.arg for c in chs].count(ch.arg) > 1:
            xsl_withparam("nsid", ch.i_module.i_modulename + ":", nt)
        if ch.keyword in ["leaf", "leaf-list"]:
            type_param(ch, nt)
        elif ch.keyword != "anyxml":
            process_children(ch, p)

def type_param(node, ct):
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
             "uint8", "uint16", "uint32", "uint64"]:
        typ = "unquoted"
    elif t == "empty":
        typ = "empty"
    elif t == "instance-identifier":
        typ = "instance-identifier"
    elif t == "string":
        typ = "string"
    else:
        typ = "other"
    xsl_withparam("type", typ, ct)

def qname(node):
    return node.i_module.i_prefix + ":" + node.arg

def xsl_template(name):
    return ET.SubElement(ss, "template" , match = name) 

def xsl_text(text, parent):
    res = ET.SubElement(parent, "text")
    res.text = text
    return res

def xsl_calltemplate(name, parent):
    return ET.SubElement(parent, "call-template", name=name)

def xsl_withparam(name, value, parent):
    res = ET.SubElement(parent, "with-param", name=name)
    res.text = value
    return res
