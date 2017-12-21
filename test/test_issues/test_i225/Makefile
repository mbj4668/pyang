ifeq ($(SKIP_VIRTUALENV),true)
test:
	# skip
else
test:
	# it is not possible to run 'source' from Makefile,
	# since it is required for virtualenv, call a bash script
	bash test.sh
endif
