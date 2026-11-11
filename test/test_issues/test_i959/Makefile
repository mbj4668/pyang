test: test1 test2 test3 test4

# the modules from the issue
test1:
	$(PYANG) --print-error-code example-3-a@2017-08-01.yang
	$(PYANG) -f tree example-3-a@2017-08-01.yang | diff expect.tree -

# 1.1: a submodule sees everything in its module and the other submodules
test2:
	$(PYANG) -Werror m.yang
	$(PYANG) -f tree m.yang | diff m.tree -

# 1.1: a submodule is validated with the module it belongs to
test3:
	$(PYANG) -Werror s1.yang
	$(PYANG) -Werror s2.yang

# 1: a submodule sees only its own definitions
test4:
	$(PYANG) --print-error-code -p v1 v1/m.yang 2> v1.out; true
	for e in IDENTITY_NOT_FOUND TYPE_NOT_FOUND LEAFREF_IDENTIFIER_NOT_FOUND \
	    GROUPING_NOT_FOUND NODE_NOT_FOUND; do \
	  grep "s1.yang.*$$e" v1.out > /dev/null || exit 1; \
	done; rm -f v1.out
