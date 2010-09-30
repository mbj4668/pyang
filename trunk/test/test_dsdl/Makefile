PYANG_RNG_LIBDIR = ../../schema
PYANG_XSLT_DIR = ../../xslt
YANG2DSDL := ../../bin/yang2dsdl

results := $(patsubst %.xml,%.log,$(wildcard *.xml))

.PHONY = all clean

all: $(results) 

%-data.log: %-data.xml %.yin
	$(YANG2DSDL) -t data -v $^ > $@

%-config.log: %-config.xml %.yin
	$(YANG2DSDL) -t config -v $^ > $@

%-get-reply.log: %-get-reply.xml %.yin
	$(YANG2DSDL) -t get-reply -v $^ > $@

%-get-config-reply.log: %-get-config-reply.xml %.yin
	$(YANG2DSDL) -t get-config-reply -v $^ > $@

%-rpc.log: %-rpc.xml %.yin
	$(YANG2DSDL) -t rpc -v $^ > $@

%-rpc-reply.log: %-rpc-reply.xml %.yin
	$(YANG2DSDL) -t rpc-reply -v $^ > $@

%-notification.log: %-notification.xml %.yin
	$(YANG2DSDL) -t notification -v $^ > $@

clean:
	rm -f *.log *.rng *.dsrl *.sch


