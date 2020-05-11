DIRS = $(shell for d in test_* ; \
	do [ -d $$d -a -f $$d/Makefile ] && echo $$d ; done)

ifeq "$(TEST_MODE)" "coverage"
COVERAGE := python -mcoverage run --branch --parallel-mode --source $(W)/pyang,$(W)/bin --omit $(W)/pyang/yacc.py
export PYANG := $(COVERAGE) $(W)/bin/pyang
export JSON2XML := $(COVERAGE) $(W)/bin/json2xml
export YANG2HTML := $(COVERAGE) $(W)/bin/yang2html
else ifeq "$(TEST_MODE)" "profile"
PROFILE := python -mcProfile -o .profile-`date +%M.%S.%N`
export PYANG := $(PROFILE) $(W)/bin/pyang
export JSON2XML := $(PROFILE) $(W)/bin/json2xml
export YANG2HTML := $(PROFILE) $(W)/bin/yang2html
else
export PYANG := pyang
export JSON2XML := json2xml
export YANG2HTML := yang2html
endif
export YANG2DSDL := env PYANG="$(PYANG)" $(W)/bin/yang2dsdl

test:
	$(MAKE) selftest mtest itest

test_all: python2_test python3_test

python2_test: python2/python
	$(MAKE) clean
	env PATH=`pwd`/python2:$(PATH) $(MAKE) itest

python3_test: python3/python
	$(MAKE) clean
	env PATH=`pwd`/python3:$(PATH) $(MAKE) itest

selftest:
	@echo "selftest... " | tr -d '\012'; \
		./selftest.py || exit 1; echo "ok";

mtest:
	@echo "validate all modules...";				\
	for d in ../modules/*; do					\
		( export YANG_MODPATH="$$d:$$YANG_MODPATH";		\
		for m in $$d/*.yang; do					\
			echo "  $${m}... " | tr -d '\012';		\
			$(PYANG) -Werror $$m || exit 1;			\
			echo "ok";					\
		done ) || exit 1;					\
	done || exit 1;

itest:
	for d in $(DIRS); do 						\
		( cd $$d && $(MAKE) test ) || exit 1;			\
	done

python2/python: python2
	ln -sf `which python2` $@

python3/python: python3
	ln -sf `which python3` $@

python2:
	mkdir $@

python3:
	mkdir $@

clean:
	@find -name '.coverage*' -delete;				\
	find -name '.profile*' -delete;					\
	for d in $(DIRS); do 						\
		  (cd $$d && $(MAKE) $@)				\
	done;								\
	rm -rf python2 python3
