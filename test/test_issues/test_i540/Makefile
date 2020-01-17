test: test1 test2 test3

test1:
	pyang a.yang --print-error-code 2>&1 | diff a.expect -

test2:
	pyang b.yang --print-error-code 2>&1 | diff b.expect -

test3:
	pyang c.yang --print-error-code 2>&1 | diff c.expect -
