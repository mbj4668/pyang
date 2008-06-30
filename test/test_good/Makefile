PYANG = pyang

MODULES = $(wildcard *.yang)

test: clean
	@for m in $(MODULES); do 					\
		echo -n "checking $$m...";				\
		$(PYANG) $$m || exit 1;					\
		echo -n " generating xsd...";				\
		$(PYANG) -f xsd -o $$m.xsd $$m || exit 1;		\
		echo " generating yin...";				\
		$(PYANG) -f yin -o $$m.yin $$m || exit 1;		\
		echo -n " ";						\
		echo -n " generating xsd from the generated yin...";	\
		$(PYANG) -f xsd -o $$m.yin.xsd $$m.yin || exit 1;	\
		echo " comparing the two xsd...";			\
		diff $$m.xsd $$m.yin.xsd > $$m.diff || 			\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo -n " ";						\
		echo -n " generating yang...";				\
		$(PYANG) -f yang -o $$m.gen.yang $$m || exit 1;		\
		echo " generating yin from the generated yang...";	\
		$(PYANG) -f yin -o $$m.gen.yin $$m.gen.yang || exit 1;	\
		echo -n " ";						\
		echo -n " comparing the two generated yin...";		\
		diff $$m.yin $$m.gen.yin > $$m.diff ||	 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo -n " generating DSDL...";				\
		$(PYANG) -f dsdl -o $$m.rng $$m || exit 0;		\
		echo " ok";						\
	done

clean:
	rm -rf *.xsd *.yin *.gen.* *.rng
