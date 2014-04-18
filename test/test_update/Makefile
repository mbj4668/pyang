PYANG = pyang --print-error-code --check-update-from

MODULES = a

test:
	@for m in $(MODULES); do					\
		echo -n "trying $$m...";				\
		$(PYANG) $$m.yang $$m@2014-04-01.yang 2> $$m.out;	\
		diff expect/$$m.out $$m.out > $$m.diff || 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo " ok";						\
	done

clean:
	rm -rf *.out *.diff
