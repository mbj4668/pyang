test: test_good test_bad test_ignore test_empty

test_good:
	$(PYANG) test.yang --msg-template="filename: {file} -- line: {line} \
	-- code: {code} -- type: {type} -- level: {level} \
        -- msg: [{msg}]" 2>&1 | \
	grep "filename: subtest.yang -- line: 11 -- code: NODE_NOT_FOUND \
	-- type: error -- level: 1 \
        -- msg: \[node subtest::cnt is not found\]"

test_bad:
	$(PYANG) test.yang --msg-template="filename: {file} -- line: {line} \
	-- code: {code} -- type: {type} -- msg: [{failed_parameter}]" 2>&1 | \
	grep "unsupported key 'failed_parameter' in msg-template"

test_ignore:
	$(PYANG) test.yang --ignore-error NODE_NOT_FOUND 2>&1

test_empty:
	$(PYANG) test.yang --ignore-errors 2>&1
