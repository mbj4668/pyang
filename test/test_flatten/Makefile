test: test_xpath test_deviation test_deviation_show test_all test_rpc_notif test_filter_keyword test_filter_primitive test_filter_flag

test_xpath:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang | diff benchmarks/ietf-interfaces.xpath.csv -

test_deviation:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang ietf-interfaces-deviations.yang | diff benchmarks/ietf-interfaces.dev.csv -

test_deviation_show:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang ietf-interfaces-deviations.yang --flatten-deviated | diff benchmarks/ietf-interfaces.dev-show.csv -

test_all:
	pyang -f flatten interfaces-ext.yang ietf-yang-types.yang ietf-interfaces.yang ietf-interfaces-deviations.yang --flatten-keyword --flatten-type --flatten-primitive-type --flatten-flag --flatten-description --flatten-deviated --flatten-data-keywords | diff benchmarks/ietf-interfaces.all.csv -

test_rpc_notif:
	pyang -f flatten x.yang y.yang --flatten-keyword --flatten-data-keywords | diff benchmarks/xy.flatten.csv -

test_filter_keyword:
	pyang -f flatten ietf-yang-types.yang ietf-interfaces.yang --flatten-keyword --flatten-filter-keyword leaf | diff benchmarks/ietf-interfaces.leaf.csv -

test_filter_primitive:
	pyang -f flatten ietf-yang-types.yang ietf-interfaces.yang --flatten-primitive --flatten-filter-primitive uint64 | diff benchmarks/ietf-interfaces.uint64.csv -

test_filter_flag:
	pyang -f flatten ietf-yang-types.yang ietf-interfaces.yang --flatten-flag --flatten-filter-flag rw | diff benchmarks/ietf-interfaces.rw.csv -
