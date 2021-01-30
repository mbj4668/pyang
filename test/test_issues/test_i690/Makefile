test: test1

test1:
	-$(PYANG) test.yang --print-error-code 2>&1 | diff main.expect -
