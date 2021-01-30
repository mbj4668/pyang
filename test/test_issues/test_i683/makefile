test: test1

test1:
	-$(PYANG) --format=sample-xml-skeleton base.yang main.yang 2>&1 | diff main.expect -
