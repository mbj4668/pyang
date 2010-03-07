class SchemaNode(object):

    """Generic node in the schema.

    Instance variables:

    * `occur` - 0=optional, 1=implicit, 2=mandatory, 3=presence

    Class variables:

    * `interleave` - signal whether children should be interleaved.

    * `ser_format` - dictionary of methods returning string
      serialization formats
    """

    interleave = True

    def element(cls, name, parent=None):
        """Create an element node."""
        node = cls("element", parent)
        node.attr["name"] = name
        node.occur = 0
        return node
    element = classmethod(element)

    def leaf_list(cls, name, prefix, parent=None):
        """Create list node for a leaf-list."""
        node = cls("list", parent)
        node.attr["name"] = name
        node.minEl = "0"
        return node
    leaf_list = classmethod(leaf_list)

    def list(cls, name, parent=None):
        """Create list node for a list."""
        node = cls.leaf_list(name, parent)
        node.keys = {}
        return node
    list = classmethod(list)

    def choice(cls, parent=None):
        """Create choice node."""
        node = cls("choice", parent)
        node.occur = 0
        return node
    choice = classmethod(choice)

    def case(cls, parent=None):
        """Create case node."""
        node = cls("case", parent)
        return node
    case = classmethod(case)

    def __init__(self, name, parent=None, text=""):
        """Initialize the object under `parent`.
        """
        self.name = name
        self.parent = parent
        if parent is not None: parent.children.append(self)
        self.children = []
        self.attr = {}
        self.text = text

    def subnode(self, node):
        """Make `node` receiver's child."""
        self.children.append(node)
        node.parent = self

    def set_attr(self, key, value):
        self.attr[key] = value
        return self

    def data_children_count(self):
        """Check whether the receiver has more data children."""
        return len([ ch for ch in self.children
                     if ch.name in ("element", "choice", "list") ])

    def start_tag(self, alt=None, empty=False):
        """Return XML start tag for the receiver."""
        if alt:
            name = alt
        else:
            name = self.name
        result = "<" + name 
        for it in self.attr.items():
            result += ' %s="%s"' % it
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

    def serialize(self):
        """Return RELAX NG representation of the receiver and subtree.
        """
        return (self.ser_format.get(self.name,
                                    SchemaNode._default_format)(self) %
                (self.text +
                 ''.join([ch.serialize() for ch in self.children])))

    def _default_format(self):
        if self.text or self.children:
            return self.start_tag() + "%s" + self.end_tag()
        else:
            return self.start_tag(empty=True) + "%s"

    def _element_format(self):
        if hasattr(self, "default"):
            self.attr["nma:default"] = self.default
        elif self.occur == 1:
            self.attr["nma:implicit"] = "true"
        if self.interleave and self.data_children_count() > 1:
            fmt = "<interleave>%s</interleave>"
        else:
            fmt = "%s"
        fmt = self.start_tag() + fmt + self.end_tag()
        if self.occur < 2:
            return "<optional>" + fmt + "</optional>"
        else:
            return fmt

    def _list_format(self):
        mc = int(self.minEl)
        if hasattr(self, "maxEl"):
            self.attr["nma:max-elements"] = self.maxEl
        if mc > 1:
            self.attr["nma:min-elements"] = self.minEl
        fmt = self.start_tag("element") + "%s" + self.end_tag("element")
        if mc > 0:
            return "<oneOrMore>" + fmt + "</oneOrMore>"
        else:
            return "<zeroOrMore>" + fmt + "</zeroOrMore>"

    def _choice_format(self):
        fmt = self.start_tag() + "%s" + self.end_tag()
        if self.occur < 2:
            return "<optional>" + fmt + "</optional>"
        else:
            return fmt

    def _case_format(self):
        if self.occur == 1:
            self.attr["nma:implicit"] = "true"
        if self.data_children_count() == 1 or not self.interleave:
            return self.start_tag("group") + "%s" + self.end_tag("group")
        else:
            return (self.start_tag("interleave") + "%s" +
                    self.end_tag("interleave"))

    ser_format = { "element": _element_format,
                   "list": _list_format,
                   "choice": _choice_format,
                   "case": _case_format,
                   }
