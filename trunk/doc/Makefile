ifeq ($(DBSS),)
  DBSS=$(wildcard /usr/share/xml/docbook/stylesheet/docbook-xsl/manpages/docbook.xsl)
endif
ifeq ($(DBSS),)
  DBSS=$(wildcard /usr/share/sgml/docbook/stylesheet/docbook-xsl/manpages/docbook.xsl)
endif
ifeq ($(DBSS),)
  $(error docbook stylesheet not found)
endif

MANPAGES=../man/man1/yang2dsdl.1 ../man/man1/pyang.1

PYANG_VERSION=$(shell grep __version__ ../pyang/__init__.py | \
	        awk -F\' '{print $$2}')
DATE=$(shell grep __date__ ../pyang/__init__.py | \
	        awk -F\' '{print $$2}')

all: $(MANPAGES)

.PHONY: clean
clean:
	rm $(MANPAGES)

../man/man1/%.1: %.1.dbk
	cat $< | \
	  sed -e 's/%PYANG_VERSION%/$(PYANG_VERSION)/g' \
	      -e 's/%DATE%/$(DATE)/g' | \
	  xsltproc -o $@ $(DBSS) -
