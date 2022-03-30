test: test_xpath test_deviation test_deviation_show test_all test_rpc_notif test_filter_keyword test_filter_primitive test_filter_flag test_all_keyed test_keys

test_xpath:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang | diff benchmarks/ietf-interfaces.xpath.csv -

test_deviation:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang ietf-interfaces-deviations.yang | diff benchmarks/ietf-interfaces.dev.csv -

test_deviation_show:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang ietf-interfaces-deviations.yang --flatten-deviated | diff benchmarks/ietf-interfaces.dev-show.csv -

test_all:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang ietf-interfaces-deviations.yang --flatten-keyword --flatten-type --flatten-primitive-type --flatten-flag --flatten-description --flatten-deviated --flatten-data-keywords | diff benchmarks/ietf-interfaces.all.csv -

test_all_keyed:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang ietf-interfaces-deviations.yang --flatten-keyword --flatten-type --flatten-primitive-type --flatten-flag --flatten-description --flatten-deviated --flatten-data-keywords --flatten-keys --flatten-keys-in-xpath | diff benchmarks/ietf-interfaces.all-keyed.csv -

test_all_qualified:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang ietf-interfaces-deviations.yang --flatten-keyword --flatten-type --flatten-primitive-type --flatten-flag --flatten-description --flatten-deviated --flatten-data-keywords --flatten-prefix-in-xpath --flatten-qualified-in-xpath | diff benchmarks/ietf-interfaces.all-qualified.csv -

test_rpc_notif:
	pyang -f flatten x.yang y.yang --flatten-keyword --flatten-data-keywords | diff benchmarks/xy.flatten.csv -

test_filter_keyword:
	pyang -f flatten ietf-yang-types.yang ietf-interfaces.yang --flatten-keyword --flatten-filter-keyword leaf | diff benchmarks/ietf-interfaces.leaf.csv -

test_filter_primitive:
	pyang -f flatten ietf-yang-types.yang ietf-interfaces.yang --flatten-primitive --flatten-filter-primitive uint64 | diff benchmarks/ietf-interfaces.uint64.csv -

test_filter_flag:
	pyang -f flatten ietf-yang-types.yang ietf-interfaces.yang --flatten-flag --flatten-filter-flag rw | diff benchmarks/ietf-interfaces.rw.csv -

test_keys:
	pyang -f flatten ietf-yang-types.yang ietf-interfaces-multikey.yang --flatten-keys --flatten-keys-in-xpath | diff benchmarks/ietf-interfaces-multikey.keys.csv -

test_prefixed_xpath:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang --flatten-prefix-in-xpath | diff benchmarks/ietf-interfaces.prefixed.csv -

test_qualified_xpath:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang --flatten-qualified-in-xpath | diff benchmarks/ietf-interfaces.qualified.csv -

test_mod_prefix_keyed:
	pyang -f flatten --flatten-qualified-module-and-prefix-path --flatten-keys-in-xpath ietf-interfaces-multikey.yang | diff benchmarks/ietf-interfaces-multikey.all-keyed-mod-prefix.csv -

test_status:
	pyang -f flatten --flatten-status ietf-interfaces.yang interfaces-ext.yang ietf-yang-types.yang | diff benchmarks/ietf-interfaces.status.csv -

test_resolve_leafref:
	pyang -f flatten --flatten-resolve-leafref ietf-interfaces.yang ietf-yang-types.yang interfaces-ext.yang | diff benchmarks/ietf-interfaces.leafref.csv -
