test: test1 test2 test3 test4 test5

test1:
	# Baseline test that a module following 3gpp guidelines is OK
	# $(PYANG) --3gpp _3gpp-correct.yang &> correct-3gpp.result
	$(PYANG) --3gpp _3gpp-correct.yang 

test2:
	# $(PYANG) --3gpp _3gpp-incorrect.yang &> incorrect-3gpp.result
	$(PYANG) --3gpp _3gpp-incorrect.yang |& diff incorrect-3gpp.expect -

test3:
	# $(PYANG) --3gpp _3gpp-missing-incorrect2.yang &> missing-incorrect2-3gpp.result
	$(PYANG) --3gpp _3gpp-missing-incorrect2.yang |& diff missing-incorrect2-3gpp.expect -

test4:
	# $(PYANG) --3gpp twogpp-wrongFileName.yang &> twogpp-wrongFileName.result
	$(PYANG) --3gpp twogpp-wrongFileName.yang |& diff twogpp-wrongFileName.expect -

test5:
  # Check that normal validation still works
	$(PYANG) --ietf ietf-yang-types@2013-07-15.yang