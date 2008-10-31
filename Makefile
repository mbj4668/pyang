sdist: MANIFEST
	python setup.py sdist

bdist: MANIFEST
	python setup.py bdist

.PHONY:	test
test:
	(cd test; $(MAKE) test)

clean:
	(cd test && $(MAKE) clean)
	python setup.py clean --all
	rm -rf build dist MANIFEST
	find . -name "*.pyc" -exec rm {} \;

MANIFEST:
	svn list -R > $@
