test: test1 test2

test1:
	$(PYANG) --ietf --print-error-code ietf-test-a.yang

test2:
	$(PYANG) --ietf --print-error-code ietf-test-a.yang \
	ietf-test-b.yang 2>&1 |	grep IETF_MISSING_RFC8174


