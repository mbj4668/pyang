test: test1 test2 test3 test4 test5 test6 test7

test1:
	$(PYANG) -f tree x.yang --tree-line-length 10 | diff x.tree.10.expect -

test2:
	$(PYANG) -f tree x.yang --tree-line-length 50 | diff x.tree.50.expect -

test3:
	$(PYANG) -f tree x.yang --tree-line-length 1000 | diff x.tree.expect -

test4:
	$(PYANG) -f tree x.yang | diff x.tree.expect -

test5:
	# Baseline test before using module name as prefix
	$(PYANG) -f tree interfaces-ext.yang ietf-interfaces.yang | diff ietf-interfaces.tree.expect -

test6:
	# Use module name as prefix
	$(PYANG) -f tree --tree-module-name-prefix interfaces-ext.yang ietf-interfaces.yang | diff ietf-interfaces-ext.tree.expect -

test7:
	$(PYANG) -f tree sx.yang --tree-print-structures| diff sx.tree.expect -

test8:
	$(PYANG) -f tree aug.yang | diff aug.tree.expect -
