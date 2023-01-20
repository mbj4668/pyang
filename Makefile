export W := $(shell pwd)

# create a full source package
sdist: build
	python setup.py sdist
	-# mv dist/pyang-*.tar.gz dist/pyang_src-*.tar.gz

# create a minimal package
dist: build
	python setup.py sdist

.PHONY:	test tags clean doc build lint pylint
build: doc pyang/xpath_parsetab.py

doc:
	(cd doc; $(MAKE))

pyang/xpath_parsetab.py: pyang/xpath_parser.py
	python -m pyang.xpath_parser

test: lint
	(cd test; $(MAKE) test)

lint:
	flake8 .

pylint:
	pylint pyang $(shell find test -name '*.py') || true

clean:
	rm -f pyang/parser.out pyang/xpath_parsetab.py
	(cd test && $(MAKE) clean)
	(cd doc &&  $(MAKE) clean)
	python setup.py clean --all
	rm -rf build dist MANIFEST
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

tags:
	find . -name "*.py" | etags -
