PYANG := $(PYANG) -Wnone

MODULES ?= $(wildcard *.yang)

SEDSCRIPT = sed -e 's/[^-]*//' -e 's/\.yang//' -e 's/--/ --/g' -e 's/_/ /g'

test: clean out
	@for m in $(MODULES); do 					\
	  echo "trying $$m..." | tr -d '\012';				\
	  x=`echo $$m | $(SEDSCRIPT)`;					\
	  $(PYANG) -f yang $$x $$m -o out/$$m				\
	    || exit 1;							\
	  diff expect/$$m out/$$m > $$m.diff 				\
	    || { cat $$m.diff; exit 1; };				\
	  rm -f $$m.diff;						\
	  echo " ok";							\
	done

out:
	mkdir out

clean:
	rm -rf out *diff


