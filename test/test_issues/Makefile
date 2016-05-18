DIRS = $(shell for d in test_* ; \
	do [ -d $$d -a -f $$d/Makefile ] && echo $$d ; done)

test: subdirs

subdirs:
	for d in $(DIRS); do 						\
		( cd $$d && $(MAKE) test ) || exit 1;			\
	done

