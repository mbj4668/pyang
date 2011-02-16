BASE = aug-acme-system
PYANG_XSLT_DIR = ../../xslt
RNG_LIB = ../../schema/relaxng-lib.rng
MODULES = acme-system.yang extra-interface-nodes.yang
FILES = $(BASE).dsdl $(BASE)-data.rng $(BASE)-gdefs.rng \
        $(BASE)-data.sch $(BASE)-data.dsrl $(BASE)-data-dsrl.xsl \
        $(BASE)-data-wdef.xml $(BASE)-data-sch.xsl $(BASE)-data.svrl
.PHONY: all schemas clean

all: $(FILES)

$(BASE).dsdl: $(MODULES)
	pyang -f dsdl $^ | xmllint --format - > $@

$(BASE)-data.rng: $(BASE).dsdl
	xsltproc --stringparam target data \
	--stringparam basename $(BASE) --stringparam rng-lib $(RNG_LIB) \
	$(PYANG_XSLT_DIR)/gen-relaxng.xsl $< | xmllint --format - > $@

$(BASE)-gdefs.rng: $(BASE).dsdl
	xsltproc --stringparam gdefs-only 1 \
	$(PYANG_XSLT_DIR)/gen-relaxng.xsl $< | xmllint --format - > $@

$(BASE)-data.sch: $(BASE).dsdl
	xsltproc --stringparam target data \
	$(PYANG_XSLT_DIR)/gen-schematron.xsl $< | xmllint --format - > $@

$(BASE)-data.dsrl: $(BASE).dsdl
	xsltproc --stringparam target data \
	$(PYANG_XSLT_DIR)/gen-dsrl.xsl $< | xmllint --format - > $@

$(BASE)-data-dsrl.xsl: $(BASE)-data.dsrl
	xsltproc $(PYANG_XSLT_DIR)/dsrl2xslt.xsl $< | xmllint --format - > $@

$(BASE)-data-wdef.xml: $(BASE)-data-dsrl.xsl $(BASE)-data.xml
	xsltproc $^ | xmllint --format - > $@

$(BASE)-data-sch.xsl: $(BASE)-data.sch
	xsltproc $(PYANG_XSLT_DIR)/iso_abstract_expand.xsl $< | \
	xsltproc $(PYANG_XSLT_DIR)/iso_svrl_for_xslt1.xsl - | \
	xmllint --format - > $@

$(BASE)-data.svrl: $(BASE)-data-sch.xsl $(BASE)-data-wdef.xml
	xsltproc $^ | xmllint --format - > $@

clean:
	rm -f $(FILES)