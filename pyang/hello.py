import xml.parsers.expat, sys, re

NC_NS_URI ="urn:ietf:params:xml:ns:netconf:base:1.0"
YAM_URI = re.compile(r".+\?(\S+)\s*")

class HelloParser:

    def __init__(self):
        self.modules = {}
        self.depth = self.state = 0
        self.buffer = ""
        self.parser = xml.parsers.expat.ParserCreate(namespace_separator=' ')
        self.parser.CharacterDataHandler = self.handleCharData
        self.parser.StartElementHandler = self.handleStartElement
        self.parser.EndElementHandler = self.handleEndElement

    def handleCharData(self, data):
        if self.state == self.depth == 3:
            self.buffer += data

    def handleStartElement(self, data, attrs):
        ns_uri, tag = data.split()
        if ns_uri == NC_NS_URI:
            if self.state == self.depth == 0 and tag == "hello":
                self.state = 1
            elif self.state == self.depth == 1 and tag == "capabilities":
                self.state = 2
            elif self.state == self.depth == 2 and tag == "capability":
                self.state = 3
        self.depth += 1
            
    def handleEndElement(self, data):
        ns_uri, tag = data.split()
        if ns_uri == NC_NS_URI:
            if self.state == self.depth == 1 and tag == "hello":
                self.state = 0
            elif self.state == self.depth == 2 and tag == "capabilities":
                self.state = 1
            elif self.state == self.depth == 3 and tag == "capability":
                m = YAM_URI.search(self.buffer)
                if m:
                    self.parse_parameters(m.group(1))
                self.buffer = ""
                self.state = 2
        self.depth -= 1

    def parse_parameters(self, data):
        pars = dict([ x.split("=") for x in data.split("&") ])
        if "module" not in pars: return
        mnam = pars["module"]
        if "revision" in pars:
            rev=pars["revision"]
        else:
            rev=None
        if "features" in pars:
            self.modules[(mnam,rev)] = pars["features"].split(",")
        else:
            self.modules[(mnam,rev)] = []

    def get_modules(self, fd):
        self.parser.ParseFile(fd)
        return self.modules

