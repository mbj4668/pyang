MANPAGES=$(patsubst %.1.md,../man/man1/%.1,$(wildcard *.1.md))

VERSION=$(shell grep __version__ ../pyang/__init__.py | \
	        awk -F\' '{print $$2}')
DATE=$(shell grep __date__ ../pyang/__init__.py | \
	        awk -F\' '{print $$2}')

all: $(MANPAGES)

.PHONY: clean
clean:
	rm -f $(MANPAGES)

../man/man1/%.1: %.1.md
	cat $< | \
	  sed -e 's/_VERSION_/$(VERSION)/g' \
	      -e 's/_DATE_/$(DATE)/g' | \
	  pandoc - -s -t man -o $@
