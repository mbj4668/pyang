PYANG := $(PYANG) -Wnone

MODULES ?= $(wildcard *.yang)

SEDSCRIPT = sed -e 's/[^-]*//' -e 's/\.yang//' -e 's/--/ --/g'

HOME := $(shell pwd)/out

test: clean out
	@for m in $(MODULES); do 					\
	  echo "trying $$m..." | tr -d '\012';				\
	  x=`echo $$m | $(SEDSCRIPT)`;					\
	  o=`echo $$m | sed -e 's/\.yang/.stderr/'`;			\
	  HOME=$(HOME) $(PYANG) --verbose $$x $$m 2>&1 |                \
	    grep -v '^# module search path' > out/$$o		        \
	    || exit 1;							\
	  diff expect/$$o out/$$o > $$o.diff                     	\
	    || { cat $$o.diff; exit 1; };				\
	  rm -f $$o.diff;						\
	  echo " ok";							\
	done

out:
	mkdir out

clean:
	rm -rf out *diff


