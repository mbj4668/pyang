test: test1 test2 test3 test4

test1:
	$(PYANG) -Werror x-base.yang

test2:
	$(PYANG) -Werror y-base.yang

test3:
	$(PYANG) -Werror z-base.yang

test4:
	$(PYANG) -Werror --print-error-code y1-base.yang 2>&1 \
	  | grep XPATH_NODE_NOT_FOUND2 >/dev/null || exit 1
