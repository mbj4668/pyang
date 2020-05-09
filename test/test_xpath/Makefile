DIRS = $(shell for d in test_* ; \
	do [ -d $$d -a -f $$d/Makefile ] && echo $$d ; done)

PYANG := $(PYANG) --print-error-code --strict

MODULES = $(wildcard *.yang)

test: subdirs
	@for m in $(MODULES); do					\
		echo "trying $$m..." | tr -d '\012';			\
		$(PYANG) $$m 2> $$m.out;				\
		diff expect/$$m.out $$m.out > $$m.diff || 		\
			{ cat $$m.diff; exit 1; };			\
		rm -f $$m.diff;						\
		echo " ok";						\
	done

subdirs:
	for d in $(DIRS); do 						\
		( cd $$d && $(MAKE) test ) || exit 1;			\
	done


clean:
	rm -rf *.out *.diff
