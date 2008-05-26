PYANG = pyang --plugindir ../plugins

MODULES = $(wildcard *.yang)

test:
	for m in $(MODULES); do 				\
		echo -n "trying $$m...";			\
		$(PYANG) $$m || exit 1;				\
		echo -n " xsd...";				\
		$(PYANG) -f xsd -o $$m.xsd $$m || exit 1;	\
		echo -n " yin...";				\
		$(PYANG) -f yin -o $$m.yin $$m || exit 1;	\
		echo " ok";					\
	done

clean:
	rm -rf *.xsd *.yin
