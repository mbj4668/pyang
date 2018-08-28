test: test1 test2 test3 test4 test5 test6

test1:
	pyang -f tree x.yang --tree-line-length 10 | diff x.tree.10.expect -

test2:
	pyang -f tree x.yang --tree-line-length 50 | diff x.tree.50.expect -

test3:
	pyang -f tree x.yang --tree-line-length 1000 | diff x.tree.expect -

test4:
	pyang -f tree x.yang | diff x.tree.expect -

test5:
	# Baseline test before using module name as prefix
	pyang -f tree interfaces-ext.yang ietf-interfaces.yang | diff ietf-interfaces.tree.expect -

test6:
	# Use module name as prefix
	pyang -f tree --tree-module-name-prefix interfaces-ext.yang ietf-interfaces.yang | diff ietf-interfaces-ext.tree.expect -