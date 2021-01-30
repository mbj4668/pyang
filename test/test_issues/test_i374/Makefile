test:
	$(PYANG) a.yang > /dev/null
	$(PYANG) b.yang --print-error-code 2>&1 | diff b.expect -
