PYANG_RNG_LIBDIR = ../../schema
PYANG_XSLT_DIR = ../../xslt
YANG2DSDL ?= ../../bin/yang2dsdl

results := $(patsubst %.xml,%.log,$(wildcard *.xml))

.PHONY = all clean

all: $(results) 

test: all

%-data.log: %-data.xml %.yin
	$(YANG2DSDL) -t data -v $^ > $@

%-config.log: %-config.xml %.yin
	$(YANG2DSDL) -t config -v $^ > $@

%-get-reply.log: %-get-reply.xml %.yin
	$(YANG2DSDL) -t get-reply -v $^ > $@

%-get-config-reply.log: %-get-config-reply.xml %.yin
	$(YANG2DSDL) -t get-config-reply -v $^ > $@

%-edit-config.log: %-edit-config.xml %.yin
	$(YANG2DSDL) -t edit-config -v $^ > $@

%-rpc.log: %-rpc.xml %.yin
	$(YANG2DSDL) -t rpc -v $^ > $@

%-rpc-reply.log: %-rpc-reply.xml %.yin
	$(YANG2DSDL) -t rpc-reply -v $^ > $@

%-notification.log: %-notification.xml %.yin
	$(YANG2DSDL) -t notification -v $^ > $@

ll-2mod-%.log: ll-2mod-%.xml ll-2mod-*.yin ll-2sub-b.yin
	$(YANG2DSDL) -t $* -b ll-2mod -v $< ll-2mod-[ab].yin > $@

clean:
	rm -f *.log *.tmp *.rng *.dsrl *.sch
