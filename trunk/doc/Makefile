DBSS=/usr/share/xml/docbook/stylesheet/docbook-xsl/manpages/docbook.xsl
MANPAGES=../man/man1/yang2dsdl.1
.PHONY=all

all: $(MANPAGES)

../man/man1/%.1: %.1.dbk
	xsltproc -o $@ $(DBSS) $<
