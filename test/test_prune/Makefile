PYANG := $(PYANG) --features a:foo,fox --features b:foo --deviation-module d.yang

MODULES = a.yang b.yang

test:
	@for m in $(MODULES); do					\
		echo "trying $$m..."Makefile;				\
		$(PYANG) -f tree $$m > $$m.out;				\
		diff expect/$$m.out $$m.out > $$m.diff ||		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		$(PYANG) $$m -f capability > $$m.capa;			\
		diff expect/$$m.capa $$m.capa > $$m.diff || 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo " ok";						\
	done

clean:
	rm -rf *.out *.diff *.capa
