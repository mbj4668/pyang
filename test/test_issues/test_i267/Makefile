test:
	pyang --print-error-code test.yang --deviation-module=test-dev.yang \
	  2>&1 | grep BAD_DEVIATE_ADD > /dev/null
