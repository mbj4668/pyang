test: test-1 test-2


test-1:
	pyang -Werror a.yang

test-2:
	pyang b.yang -Werror --print-error-code 2>&1 | diff b.expect -
