test:
	$(PYANG) a.yang --print-error-code 2>&1 | diff a.expect -

	$(PYANG) b.yang --print-error-code 2>&1 | diff b.expect -
