PYANG := $(or $(PYANG), pyang) --plugindir . --transform feature --format tree feature.yang

test: basic \
      include-exclude-different include-exclude-same \
      include-none include-foo include-both \
      exclude-none exclude-foo exclude-both

# pass DEBUG=<anything> to output to stdout/stderr for debugging
# pass SNAP=<anything> to save rather than compare the expected output files
POST = $(if $(DEBUG),,2>&1 | $(if $(SNAP),cat - >$@.expect,diff - $@.expect))

basic:
	$(PYANG) $(POST)

include-exclude-different:
	-$(PYANG) --features ietf-types: --exclude-features feature: $(POST)

include-exclude-same:
	-$(PYANG) --features feature: --exclude-features feature: $(POST)

include-none:
	$(PYANG) --features feature: $(POST)

include-foo:
	$(PYANG) --features feature:has-leaf-foo $(POST)

include-both:
	$(PYANG) --features feature:has-leaf-foo,has-leaf-goo $(POST)

exclude-none:
	$(PYANG) --exclude-features feature: $(POST)

exclude-foo:
	$(PYANG) --exclude-features feature:has-leaf-foo $(POST)

exclude-both:
	$(PYANG) --exclude-features feature:has-leaf-foo,has-leaf-goo $(POST)
