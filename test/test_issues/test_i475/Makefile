test:
	$(PYANG) --print-error-code test.yang --deviation-module=test-dev.yang \
	  2>&1 | diff test-dev.expect -
