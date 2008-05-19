# After you have made all you can point PYTHONPATH to here and off you go...
all: version.txt confd_api.so

sdist: 
	python setup.py sdist

bdist: 
	python setup.py bdist

test:
        @env PYTHONPATH="$(PWD)" python test/test1.py

clean:
	rm -rf build dist MANIFEST
	find . -name "*.pyc" -exec rm {} \;
