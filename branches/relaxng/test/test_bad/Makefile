PYANG = pyang --print-error-code

MODULES = $(wildcard *.yang)

test:
	@for m in $(MODULES); do					\
		echo -n "trying $$m...";				\
		$(PYANG) $$m 2> $$m.out;				\
		diff expect/$$m.out $$m.out > $$m.diff || 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo " ok";						\
	done

clean:
	rm -rf *.out *.diff
