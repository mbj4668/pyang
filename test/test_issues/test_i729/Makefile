test: test1 test2 test3 test4

test1:
	$(PYANG) -Werror -p v1.1 v1.1/native.yang

test2:
	$(PYANG) -Werror -p v1.1 v1.1/bgp.yang

test3:
	$(PYANG) -Werror -p v1 v1/native.yang

test4:
	$(PYANG) -Werror -p v1 --print-error-code  v1/bgp.yang 2>&1 \
	  | grep LEAFREF_IDENTIFIER_NOT_FOUND >/dev/null || exit 1
