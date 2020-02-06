test:
	$(PYANG) test.yang --msg-template="filename: {file} -- line: {line} \
	-- code: {code} -- type: {type} -- msg: [{msg}]" 2>&1 | \
	grep "filename: subtest.yang -- line: 11 -- code: NODE_NOT_FOUND \
	-- type: error -- msg: \[node subtest::cnt is not found\]"
