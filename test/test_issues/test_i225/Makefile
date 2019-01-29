ifeq ($(USE_VIRTUALENV),true)
test:
	# it is not possible to run 'source' from Makefile,
	# since it is required for virtualenv, call a bash script
	bash test.sh
else
test:
	# skip
endif
