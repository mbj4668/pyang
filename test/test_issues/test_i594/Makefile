test: test1

test1:
	$(PYANG) mod1.yang --print-error-code 2>&1 | diff expect/mod1.expect -
