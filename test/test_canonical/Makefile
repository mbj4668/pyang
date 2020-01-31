PYANG := $(PYANG) -Wnone

MODULES = $(wildcard *.yang)

test:
	@for m in $(MODULES); do					\
		echo "trying canonical $$m..." | tr -d '\012';		\
		$(PYANG) --print-error-code --canonical $$m 2> $$m.out;	\
		diff expect/$$m.out $$m.out > $$m.diff || 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo " trying normal $$m..." | tr -d '\012';		\
		$(PYANG) $$m || exit 1;					\
		echo " ok";						\
	done

clean:
	rm -rf *.out *.diff
