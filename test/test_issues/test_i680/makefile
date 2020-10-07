test: test1

test1:
	-$(PYANG) --max-line-len=70 -f tree -o mod1.tree mod1.yang 2>&1 | diff mod1.expect -
