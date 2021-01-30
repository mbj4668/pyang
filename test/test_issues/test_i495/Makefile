test: test-1 test-2


test-1:
	$(PYANG) -Werror a.yang

test-2:
	$(PYANG) b.yang -Werror --print-error-code 2>&1 | diff b.expect -
