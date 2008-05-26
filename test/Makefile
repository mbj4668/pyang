DIRS = $(shell for d in test_* ; do [ -d $$d -a -f $$d/Makefile ] && echo $$d ; done)

test: 
	for d in $(DIRS); do 						\
		( echo "" ; echo "=== running test: $$d ==="; echo "";	\
		  cd $$d && $(MAKE) $@				        \
		) || exit 1 ;				 		\
	 done

clean: 
	for d in $(DIRS); do 						\
		  (cd $$d && $(MAKE) $@)			        \
	done
