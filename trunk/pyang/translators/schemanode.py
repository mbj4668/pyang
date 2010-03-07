from xml.sax.saxutils import escape

class SchemaNode(object):

    """Generic node in the schema.

    Instance variables:

    * `interleave` - signal whether children should be interleaved.

    * `occur` - 0=optional, 1=implicit, 2=mandatory, 3=presence

    Class variables:

    * `ser_format` - dictionary of methods returning string
      serialization formats
    """
    def element(cls, name, parent=None, interleave=None, occur=0):
        """Create an element node."""
        node = cls("element", parent, interleave=interleave)
        node.attr["name"] = name
        node.occur = occur
        return node
    element = classmethod(element)

    def leaf_list(cls, name, parent=None, interleave=None):
        """Create list node for a leaf-list."""
        node = cls("_list_", parent, interleave=interleave)
        node.attr["name"] = name
        node.keys = None
        node.minEl = "0"
        node.maxEl = None
        return node
    leaf_list = classmethod(leaf_list)

    def list(cls, name, parent=None, interleave=None):
        """Create list node for a list."""
        node = cls.leaf_list(name, parent, interleave=interleave)
        node.keys = None
        node.keymap = {}
        node.occur = 3
        return node
    list = classmethod(list)

    def choice(cls, parent=None, occur=0):
        """Create choice node."""
        node = cls("choice", parent)
        node.occur = occur
        node.default_case = None
        return node
    choice = classmethod(choice)

    def case(cls, parent=None):
        """Create case node."""
        node = cls("case", parent)
        node.occur = 0
        return node
    case = classmethod(case)

    def define(cls, name, parent=None, interleave=False):
        """Create define node."""
        node = cls("define", parent, interleave=interleave)
        node.occur = 0
        node.attr["name"] = name
        return node
    define = classmethod(define)

    def __init__(self, name, parent=None, text="", interleave=None):
        """Initialize the object under `parent`.
        """
        self.name = name
        self.parent = parent
        if parent is not None: parent.children.append(self)
        self.text = text
        self.adjust_interleave(interleave)
        self.children = []
        self.attr = {}

    def adjust_interleave(self, interleave):
        """Inherit interleave status from parent if undefined."""
        if interleave == None and self.parent:
            self.interleave = self.parent.interleave
        else:
            self.interleave = interleave

    def subnode(self, node):
        """Make `node` receiver's child."""
        self.children.append(node)
        node.parent = self
        node.adjust_interleave(None)

    def set_attr(self, key, value):
        self.attr[key] = value
        return self

    def data_nodes_count(self):
        """Return the number of receiver's data subnodes."""
        return len([ch for ch in self.children
                    if ch.name in ("element", "choice", "list")])

    def start_tag(self, alt=None, empty=False):
        """Return XML start tag for the receiver."""
        if alt:
            name = alt
        else:
            name = self.name
        result = "<" + name
        for it in self.attr:
            result += ' %s="%s"' % (it, escape(self.attr[it]))
        if empty:
            return result + "/>"
        else:
            return result + ">"

    def end_tag(self, alt=None):
        """Return XML end tag for the receiver."""
        if alt:
            name = alt
        else:
            name = self.name
        return "</" + name + ">"

    def serialize(self, occur=None):
        """Return RELAX NG representation of the receiver and subtree.
        """
        return (self.ser_format.get(self.name, SchemaNode._default_format)
                (self, occur) % (escape(self.text) + ''.join
                                 ([ch.serialize() for ch in self.children])))

    def _default_format(self, occur):
        if self.text or self.children:
            return self.start_tag() + "%s" + self.end_tag()
        else:
            return self.start_tag(empty=True) + "%s"

    def _define_format(self, occur):
        if hasattr(self, "default"):
            self.attr["nma:default"] = self.default
        return self._default_format(None)

    def _element_format(self, occur):
        if occur:
            occ = occur
        else:
            occ = self.occur
        if occ == 1:
            if hasattr(self, "default"):
                self.attr["nma:default"] = self.default
            else:
                self.attr["nma:implicit"] = "true"
        fmt = self.start_tag() + self._chorder() + self.end_tag()
        if (occ == 2 or self.parent.name == "choice"
            or self.parent.name == "case" and self.data_nodes_count() == 1):
            return fmt
        else:
            return "<optional>" + fmt + "</optional>"

    def _chorder(self):
        """Add <interleave> if child order is arbitrary."""
        if self.interleave and self.data_nodes_count() > 1:
            return "<interleave>%s</interleave>"
        return "%s"

    def _list_format(self, occur):
        if self.keys:
            self.attr["nma:keys"] = " ".join(self.keys)
            keys = ''.join([self.keymap[k].serialize(occur=2)
                            for k in self.keys])
        else:
            keys = ""
        if self.maxEl:
            self.attr["nma:max-elements"] = self.maxEl
        if self.minEl == "0":
            ord_ = "zeroOrMore"
        else:
            ord_ = "oneOrMore"
            self.attr["nma:min-elements"] = self.minEl
        return ("<" + ord_ + ">" + self.start_tag("element") + keys +
                self._chorder() + self.end_tag("element") + "</" + ord_ + ">")

    def _choice_format(self, occur):
        fmt = self.start_tag() + "%s" + self.end_tag()
        if self.occur < 2:
            return "<optional>" + fmt + "</optional>"
        else:
            return fmt

    def _case_format(self, occur):
        if self.occur == 1:
            self.attr["nma:implicit"] = "true"
        if len(self.children) == 1 or not self.interleave:
            return self.start_tag("group") + "%s" + self.end_tag("group")
        else:
            return (self.start_tag("interleave") + "%s" +
                    self.end_tag("interleave"))

    ser_format = { "element": _element_format,
                   "_list_": _list_format,
                   "choice": _choice_format,
                   "case": _case_format,
                   "define": _define_format,
                   }
