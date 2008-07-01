#
# Just drop .mib files here and do make all; make gen-xml
#
PYANG ?= pyang
# need smidump 0.4.7 or later
SMIDUMP ?= smidump

MIB_SOURCES  := $(wildcard *.mib)
YANG_OBJECTS := $(MIB_SOURCES:%.mib=%.yang)
YIN_OBJECTS := $(MIB_SOURCES:%.mib=%.yin)
XSD_OBJECTS := $(MIB_SOURCES:%.mib=%.xsd)
DSDL_OBJECTS := $(MIB_SOURCES:%.mib=%.rng)
XML_OBJECTS := $(MIB_SOURCES:%.mib=%.xml)
STD_MODULES := yang-types.yang inet-types.yang ieee-types.yang
STD_XSD := $(STD_MODULES:%.yang=%.xsd)

all: $(STD_XSD) yang yin xsd dsdl

test: all gen-xml

yang-types.yang:
	cp ../../modules/$@ $@
inet-types.yang:
	cp ../../modules/$@ $@
ieee-types.yang:
	cp ../../modules/$@ $@

gen-xml: 
	rm -f $(XML_OBJECTS)
	$(MAKE) xml

yang: $(YANG_OBJECTS)
yin: $(YIN_OBJECTS)
xsd: $(XSD_OBJECTS)
dsdl: $(DSDL_OBJECTS)
xml: $(XML_OBJECTS)

%.yang:	%.mib
	$(SMIDUMP) -f yang $< -o $@

%.yin:	%.yang
	$(PYANG) -f yin $< -o $@

%.xsd:	%.yang
	$(PYANG) -f xsd $< -o $@

%.rng:	%.yang
	$(PYANG) -f dsdl $< -o $@

%.xml: %.yang
	@echo "generating random xml document for $<..."
	@$(PYANG) --plugindir ../plugins -f xml $< > $@
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
	   str=`xmllint --noout --relaxng $${rng} $@ 2>&1 |         \
                grep -v __foo__ | grep -v 'validate'`;              \
	   if [ ! -z "$${str}" ]; then                              \
	      echo $${str};                                         \
	      exit 1;                                               \
           fi; )

clean:
	rm -f $(YANG_OBJECTS) $(XSD_OBJECTS) $(YIN_OBJECTS) $(XML_OBJECTS) \
		$(STD_MODULES) $(STD_XSD)
