#
# Just drop .mib files here and do make all; make gen-xml
#
PYANG := $(PYANG) -Wnone
# need smidump 0.4.7 or later
SMIDUMP ?= smidump

MIB_SOURCES  := $(wildcard *.mib)
YANG_OBJECTS := $(MIB_SOURCES:%.mib=%.yang)
YIN_OBJECTS := $(MIB_SOURCES:%.mib=%.yin)
XSD_OBJECTS := $(MIB_SOURCES:%.mib=%.xsd)
RNG_OBJECTS := $(MIB_SOURCES:%.mib=%.rng)
XML_OBJECTS := $(MIB_SOURCES:%.mib=%.xml)
XML2_OBJECTS := $(MIB_SOURCES:%.mib=%.xml.2)
STD_MODULES := ietf-yang-types.yang ietf-inet-types.yang ietf-yang-smiv2.yang
STD_XSD := $(STD_MODULES:%.yang=%.xsd)

test:
	@echo "disabled"

all: $(STD_XSD) yang yin xsd rng

xtest: all gen-xml

ietf-yang-types.yang:
	cp ../../modules/$@ $@
ietf-inet-types.yang:
	cp ../../modules/$@ $@
ietf-yang-smiv2.yang:
	cp ../../modules/$@ $@

gen-xml: 
	rm -f $(XML_OBJECTS) $(XML2_OBJECTS)
	$(MAKE) xml

yang: $(YANG_OBJECTS)
yin: $(YIN_OBJECTS)
xsd: $(XSD_OBJECTS)
rng: $(RNG_OBJECTS)
xml: $(XML_OBJECTS)

%.yang:	%.mib
	$(SMIDUMP) -f yang  $< > $@

%.yin:	%.yang
	$(PYANG) -f yin $< -o $@

%.xsd:	%.yang
	$(PYANG) -f xsd $< -o $@

%.rng:	%.yang
	$(PYANG) -f rng $< -o $@

%.xml: %.yang
	@echo "generating random xml document for $<..."
	@$(PYANG) --plugindir ../plugins -f xml $< > $@
	@echo '<netmod-tree xmlns="urn:ietf:params:xml:ns:netmod:tree:1"><top>' \
	  > $@.2
	@cat $@ >> $@.2
	@echo '</top></netmod-tree>' >> $@.2
	@echo "validating against generated XSD..."
	@( if [ ! -s $@ ]; then                                     \
               exit 0;                                              \
           fi;                                                      \
           xsd=`basename $@ .xml`.xsd;                              \
	   str=`xmllint --noout --schema $${xsd} $@ 2>&1 |          \
                grep -v __foo__ | grep -v 'validate'`;              \
	   if [ ! -z "$${str}" ]; then                              \
	      echo $${str};                                         \
	      exit 1;                                               \
           fi; )
	@echo "validating against generated RNG..."
	@( if [ ! -s $@ ]; then                                     \
               exit 0;                                              \
           fi;                                                      \
	   exit 0; # FIXME - remove this line \
           rng=`basename $@ .xml`.rng;                              \
	   str=`xmllint --noout --relaxng $${rng} $@.2 2>&1 |       \
                grep -v __foo__ | grep -v 'validate'`;              \
	   if [ ! -z "$${str}" ]; then                              \
	      echo $${str};                                         \
	      exit 1;                                               \
           fi; )

clean:
	rm -f $(YANG_OBJECTS) $(XSD_OBJECTS) $(YIN_OBJECTS) \
		$(XML_OBJECTS) $(XML2_OBJECTS) \
		$(STD_MODULES) $(STD_XSD) $(RNG_OBJECTS)
