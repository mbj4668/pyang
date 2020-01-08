PYANG = pyang -Werror -WWBAD_MODULE_NAME

test: clean utf8-test mef-ieee-test
	@for m in $(wildcard *.yang); do 				\
		echo "checking $$m..." | tr -d '\012';			\
		$(PYANG) $$m || exit 1;					\
		echo " generating yin...";				\
		$(PYANG) -f yin -o $$m.yin $$m || exit 1;		\
		echo " " | tr -d '\012';				\
		echo " generating yang from the generated yin...";	\
		$(PYANG) -f yang -o $$m.gen.yang $$m.yin || exit 1;	\
		echo " " | tr -d '\012';				\
		echo " generating yang..." | tr -d '\012';		\
		$(PYANG) -f yang -o $$m.gen.yang $$m || exit 1;		\
		echo " generating yin from the generated yang...";	\
		$(PYANG) -f yin -o $$m.gen.yin $$m.gen.yang || exit 1;	\
		echo " " | tr -d '\012';				\
		echo " comparing the two generated yin..." | tr -d '\012';\
		diff $$m.yin $$m.gen.yin > $$m.diff ||	 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo " generating DSDL..." | tr -d '\012';		\
		(grep '^submodule' $$m > /dev/null || $(PYANG) -f dsdl -o $$m.dsdl $$m || exit 0);	\
		echo " ok";						\
	done

utf8-test:
	pyang -f yang q.yang || exit 1; \
	pyang -f yang q.yang > x || exit 1; \
	pyang -f yang q.yang -o x || exit 1; \
	rm -f x

mef-ieee-test:
	pyang --mef mef-yt10.yang || exit 1; \
        pyang --mef mef-yt11.yang || exit 1; \
        pyang --ieee ieee-yt12.yang || exit 1;

clean:
	rm -rf *.yang.yin *.gen.* *.dsdl
