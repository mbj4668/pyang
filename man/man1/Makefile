DBSS=/usr/share/xml/docbook/stylesheet/docbook-xsl/manpages/docbook.xsl
.PHONY=all

all: yang2dsdl.1

%.1: %.1.dbk
	xsltproc -o $@ $(DBSS) $<
