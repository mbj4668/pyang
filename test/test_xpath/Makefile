test: test1 test2 test3 test4

test1:
	-pyang ietf-netconf-notifications@2012-02-06.yang > temp.txt 2>&1
	diff temp.txt xpath.expect

test2:
	-pyang ietf-snmp-community@2014-12-10.yang > temp.txt 2>&1
	diff temp.txt xpath2.expect

test3:
	-pyang ietf-ipv4-unicast-routing.yang > temp.txt 2>&1
	diff temp.txt xpath3.expect

test4:
	-pyang ietf-ipv6-unicast-routing.yang  > temp.txt 2>&1
	diff temp.txt xpath4.expect

clean:
	rm temp.txt




