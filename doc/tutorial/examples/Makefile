MODULES = turing-machine
YMOD = $(addsuffix .yang, $(MODULES))
WIKI = TuringMachine.wiki
TARGET ?= get-reply
BASE ?= turing-machine
Y2Y = ~/Projects/yang-tools/xslt/yin2yang.xsl
SCHEMAS = $(BASE)-$(TARGET).rng $(BASE)-$(TARGET).sch $(BASE)-$(TARGET).dsrl
XINSTANCE = $(BASE)-$(TARGET).xml
JINSTANCE = $(BASE)-$(TARGET).json
Y2DOPTS = -t $(TARGET) -b $(BASE)
.PHONY = all json clean validate install

all: $(SCHEMAS) $(BASE)-$(TARGET).rnc $(YMOD) model.jtox $(WIKI)

json: $(JINSTANCE)

model.xsl: $(YMOD)
	pyang -o $@ -f jsonxsl $<

model.jtox: $(YMOD)
	pyang -o $@ -f jtox $<

model.dsdl: $(YMOD)
	pyang -f dsdl --dsdl-no-documentation --dsdl-no-dublin-core $^ | \
	    xmllint --output $@ --format -

$(JINSTANCE): model.xsl $(XINSTANCE)
	xsltproc -o $@ $^

$(SCHEMAS): $(YMOD)
	yang2dsdl $(Y2DOPTS) $(YMOD)

TuringMachine.wiki: turing-machine.yang
	@echo "#summary Example YANG module" > $@
	@echo "{{{" >> $@
	@cat $< >> $@
	@echo "}}}" >> $@

%.yang: %.yinx
	xsltproc --output $@ $(Y2Y) $<

%.rnc: %.rng
	trang -I rng -O rnc $< $@

clean:
	rm -f $(SCHEMAS) $(JINSTANCE) $(YMOD) model.* \
	    $(BASE)-gdefs*.rng *.rnc TuringMachine.wiki

validate: $(XINSTANCE) $(SCHEMAS)
	yang2dsdl -j -s $(Y2DOPTS) -v $<

install: $(WIKI)
	cp $^ ~/Projects/pyang.wiki/
