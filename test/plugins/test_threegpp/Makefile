test: test1 test2 test3 test4 test5 test6

test1:
	# Before running the test manually "export PYANG=/usr/bin/pyang" or wherever it is
	# Baseline test that a module following 3gpp guidelines is OK
	# $(PYANG) --3gpp -p ../../../modules/ietf _3gpp-correct.yang
	$(PYANG) --3gpp -p ../../../modules/ietf _3gpp-correct.yang 

test2:
	# $(PYANG) --3gpp _3gpp-incorrect.yang |& diff incorrect-3gpp.expect -
	$(PYANG) --3gpp _3gpp-incorrect.yang |& diff incorrect-3gpp.expect -

test3:
	# $(PYANG) -3gpp _3gpp-missing-incorrect2.yang |& diff missing-incorrect2-3gpp.expect -
	$(PYANG) --3gpp _3gpp-missing-incorrect2.yang |& diff missing-incorrect2-3gpp.expect -

test4:
	# $(PYANG) --3gpp twogpp-wrongFileName.yang |& diff twogpp-wrongFileName.expect -
	$(PYANG) --3gpp twogpp-wrongFileName.yang |& diff twogpp-wrongFileName.expect -

test5:
  # Check that normal validation still works
	# $(PYANG) --ietf -p ../../../modules/ietf ../../../modules/ietf/ietf-netconf-acm.yang
	$(PYANG) --ietf -p ../../../modules/ietf ../../../modules/ietf/ietf-netconf-acm.yang

test6:
  # Check help text
  #
	$(PYANG) -h | grep "  --3gpp                Validate the module(s) according to 3GPP rules."

  