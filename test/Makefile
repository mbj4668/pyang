DIRS = $(shell for d in test_* ; \
	do [ -d $$d -a -f $$d/Makefile ] && echo $$d ; done)

ifeq "$(TEST_MODE)" "coverage"
COVERAGE := python -mcoverage run --branch --parallel-mode --source $(W)/pyang --omit $(W)/pyang/yacc.py
export PYANG := $(COVERAGE) $(W)/pyang/scripts/pyang_tool.py
export JSON2XML := $(COVERAGE) $(W)/pyang/scripts/json2xml.py
export YANG2HTML := $(COVERAGE) $(W)/pyang/scripts/yang2html.py
else ifeq "$(TEST_MODE)" "profile"
PROFILE := python -mcProfile -o .profile-`date +%M.%S.%N`
export PYANG := $(PROFILE) $(W)/pyang/scripts/pyang_tool.py
export JSON2XML := $(PROFILE) $(W)/pyang/scripts/json2xml.py
export YANG2HTML := $(PROFILE) $(W)/pyang/scripts/yang2html.py
else
export PYANG := pyang
export JSON2XML := json2xml
export YANG2HTML := yang2html
endif
export YANG2DSDL := env PYANG="$(PYANG)" $(W)/bin/yang2dsdl

test:
	$(MAKE) selftest mtest itest

test_all: python3_test


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

python3/python: python3
	ln -sf `which python3` $@

python3:
	mkdir $@

clean:
	@find -name '.coverage*' -delete;				\
	find -name '.profile*' -delete;					\
	for d in $(DIRS); do 						\
		  (cd $$d && $(MAKE) $@)				\
	done;								\
	rm -rf python3
