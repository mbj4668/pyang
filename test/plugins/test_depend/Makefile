test: test1 test2 test3 test4 test5 test6 test7 test8 test9

test 1:
	pyang -f depend a@2022-03-29.yang |& diff a@2022-03-29.yang : b c a-sub
test 2:
	pyang -f depend --depend-recurse a@2022-03-29.yang |& diff a@2022-03-29.yang : b c a-sub d
test 3:
	pyang -f depend --depend-no-submodules a@2022-03-29.yang |& diff a@2022-03-29.yang : b c
test 4:
	pyang -f depend --depend-recurse --depend-no-submodules a@2022-03-29.yang |& diff a@2022-03-29.yang : b c d
test 5:
	pyang -f depend --depend-recurse --depend-ignore-module 'a-sub' a@2022-03-29.yang |& diff a@2022-03-29.yang : b c d
test 6:
	pyang -f depend --depend-ignore-module b a@2022-03-29.yang |& diff a@2022-03-29.yang : c a-sub
test 7:
	pyang -f depend --depend-recurse b@2022-02-20.yang |& diff b@2022-02-20.yang : d
test 8:
	pyang -f depend --depend-extension '.yang' b@2022-02-20.yang |& diff b@2022-02-20.yang : d.yang
test 9:
	pyang -f depend --depend-recurse d@2022-03-03.yang |& diff d@2022-03-03.yang :