PYANG?= pyang

.PHONY: test test1 test2 test3 test4
test: test1 test2 test3 test4

test1:
	# Test tree for strcuture (duplicit test)
	$(PYANG) -f tree --tree-print-structures -p ../../modules/ietf example-module@2020-06-17.yang 2>&1 | diff -b test-1-expected-output.txt -
	
test2:
	# Test tree for augment-structure
	$(PYANG) -f tree --tree-print-structures -p ../../modules/ietf example-module-aug.yang 2>&1 | diff -b test-2-expected-output.txt -

test3:
	# More complex test
	$(PYANG) -f tree --tree-print-structures -p ../../modules/ietf	test-3-complex.yang 2>&1 | diff -b test-3-expected-output.txt -
	
test4:
	# Test bad augment-structure -- target must be structure descendant 
	$(PYANG) -p ../../modules/ietf test-4-bad-aug.yang 2>&1 | diff -b test-4-expected-output.txt -
