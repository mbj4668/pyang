PYANG = pyang -Wnone

MODULES = a b

test: clean ietf-inet-types.xsd
	@for m in $(MODULES); do 					\
		echo -n "checking $$m...";				\
		$(PYANG) $$m.yang || exit 1;				\
		echo -n " generating xsd...";				\
		$(PYANG) -f xsd -o $$m.xsd $$m.yang || exit 1;		\
		echo " check xsd and xml...";				\
		xmllint --noout --schema $$m.xsd $$m.xml || exit 1;		\
		echo " ok";						\
	done

ietf-inet-types.xsd: ../../modules/ietf-inet-types.yang
	$(PYANG) -f xsd $< -o $@

clean:
	rm -rf *.xsd


