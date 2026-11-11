test: test1 test2 test3

# 1.1: submodule augments a node in another submodule, which is
# included after the augmenting submodule
test1:
	$(PYANG) -Werror x-base.yang
	$(PYANG) -f tree x-base.yang | diff expect.tree -

# 1.1: submodule augments a node in the main module
test2:
	$(PYANG) -Werror y-base.yang
	$(PYANG) -f tree y-base.yang | diff y-expect.tree -

# 1: a submodule cannot augment a node in the main module
test3:
	$(PYANG) -p v1 --print-error-code v1/y-base.yang 2>&1 \
	  | grep "y-profiles.yang.*NODE_NOT_FOUND" >/dev/null || exit 1
