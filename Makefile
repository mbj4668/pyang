sdist: 
	python setup.py sdist

bdist: 
	python setup.py bdist

.PHONY:	test
test:
	(cd test; $(MAKE) test)

clean:
	(cd test && $(MAKE) clean)
	rm -rf build dist MANIFEST
	find . -name "*.pyc" -exec rm {} \;
