DIRS = $(shell for d in test_* ; \
	do [ -d $$d -a -f $$d/Makefile ] && echo $$d ; done)

test:
	$(MAKE) itest

test_all: python2_test python3_test

python2_test: python2/python
	$(MAKE) clean
	env PATH=`pwd`/python2:$(PATH) $(MAKE) itest

python3_test: python3/python
	$(MAKE) clean
	env PATH=`pwd`/python3:$(PATH) $(MAKE) itest

itest:
	$(MAKE) selftest;						\
	for d in $(DIRS); do 						\
		( cd $$d && $(MAKE) test ) || exit 1;			\
	done

selftest:
	@echo "selftest... " | tr -d '\012'; \
		./selftest.py || exit 1; echo "ok";	\
	echo "validate all modules...";					\
	for d in ../modules/*; do					\
		( cd $$d;						\
		for m in *.yang; do					\
			echo "  $${m}... " | tr -d '\012';		\
			pyang -Werror $$m || exit 1;			\
			echo "ok";					\
		done ) || exit 1;					\
	done || exit 1;

python2/python: python2
	ln -sf `which python2` $@

python3/python: python3
	ln -sf `which python3` $@

python2:
	mkdir $@

python3:
	mkdir $@

clean:
	@for d in $(DIRS); do 						\
		  (cd $$d && $(MAKE) $@)				\
	done;								\
	rm -rf python2 python3
