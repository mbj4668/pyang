test:
	pyang a.yang > /dev/null
	pyang b.yang --print-error-code 2>&1 | diff b.expect -
