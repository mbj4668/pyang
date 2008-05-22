sdist: 
	python setup.py sdist

bdist: 
	python setup.py bdist

test:
        @env PYTHONPATH="$(PWD)" python test/test1.py

clean:
	(cd test && $(MAKE) clean)
	rm -rf build dist MANIFEST
	find . -name "*.pyc" -exec rm {} \;
