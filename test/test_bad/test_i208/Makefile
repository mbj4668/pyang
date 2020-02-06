test:
	$(PYANG) test.yang --msg-template="filename: {file} -- line: {line} \
	-- code: {code} -- type: {type} -- msg: [{failed_parameter}]" 2>&1 | \
	grep "unsupported key 'failed_parameter' in msg-template"
