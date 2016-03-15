# ifeq ($(DBSS),)
#   DBSS=$(wildcard /usr/share/xml/docbook/stylesheet/docbook-xsl/manpages/docbook.xsl)
# endif
# ifeq ($(DBSS),)
#   DBSS=$(wildcard /usr/share/sgml/docbook/stylesheet/docbook-xsl/manpages/docbook.xsl)
# endif
# ifeq ($(DBSS),)
#   $(error docbook stylesheet not found)
# endif

# NOTE: 1.79.1 generates bad man pages; they don't render properly
#DBURI=http://docbook.sourceforge.net/release/xsl/current
DBURI=http://docbook.sourceforge.net/release/xsl/1.78.1
MANPAGES=../man/man1/yang2dsdl.1 ../man/man1/pyang.1 ../man/man1/json2xml.1

PYANG_VERSION=$(shell grep __version__ ../pyang/__init__.py | \
	        awk -F\' '{print $$2}')
DATE=$(shell grep __date__ ../pyang/__init__.py | \
	        awk -F\' '{print $$2}')

all: $(MANPAGES)

.PHONY: clean
clean:
	rm -f $(MANPAGES)

../man/man1/%.1: %.1.dbk
	cat $< | \
	  sed -e 's/%PYANG_VERSION%/$(PYANG_VERSION)/g' \
	      -e 's/%DATE%/$(DATE)/g' | \
	  xsltproc -o $@ $(DBURI)/manpages/docbook.xsl -

%.1.html: %.1.dbk
	cat $< | \
	  sed -e 's/%PYANG_VERSION%/$(PYANG_VERSION)/g' \
	      -e 's/%DATE%/$(DATE)/g' | \
	  xsltproc -o $@ $(DBURI)/xhtml/docbook.xsl -
