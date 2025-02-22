test: test1 test2 test3 test4

# Baseline test that a module following 3gpp guidelines is OK
test1:
	$(PYANG) --ieee ieee802-dot1q-correct.yang 

test2:
	$(PYANG) --ieee ieee-802-dot1q-incorrect-name.yang 2>&1 | diff ieee-802-dot1q-incorrect-name.expect -

test3:
	$(PYANG) --ieee ieee802-dot1q-incorrect-namespace.yang 2>&1 | diff ieee802-dot1q-incorrect-namespace.expect -

# Check help text
test4:
	$(PYANG) -h | grep "  --ieee                Validate the module(s) according to IEEE rules."
