PYANG = pyang --print-error-code --check-update-from

MODULES = a b
DEVIATION_MODULES = d e

test:
	@for m in $(MODULES); do					\
		echo "trying $$m..." | tr -d '\012';			\
		$(PYANG) $$m.yang $$m@2014-04-01.yang 2> $$m.out;	\
		diff expect/$$m.out $$m.out > $$m.diff || 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo " ok";						\
	done

	@for m in $(DEVIATION_MODULES); do					\
		echo "trying b+$$m..." | tr -d '\012';			\
		$(PYANG) b.yang --check-update-from-deviation-module $$m.yang \
		--deviation-module $$m@2014-04-01.yang b@2014-04-01.yang 2> $$m.out; \
		diff expect/$$m.out $$m.out > $$m.diff || 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo " ok";						\
	done

clean:
	rm -rf *.out *.diff
