PYANG = pyang -Werror -WWBAD_MODULE_NAME

MODULES ?= $(wildcard *.yang)

test: clean
	@for m in $(MODULES); do 					\
		echo -n "checking $$m...";				\
		$(PYANG) $$m || exit 1;					\
		echo " generating yin...";				\
		$(PYANG) -f yin -o $$m.yin $$m || exit 1;		\
		echo -n " ";						\
		echo -n " generating yang from generated yin...";	\
		$(PYANG) -f yang -o $$m.gen.yang $$m.yin || exit 1;     \
		echo -n " comparing the two yang...";			\
		diff -bw $$m $$m.gen.yang > $$m.diff ||	 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo " ok";						\
	done

clean:
	rm -rf *.yin *.gen.* *.diff
