test: test1 test2

test1:
	$(PYANG) mod1.yang --print-error-code 2>&1 | diff mod1.expect -

test2:
	$(PYANG) mod2.yang --print-error-code 2>&1 | diff mod2.expect -
