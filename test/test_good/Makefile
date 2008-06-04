PYANG = pyang

MODULES = $(wildcard *.yang)

test:
	@for m in $(MODULES); do 					\
		echo -n "checking $$m...";				\
		$(PYANG) $$m || exit 1;					\
		echo -n " generating xsd...";				\
		$(PYANG) -f xsd -o $$m.xsd $$m || exit 1;		\
		echo -n " generating yin...";				\
		$(PYANG) -f yin -o $$m.yin $$m || exit 1;		\
		echo -n " generating xsd from the generated yin...";	\
		$(PYANG) -f xsd -o $$m.yin.xsd $$m.yin || exit 1;	\
		echo -n " comparing the two xsd..."			\
		diff expect/$$m.xsd $$m.yin.xsd > $$m.diff || 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo " ok";						\
	done

clean:
	rm -rf *.xsd *.yin
