PYANG = pyang --print-error-code --check-update-from

MODULES = a c d

test:
	@for m in $(MODULES); do					\
		echo "trying $$m..." | tr -d '\012';			\
		$(PYANG) $$m.yang $$m@2014-04-01.yang 2> $$m.out;	\
		diff expect/$$m.out $$m.out > $$m.diff || 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo " ok";						\
	done

clean:
	rm -rf *.out *.diff
