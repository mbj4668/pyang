test: test1 test2

test1:
	pyang -f yin x.yang | pyang -f yang | diff x.yang -

test2:
	pyang -f tree x.yang | diff x.tree.expect -
