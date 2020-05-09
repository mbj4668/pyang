test: test1 test2

test1:
	$(PYANG) -f yin x.yang | $(PYANG) -f yang | diff x.yang -

test2:
	$(PYANG) -f tree x.yang | diff x.tree.expect -
