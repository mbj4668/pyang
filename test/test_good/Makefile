PYANG = pyang -Werror -WWBAD_MODULE_NAME

MODULES ?= $(wildcard *.yang)

test: clean utf8-test
	@for m in $(MODULES); do 					\
		echo -n "checking $$m...";				\
		$(PYANG) $$m || exit 1;					\
		echo " generating yin...";				\
		$(PYANG) -f yin -o $$m.yin $$m || exit 1;		\
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
		(grep '^submodule' $$m > /dev/null || $(PYANG) -f dsdl -o $$m.dsdl $$m) || exit 0;	\
		echo " ok";						\
	done

utf8-test:
	pyang -f yang q.yang || exit 1; \
	pyang -f yang q.yang > x || exit 1; \
	pyang -f yang q.yang -o x || exit 1; \
	rm -f x

clean:
	rm -rf *.yang.yin *.gen.* *.dsdl
