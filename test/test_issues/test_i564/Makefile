test: test1 test2 test4

test1:
	$(PYANG) mod1.yang --print-error-code 2>&1 | diff expect/mod1.expect -

test2:
	$(PYANG) mod2.yang --print-error-code 2>&1 | diff expect/mod2.expect -

test4:
	$(PYANG) mod4.yang --print-error-code 2>&1 | diff expect/mod4.expect -
