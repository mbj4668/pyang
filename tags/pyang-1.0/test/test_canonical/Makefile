PYANG = pyang -Wnone

MODULES = $(wildcard *.yang)

test:
	@for m in $(MODULES); do					\
		echo -n "trying canonical $$m...";			\
		$(PYANG) --print-error-code --canonical $$m 2> $$m.out;	\
		diff expect/$$m.out $$m.out > $$m.diff || 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo -n " trying normal $$m...";			\
		$(PYANG) $$m || exit 1;					\
		echo " ok";						\
	done

clean:
	rm -rf *.out *.diff
