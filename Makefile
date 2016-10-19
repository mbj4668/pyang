# create a full source package
sdist: doc
	python setup.py sdist
	-# mv dist/pyang-*.tar.gz dist/pyang_src-*.tar.gz

# create a minimal package
dist: doc
	python setup.py sdist

.PHONY:	test tags clean doc
doc:
	(cd doc; $(MAKE))

test:
	(cd test; $(MAKE) test)

clean:
	(cd test && $(MAKE) clean)
	(cd doc &&  $(MAKE) clean)
	python setup.py clean --all
	rm -rf build dist MANIFEST
	find . -name "*.pyc" -exec rm {} \;

tags:
	find . -name "*.py" | etags -
