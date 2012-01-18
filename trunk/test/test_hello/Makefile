HELLO = hello-server.xml
MODULES = test-hello-a.yin test-hello-b.yin
YANG-LIBDIR ?= ~/lib/yang/
TARGET ?= get-reply
BASE ?= htest
SCHEMAS = $(BASE)-$(TARGET).rng $(BASE)-$(TARGET).sch $(BASE)-$(TARGET).dsrl
INSTANCE = $(BASE)-$(TARGET).xml
Y2DOPTS = -L -t $(TARGET) -b $(BASE)
.PHONY: all schemas clean validate

all: $(SCHEMAS)

$(SCHEMAS): $(HELLO) $(MODULES)
	yang2dsdl $(Y2DOPTS) $(FULLEXT) $<

clean:
	rm -f $(SCHEMAS) $BASE.{dsdl,tree} *-gdefs.rng *.rnc

test: $(INSTANCE) $(SCHEMAS)
	yang2dsdl -j -s $(Y2DOPTS) -v $<

$(BASE).dsdl: $(HELLO) $(MODULES)
	pyang -f dsdl --dsdl-no-documentation $(FULLEXT) $< \
	| xmllint --format - > $@

$(BASE).tree: $(HELLO) $(MODULES)
	pyang -f tree -o $@ $(FULLEXT) $<
