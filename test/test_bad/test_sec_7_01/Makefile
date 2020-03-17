test: test1 test2 test3 test4

test1:
	pyang mod1.yang --print-error-code 2>&1 | diff expect/mod1.expect -

test2:
	pyang mod2.yang --print-error-code 2>&1 | diff expect/mod2.expect -

test3:
	pyang mod3.yang --print-error-code 2>&1 | diff expect/mod3.expect -

test4:
	pyang mod4.yang --print-error-code 2>&1 | diff expect/mod4.expect -
