MODULES = amod.yang bmod.yang
SUBMODULES = asub.yang
TARGET ?= data
BASE ?= test
SCHEMAS = $(BASE)-$(TARGET).rng $(BASE)-$(TARGET).sch $(BASE)-$(TARGET).dsrl
XINSTANCE = $(BASE)-$(TARGET).xml
JINSTANCE = $(BASE)-$(TARGET)-new.json
Y2DOPTS = -t $(TARGET) -b $(BASE)
.PHONY = all test clean validate compare

all: model.xsl model.jtox validate compare
	@echo
	@echo == All tests OK.

test: all

compare: $(BASE)-$(TARGET).json $(JINSTANCE)
	@echo
	@echo == Comparing original and generated JSON
	@./cmpjson.py $^

model.xsl: hello.xml $(MODULES) $(SUBMODULES)
	@echo
	@echo == Generating $@
	@pyang -o $@ -f jsonxsl --hello $<

model.jtox: hello.xml $(MODULES) $(SUBMODULES)
	@echo
	@echo == Generating $@
	@pyang -o $@ -f jtox --hello $<

$(XINSTANCE): model.jtox $(BASE)-$(TARGET).json
	@echo
	@echo == Generating $@
	@json2xml -t $(TARGET) -o $@ $^

$(JINSTANCE): model.xsl $(XINSTANCE)
	@echo
	@echo == Generating $@
	@xsltproc -o $@ $^

$(SCHEMAS): hello.xml $(MODULES) $(SUBMODULES)
	@yang2dsdl -L $(Y2DOPTS) $<

%.rnc: %.rng
	@trang -I rng -O rnc $< $@

clean:
	@rm -f $(SCHEMAS) $(XINSTANCE) $(JINSTANCE) model.* *-gdefs.rng *.rnc

validate: $(XINSTANCE) $(SCHEMAS)
	@yang2dsdl -j -s $(Y2DOPTS) -v $<
