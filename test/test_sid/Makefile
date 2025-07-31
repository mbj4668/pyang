PYANG?= pyang

.PHONY: test test1 test2 test3 test4 test5 test6 test7 test8 test9 test10 test11 \
	test12 test14 test15 test16 test17 test18 test19 test20 test21 test22 test23 \
	test24 test25 test26 test27 test28 test29 test30
test: test1 test2 test3 test4 test5 test6 test7 test8 test9 test10 test11 \
	test12 test14 test15 test16 test17 test18 test19 test20 test21 test22 \
	test23 test24 test25 test26 test27 test28 test29 test30

test1:
	# Test help
	$(PYANG) --sid-help 2>&1 | diff -w test-1-expected-output.txt -

test2:
	# Test generate sid file
	$(PYANG) --sid-list --sid-generate-file 20000:25 toaster@2009-11-20.yang 2>&1 | diff -b test-2-expected-output.txt -
	diff -b test-2-expected-toaster@2009-11-20.sid toaster@2009-11-20.sid
	rm toaster@2009-11-20.sid

test3:
	# Test update sid file (test3)
	cp test-2-expected-toaster@2009-11-20.sid toaster@2009-11-20.sid
	$(PYANG) --sid-list --sid-update-file toaster@2009-11-20.sid toaster@2009-12-28.yang 2>&1 | diff -b test-3-expected-output.txt -
	diff -b test-3-expected-toaster@2009-12-28.sid toaster@2009-12-28.sid
	rm toaster@2009-11-20.sid toaster@2009-12-28.sid

test4:
	# Test check sid file
	cp test-2-expected-toaster@2009-11-20.sid toaster@2009-11-20.sid
	$(PYANG) --sid-list --sid-check-file toaster@2009-11-20.sid toaster@2009-11-20.yang 2>&1 | diff -b test-4-expected-output.txt -
	rm toaster@2009-11-20.sid

test5:
	# Test augment and yang data
	$(PYANG) --sid-generate-file 2500:50 ietf-constrained-voucher@2019-08-01.yang 2>&1 | diff -b test-5-expected-output.txt -
	diff -b test-5-expected-ietf-constrained-voucher@2019-08-01.sid ietf-constrained-voucher@2019-08-01.sid
	rm ietf-constrained-voucher@2019-08-01.sid

test6:
	# Test SID range exhausted
	cp test-3-expected-toaster@2009-12-28.sid toaster@2009-12-28.sid
	$(PYANG) --sid-update-file toaster@2009-12-28.sid toaster@2019-01-01.yang 2>&1 | diff -b test-6-expected-output.txt -
	rm toaster@2009-12-28.sid

test7:
	# Test extra SID range
	cp test-2-expected-toaster@2009-11-20.sid toaster@2009-11-20.sid
	$(PYANG) --sid-update-file toaster@2009-11-20.sid toaster@2009-12-28.yang --sid-extra-range 20010:10 2>&1 | diff -b test-7b-expected-output.txt -
	cp test-3-expected-toaster@2009-12-28.sid toaster@2009-12-28.sid
	$(PYANG) --sid-update-file toaster@2009-12-28.sid toaster@2019-01-01.yang --sid-extra-range 20100:25 2>&1 | diff -b test-7-expected-output.txt -
	diff -b test-7-expected-toaster@2019-01-01.sid toaster@2019-01-01.sid
	rm -f toaster@2009-11-20.sid toaster@2009-12-28.sid toaster@2019-01-01.sid

test8:
	# In generate sid file, test count
	$(PYANG) --sid-generate-file count toaster@2009-11-20.yang 2>&1 | diff -b test-8-expected-output.txt -

test9:
	# In generate sid file, test invalid SID range
	$(PYANG) --sid-generate-file 2000025 toaster@2009-11-20.yang 2>&1 | diff -b test-9-expected-output.txt -

test10:
	# In generate sid file, test invalid yang filename
	$(PYANG) --sid-list --sid-generate-file 20000:25 test10-bad-toaster@2009-11-20.yang 2>&1 | diff -b test-10-expected-output.txt -

test11:
	# In generate sid file, test yang file not found
	$(PYANG) --sid-generate-file 20000:25 toaster@2009-01-01.yang 2>&1 | diff -b test-11-expected-output.txt -

test12:
	# In update sid file, test count
	cp test-3-expected-toaster@2009-12-28.sid toaster@2009-12-28.sid
	$(PYANG) --sid-update-file toaster@2009-12-28.sid toaster@2019-01-01.yang --sid-extra-range count 2>&1 | diff -b test-12-expected-output.txt -
	rm toaster@2009-12-28.sid

test14:
	# In update sid file, test yang file not found
	$(PYANG) --sid-update-file toaster@2009-11-20.sid toaster2009-12-29.yang 2>&1 | diff -b test-14-expected-output.txt -

test15:
	# In update sid file, test invalid sid file
	$(PYANG) --sid-update-file test15-bad-toaster@2009-11-20.sid toaster@2009-12-28.yang 2>&1 | diff -b test-15-expected-output.txt -

test16:
	# In update sid file, test invalid JSON format
	$(PYANG) --sid-update-file test16-bad-toaster@2009-11-20.sid toaster@2009-12-28.yang 2>&1 | diff -b test-16-expected-output.txt -

test17:
	# In update sid file, test sid file not found
	$(PYANG) --sid-update-file toaster@2009-11-20.sid toaster@2009-12-28.yang 2>&1 | diff -b test-17-expected-output.txt -

test18:
	# In checksid file, test yang file not found
	$(PYANG) --sid-check-file toaster@2009-11-20.sid toaster.yang 2>&1 | diff -b test-18-expected-output.txt -

test19:
	# In checksid file, test test sid file not found
	$(PYANG) --sid-check-file toaster@2009-11-20.sid toaster@2009-11-20.yang 2>&1 | sort | diff -b test-19-expected-output.txt -

test20:
	# Test multiple level of grouping
	$(PYANG) --sid-generate-file 60000:100 ieee802-dot1q-psfp@2020-07-07.yang 2>&1 | diff -b test-20-expected-output.txt -
	diff -b test-20-expected-ieee802-dot1q-psfp@2020-07-07.sid ieee802-dot1q-psfp@2020-07-07.sid
	rm ieee802-dot1q-psfp@2020-07-07.sid

test21:
	# Test finalize of sid file
	cp test-3-expected-toaster@2009-12-28.sid toaster@2009-12-28.sid
	$(PYANG) --sid-update-file toaster@2009-12-28.sid --sid-finalize toaster@2009-12-28.yang 2>&1 | diff -b test-21-expected-output.txt -
	diff -b toaster@2009-12-28.sid test-21-expected-toaster@2009-12-28.sid
	rm toaster@2009-12-28.sid

EXAMPLE_MOD=../test_structure/example-module@2020-06-17.yang
EXAMPLE_MOD_AUG=../test_structure/example-module-aug.yang

test22:
	# Test ietf-yang-structure-ext structure sid assignment
	$(PYANG) --sid-list --sid-generate-file 60000:20 ${EXAMPLE_MOD} 2>&1 | diff -b test-22-expected-output.txt -
	diff -b example-module@2020-06-17.sid test-22-expected-example-module@2020-06-17.sid
	rm example-module@2020-06-17.sid

test23:
	# Test ietf-yang-structure-ext augment-structure sid assignment
	$(PYANG) --sid-generate-file 61000:10 ${EXAMPLE_MOD_AUG} -p ../test_structure 2>&1 | diff -b test-23-expected-output.txt -
	diff -b example-module-aug.sid test-23-expected-example-module-aug.sid
	rm example-module-aug.sid

IETF_SYSTEM=../../modules/ietf/ietf-system.yang

test24:
	# Test ietf-system example from RFC 9595
	$(PYANG) --sid-generate-file 1700:100 ${IETF_SYSTEM} --sid-finalize 2>&1 | diff -b test-24-expected-output.txt -
	diff -b ietf-system@2014-08-06.sid test-24-expected-ietf-system@2014-08-06.sid
	rm ietf-system@2014-08-06.sid

test25: a.yang test-25-expected-output.txt test-25-a.sid
	# Test trivial depend
	$(PYANG) --sid-generate-file 250:10 a.yang 2>&1 | diff -b test-25-expected-output.txt -
	diff -b a.sid test-25-a.sid
	rm a.sid

test26: b@2025-07-20.yang c.yang test-26-expected-output.txt test-26-c.sid
	# Test explicit import depend
	$(PYANG) --sid-generate-file 260:10 c.yang 2>&1 | diff -b test-26-expected-output.txt -
	diff -b c.sid test-26-c.sid
	rm c.sid

test27: d@2025-07-15.yang e.yang test-27-expected-output.txt test-27-e.sid
	# Test unique module version
	$(PYANG) --sid-generate-file 270:10 e.yang 2>&1 | diff -b test-27-expected-output.txt -
	diff -b e.sid test-27-e.sid
	rm e.sid

test28: f.yang g.yang test-28-expected-output.txt test-28-g.sid
	# Test module with revision inside
	$(PYANG) --sid-generate-file 280:10 g.yang 2>&1 | diff -b test-28-expected-output.txt -
	diff -b g.sid test-28-g.sid
	rm g.sid

test29: h@2025-07-15.yang h@2025-07-20.yang i@2025-07-25.yang test-29-i.sid
	# Test revision use latest
	$(PYANG) --sid-generate-file 290:10 i@2025-07-25.yang 2>&1 | diff -b test-29-expected-output.txt -
	diff -b i@2025-07-25.sid test-29-i.sid
	rm i@2025-07-25.sid

test30: j.yang j@2025-07-15.yang k.yang test-30-expected-output.txt
	# Test with and without revision
	$(PYANG) --sid-generate-file 300:10 k.yang 2>&1 | diff -b test-30-expected-output.txt -
	diff -b k.sid test-30-k.sid
	rm k.sid

test31: l@2025-07-20.yang m.yang test-31-expected-output.txt
	# Test nonexistent revision
	$(PYANG) --sid-generate-file 310:10 m.yang 2>&1 | diff -b test-31-expected-output.txt -

