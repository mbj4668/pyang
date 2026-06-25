PYANG := $(or $(PYANG), pyang)

test: test1 test2 test3 test4 test5 test6 test7 test8 test9 \
	test10 test11 test12 test13 test14 test15 test16

# Baseline: imports (b, revision-pinned c) and an included submodule (a-sub).
test1:
	$(PYANG) -f depend a@2022-03-29.yang 2>&1 | diff test1.expect -

# --depend-recurse also pulls in d (imported by b).
test2:
	$(PYANG) -f depend --depend-recurse a@2022-03-29.yang 2>&1 | diff test2.expect -

# --depend-no-submodules drops the included a-sub submodule.
test3:
	$(PYANG) -f depend --depend-no-submodules a@2022-03-29.yang 2>&1 | diff test3.expect -

test4:
	$(PYANG) -f depend --depend-recurse --depend-no-submodules a@2022-03-29.yang 2>&1 | diff test4.expect -

# --depend-ignore-module on the recursively-reached a-sub submodule.
test5:
	$(PYANG) -f depend --depend-recurse --depend-ignore-module 'a-sub' a@2022-03-29.yang 2>&1 | diff test5.expect -

# --depend-ignore-module on a direct import.
test6:
	$(PYANG) -f depend --depend-ignore-module b a@2022-03-29.yang 2>&1 | diff test6.expect -

test7:
	$(PYANG) -f depend --depend-recurse b@2022-02-20.yang 2>&1 | diff test7.expect -

# --depend-extension appends the extension to the bare module name.
test8:
	$(PYANG) -f depend --depend-extension '.yang' b@2022-02-20.yang 2>&1 | diff test8.expect -

test9:
	$(PYANG) -f depend --depend-recurse d@2022-03-03.yang 2>&1 | diff test9.expect -

# --depend-include-path with a revision-pinned import: a imports c with
# revision-date 2022-01-01 while c@2022-02-02 also exists.  A name-only lookup
# resolves to the latest (2022-02-02), which is not loaded, so the path must be
# resolved with the import's revision-date.  This used to crash with
# "AttributeError: 'NoneType' object has no attribute 'pos'".
test10:
	$(PYANG) -f depend --depend-include-path a@2022-03-29.yang 2>&1 | diff test10.expect -

# Same, recursing through b into d.
test11:
	$(PYANG) -f depend --depend-include-path --depend-recurse a@2022-03-29.yang 2>&1 | diff test11.expect -

# --depend-include-path with --depend-extension replaces the file extension.
test12:
	$(PYANG) -f depend --depend-include-path --depend-extension '.foo' a@2022-03-29.yang 2>&1 | diff test12.expect -

# A module reached both pinned and unpinned in one closure (e imports d with
# revision-date 2022-03-03 and imports b, which imports d with no
# revision-date) must list d only once, not once per (name, revision) pair.
test13:
	$(PYANG) -f depend --depend-recurse e@2022-04-04.yang 2>&1 | diff test13.expect -

# Same, with --depend-include-path: both reach the same file, so d is listed once.
test14:
	$(PYANG) -f depend --depend-recurse --depend-include-path e@2022-04-04.yang 2>&1 | diff test14.expect -

# --depend-include-path where the revision is NOT encoded in the file name:
# v1/m.yang and v2/m.yang are both named "m.yang", distinguished only by their
# revision statement.  mtop pins m to 2020-01-01 (v1), so resolution must use
# module content, and the emitted path is the file as found (v1/m.yang).
test15:
	$(PYANG) -f depend --depend-include-path -p v1 -p v2 mtop.yang 2>&1 | diff test15.expect -

# Same, but with --depend-recurse: the walk descends into the content-resolved
# m (v1/m.yang) and harvests its own import, dep, also resolved from v1.
test16:
	$(PYANG) -f depend --depend-recurse --depend-include-path -p v1 -p v2 mtop.yang 2>&1 | diff test16.expect -
