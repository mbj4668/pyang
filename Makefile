# create a full source package
sdist: MANIFEST doc
	rm -f MANIFEST.in
	python setup.py sdist
	-# mv dist/pyang-*.tar.gz dist/pyang_src-*.tar.gz

# create a minimal package
dist: doc
	rm -f MANIFEST
	echo "include LICENSE" > MANIFEST.in
	echo "include env.sh" >> MANIFEST.in
	echo "recursive-include man *" >> MANIFEST.in
	echo "recursive-include schema *" >> MANIFEST.in
	echo "recursive-include xslt *" >> MANIFEST.in
	echo "recursive-include modules *" >> MANIFEST.in
	echo "recursive-include tools/images *" >> MANIFEST.in
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
	rm -rf build dist MANIFEST*
	find . -name "*.pyc" -exec rm {} \;

MANIFEST:
	@if [ -d .svn ] ; then \
	    svn list -R | grep -v ".gitignore" > $@; \
	elif [ -d .git ] ; then \
	    git ls-files > $@; \
	else \
	    echo "MANIFEST can only be generated from SVN or git."; \
	fi

tags:
	find . -name "*.py" | etags -
