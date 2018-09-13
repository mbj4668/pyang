test: test1 test2

test1:
	pyang --print-error-code ietf-netconf-notifications@2012-02-06.yang \
	  2>&1 | diff xpath.expect -

test2:
	pyang --print-error-code ietf-snmp-community@2014-12-10.yang \
	  2>&1 | diff xpath2.expect -





