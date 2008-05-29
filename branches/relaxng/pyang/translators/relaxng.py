"""This module implements translator from YANG to RELAX NG.

"""

__docformat__ = "reStructuredText"

import sys
import xml.etree.ElementTree as ET

class RelaxNGTranslator(object):

    """Instances of this class translate YANG to RELAX NG.

    Instance variables:
    
    * yang_mod: instance of `YangModule`

    """

    grammar_attrs = {
        "xmlns" : "http://relaxng.org/ns/structure/1.0",
        "datatypeLibrary" : "http://www.w3.org/2001/XMLSchema-datatypes",
        "xmlns:a": "http://relaxng.org/ns/compatibility/annotations/1.0",
    }
    """Fixed attributes of the root ``grammar`` element."""

    datatype_map = {
        "string" : "string",
        "int8": "byte",
        "int16": "short",
        "int32": "int",
        "int64": "long",
        "uint8": "unsignedByte",
        "uint16": "unsignedShort",
        "uint32": "unsignedInt",
        "uint64": "unsignedLong",
        "float32": "float",
        "float64": "double",
        "boolean": "boolean",
    }

    def __init__(self):
        """Initialize the instance.
        """

        self.handler = {
            "leaf": self.new_element,
            "leaf-list": self.new_list,
            "list": self.new_list,
            "container": self.new_element,
            "description": self.handle_description,
            "namespace": self.handle_namespace,
            "prefix": self.noop,
            "type": self.handle_type,
            "typedef" : self.handle_reusable,
            "grouping" : self.handle_reusable,
            "uses" : self.handle_uses,
            "enum" : self.handle_enum,
            "import" : self.noop
        }

        self.imported_symbols = {}

    def translate(self, yang_mod):
        """Translate `yang_mod` to etree with corresponding RELAX NG schema.
        """
        yang_mod.pull_imports()
        self.root_elem = ET.Element("grammar", self.grammar_attrs)
        start = ET.SubElement(self.root_elem, "start")
        for sub in yang_mod.root: self.handle(sub, start)
        return ET.ElementTree(element=self.root_elem)
        
    def handle(self, y_stmt, p_elem):
        """Run handler method for `y_stmt` ini the context of p_elem.
        """
        try:
            handler = self.handler[y_stmt.keyword]
        except KeyError:
            sys.stderr.write("%s not handled\n" % y_stmt.keyword)
        else:
            handler(y_stmt, p_elem)

    # Handlers for YANG statements

    def noop(self, y_stmt, p_elem):
        pass

    def new_element(self, y_stmt, p_elem):
        elem = ET.SubElement(p_elem, "element", name=y_stmt.argument)
        for sub in y_stmt: self.handle(sub, elem)

    def new_list(self, y_stmt, p_elem):
        cont = ET.SubElement(p_elem, "zeroOrMore")
        elem = ET.SubElement(cont, "element", name=y_stmt.argument)
        for sub in y_stmt: self.handle(sub, elem)

    def handle_description(self, y_stmt, p_elem):
        elem = ET.Element("a:documentation")
        p_elem.insert(0, elem)
        elem.text = y_stmt.argument

    def handle_namespace(self, y_stmt, p_elem):
        self.root_elem.attrib["ns"] = y_stmt.argument

    def handle_type(self, y_stmt, p_elem):
        arg = y_stmt.argument
        if arg in ("enumeration", "union"):
            elem = ET.SubElement(p_elem, "choice")
        elif ":" in arg:        # foreign type
            pref, typ = arg.split(":")
        else:
            elem = ET.SubElement(p_elem, "data",
                                 type=self.datatype_map[arg])
        for sub in y_stmt: self.handle(sub, elem)

    def handle_reusable(self, y_stmt, p_elem):
        """Handle ``typedef`` or ``grouping``."""
        elem = ET.SubElement(self.root_elem, "define",
                             name="__".join(y_stmt.full_path() +
                                            [y_stmt.argument]))
        for sub in y_stmt: self.handle(sub, elem)
        
    def handle_uses(self, y_stmt, p_elem):
        ident = y_stmt.argument
        parent = y_stmt.parent
        while parent is not None:
            grp = parent.get_by_kw_and_arg("grouping", ident)
            if grp != []:
                break
            parent = parent.parent
        ET.SubElement(p_elem, "ref",
                      name="__".join(grp[0].full_path() + [ident]))

    def handle_enum(self, y_stmt, p_elem):
        elem = ET.SubElement(p_elem, "value")
        elem.text = y_stmt.argument
        for sub in y_stmt: self.handle(sub, elem)
        
