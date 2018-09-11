test: test1 test2 clean

test1:
	-pyang ietf-netconf-notifications@2012-02-06.yang > temp.txt 2>&1
	diff temp.txt xpath.expect

test2:
	-pyang ietf-snmp-community@2014-12-10.yang > temp.txt 2>&1
	diff temp.txt xpath2.expect

clean:
	rm temp.txt




