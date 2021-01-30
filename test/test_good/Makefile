PYANGE := $(PYANG) -Werror -WWBAD_MODULE_NAME

test: clean utf8-test mef-ieee-test
	@for m in $(wildcard *.yang); do 				\
		echo "checking $$m..." | tr -d '\012';			\
		$(PYANGE) $$m || exit 1;				\
		echo " generating yin...";				\
		$(PYANGE) -f yin -o $$m.yin $$m || exit 1;		\
		echo " " | tr -d '\012';				\
		echo " generating yang from the generated yin...";	\
		$(PYANGE) -f yang -o $$m.gen.yang $$m.yin || exit 1;	\
		echo " " | tr -d '\012';				\
		echo " generating yang..." | tr -d '\012';		\
		$(PYANGE) -f yang -o $$m.gen.yang $$m || exit 1;	\
		echo " generating yin from the generated yang...";	\
		$(PYANGE) -f yin -o $$m.gen.yin $$m.gen.yang || exit 1;	\
		echo " " | tr -d '\012';				\
		echo " comparing the two generated yin..." | tr -d '\012';\
		diff $$m.yin $$m.gen.yin > $$m.diff ||	 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo " generating DSDL..." | tr -d '\012';		\
		(grep '^submodule' $$m > /dev/null			\
                || $(PYANGE) -f dsdl -o $$m.dsdl $$m || exit 0);	\
		echo " ok";						\
	done

utf8-test:
	$(PYANG) -f yang q.yang || exit 1; \
	$(PYANG) -f yang q.yang > x || exit 1; \
	$(PYANG) -f yang q.yang -o x || exit 1; \
	rm -f x

mef-ieee-test:
	$(PYANG) --mef mef-yt10.yang || exit 1; \
        $(PYANG) --mef mef-yt11.yang || exit 1; \
        $(PYANG) --ieee ieee-yt12.yang || exit 1;

clean:
	rm -rf *.yang.yin *.gen.* *.dsdl
