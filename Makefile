sdist: MANIFEST doc
	python setup.py sdist

bdist: MANIFEST doc
	python setup.py bdist

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

MANIFEST:
	@if [ -d .svn ] ; then \
	    svn list -R > $@; \
	elif [ -d .git ] ; then \
	    git ls-files > $@; \
	else \
	    echo "MANIFEST can only be generated from SVN or git."; \
	fi

tags:
	find . -name "*.py" | etags -