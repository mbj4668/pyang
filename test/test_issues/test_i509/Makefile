test: test-1 test-2


test-1:
	$(PYANG) a.yang

test-2:
	$(PYANG) b.yang --print-error-code 2>&1 | diff b.expect -
