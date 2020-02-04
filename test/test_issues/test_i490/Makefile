test: test1 test2

# ensure that 'qux' is NOT printed when we don't implement any features
test1:
	$(PYANG) -f tree -F a: a.yang | grep -q qux && exit 1 || exit 0

# ensure that 'qux' IS printed when we implement all features
test2:
	$(PYANG) -f tree a.yang | grep -q qux
