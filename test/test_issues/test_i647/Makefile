test: test1

test1:
	$(PYANG) example.yang --print-error-code 2>&1 | diff expect/example.expect -
