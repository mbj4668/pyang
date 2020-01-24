test: test1 test2 test3 test4 test5 test6 test7 test8 test9 test10 test11 test12 test14 test15 test16 test17 test18 test19
test1:
	# Test help
	pyang --sid-help 2>&1 | diff -b test-1-expected-output.txt -

test2:
	# Test generate sid file
	pyang --sid-list --sid-generate-file 20000:25 toaster@2009-11-20.yang 2>&1 | diff -b test-2-expected-output.txt -
	diff -b test-2-expected-toaster@2009-11-20.sid toaster@2009-11-20.sid
	rm toaster@2009-11-20.sid

test3:
	# Test update sid file
	cp test-2-expected-toaster@2009-11-20.sid toaster@2009-11-20.sid
	pyang --sid-list --sid-update-file toaster@2009-11-20.sid toaster@2009-12-28.yang 2>&1 | diff -b test-3-expected-output.txt -
	diff -b test-3-expected-toaster@2009-12-28.sid toaster@2009-12-28.sid
	rm toaster@2009-11-20.sid toaster@2009-12-28.sid

test4:
	# Test check sid file
	cp test-2-expected-toaster@2009-11-20.sid toaster@2009-11-20.sid
	pyang --sid-list --sid-check-file toaster@2009-11-20.sid toaster@2009-11-20.yang 2>&1 | diff -b test-4-expected-output.txt -
	rm toaster@2009-11-20.sid

test5:
	# Test augment and yang data
	pyang --sid-generate-file 2500:50 ietf-constrained-voucher@2019-08-01.yang 2>&1 | diff -b test-5-expected-output.txt -
	diff -b test-5-expected-ietf-constrained-voucher@2019-08-01.sid ietf-constrained-voucher@2019-08-01.sid
	rm ietf-constrained-voucher@2019-08-01.sid
  
test6:
	# Test SID range exhausted
	cp test-3-expected-toaster@2009-12-28.sid toaster@2009-12-28.sid
	pyang --sid-update-file toaster@2009-12-28.sid toaster@2019-01-01.yang 2>&1 | diff -b test-6-expected-output.txt - 
	rm toaster@2009-12-28.sid

test7:
	# Test extra SID range
	cp test-2-expected-toaster@2009-11-20.sid toaster@2009-11-20.sid
	pyang --sid-update-file toaster@2009-11-20.sid toaster@2009-12-28.yang --sid-extra-range 20010:10 2>&1 | diff -b test-7b-expected-output.txt -
	cp test-3-expected-toaster@2009-12-28.sid toaster@2009-12-28.sid
	pyang --sid-update-file toaster@2009-12-28.sid toaster@2019-01-01.yang --sid-extra-range 20100:25 2>&1 | diff -b test-7-expected-output.txt -
	diff -b test-7-expected-toaster@2019-01-01.sid toaster@2019-01-01.sid
	rm -f toaster@2009-11-20.sid toaster@2009-12-28.sid toaster@2019-01-01.sid

test8:
	# In generate sid file, test count 
	pyang --sid-generate-file count toaster@2009-11-20.yang 2>&1 | diff -b test-8-expected-output.txt -

test9:
	# In generate sid file, test invalid SID range
	pyang --sid-generate-file 2000025 toaster@2009-11-20.yang 2>&1 | diff -b test-9-expected-output.txt -

test10:
	# In generate sid file, test invalid yang filename
	pyang --sid-list --sid-generate-file 20000:25 test10-bad-toaster@2009-11-20.yang 2>&1 | diff -b test-10-expected-output.txt -

test11:
	# In generate sid file, test yang file not found
	pyang --sid-generate-file 20000:25 toaster@2009-01-01.yang 2>&1 | diff -b test-11-expected-output.txt -

test12:
	# In update sid file, test count
	cp test-3-expected-toaster@2009-12-28.sid toaster@2009-12-28.sid
	pyang --sid-update-file toaster@2009-12-28.sid toaster@2019-01-01.yang --sid-extra-range count 2>&1 | diff -b test-12-expected-output.txt -
	rm toaster@2009-12-28.sid

test14:
	# In update sid file, test yang file not found
	pyang --sid-update-file toaster@2009-11-20.sid toaster2009-12-29.yang 2>&1 | diff -b test-14-expected-output.txt -

test15:
	# In update sid file, test invalid sid file
	pyang --sid-update-file test15-bad-toaster@2009-11-20.sid toaster@2009-12-28.yang 2>&1 | diff -b test-15-expected-output.txt -

test16:
	# In update sid file, test invalid JSON format
	pyang --sid-update-file test16-bad-toaster@2009-11-20.sid toaster@2009-12-28.yang 2>&1 | diff -b test-16-expected-output.txt -

test17:
	# In update sid file, test sid file not found
	pyang --sid-update-file toaster@2009-11-20.sid toaster@2009-12-28.yang 2>&1 | diff -b test-17-expected-output.txt -

test18:
	# In checksid file, test yang file not found
	pyang --sid-check-file toaster@2009-11-20.sid toaster.yang 2>&1 | diff -b test-18-expected-output.txt -

test19:
	# In checksid file, test test sid file not found
	pyang --sid-check-file toaster@2009-11-20.sid toaster@2009-11-20.yang 2>&1 | diff -b test-19-expected-output.txt -
