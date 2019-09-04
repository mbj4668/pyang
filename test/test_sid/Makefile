test: test1 test2 test3 test4 test5 test6 test7

test1:
	# Test help
	pyang --sid-help 2>&1 | diff -b test-1-expected-output.txt -

test2:
	# Test generate sid file
	pyang --list-sid --generate-sid-file 20000:25 toaster@2009-11-20.yang 2>&1 | diff -b test-2-expected-output.txt -
	diff -b test-2-expected-toaster@2009-11-20.sid toaster@2009-11-20.sid
	rm toaster@2009-11-20.sid

test3:
	# Test update sid file
	cp test-2-expected-toaster@2009-11-20.sid toaster@2009-11-20.sid
	pyang --list-sid --update-sid-file toaster@2009-11-20.sid toaster@2009-12-28.yang 2>&1 | diff -b test-3-expected-output.txt -
	diff -b test-3-expected-toaster@2009-12-28.sid toaster@2009-12-28.sid
	rm toaster@2009-11-20.sid toaster@2009-12-28.sid

test4:
	# Test check sid file
	cp test-2-expected-toaster@2009-11-20.sid toaster@2009-11-20.sid
	pyang --list-sid --check-sid-file toaster@2009-11-20.sid toaster@2009-11-20.yang 2>&1 | diff -b test-4-expected-output.txt -
	rm toaster@2009-11-20.sid

test5:
	# Test augment and yang data
	pyang --list-sid --generate-sid-file 2500:50 ietf-constrained-voucher@2019-08-01.yang 2>&1 | diff -b test-5-expected-output.txt -
	diff -b test-5-expected-ietf-constrained-voucher@2019-08-01.sid ietf-constrained-voucher@2019-08-01.sid
	rm ietf-constrained-voucher@2019-08-01.sid
  
test6:
	# Test SID range exhausted
	cp test-3-expected-toaster@2009-12-28.sid toaster@2009-12-28.sid
	pyang --list-sid --update-sid-file toaster@2009-12-28.sid toaster@2019-01-01.yang 2>&1 | diff -b test-6-expected-output.txt - 
	rm toaster@2009-12-28.sid

test7:
	# Test extra SID range
	cp test-3-expected-toaster@2009-12-28.sid toaster@2009-12-28.sid
	pyang --list-sid --update-sid-file toaster@2009-12-28.sid toaster@2019-01-01.yang --extra-sid-range 20100:25 2>&1 | diff -b test-7-expected-output.txt -
	diff -b test-7-expected-toaster@2019-01-01.sid toaster@2019-01-01.sid
	rm toaster@2009-12-28.sid toaster@2019-01-01.sid
