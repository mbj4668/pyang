test: test1 test2

test1:
	pyang mod1.yang --print-error-code 2>&1 | diff expect/mod1.expect -

test2:
	pyang mod2.yang --print-error-code 2>&1 | diff expect/mod2.expect -