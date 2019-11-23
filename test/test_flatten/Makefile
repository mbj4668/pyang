test: test1

test1:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang | diff ietf-interfaces.flatten.expect -