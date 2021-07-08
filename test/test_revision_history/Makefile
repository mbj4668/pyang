test:
	$(PYANG) a.yang --verify-revision-history \
		--print-error-code 2>&1 | diff a1.expect -
	$(PYANG) a.yang -p old --verify-revision-history \
		--print-error-code 2>&1 | diff a2.expect -
