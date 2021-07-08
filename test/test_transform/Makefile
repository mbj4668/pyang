ifeq "$(origin PYANG)" "undefined"
  PYANG = pyang
endif

PYANG := $(PYANG) -Wnone

MODULES ?= $(wildcard *.yang)

SEDSCRIPT = sed -e 's/[^-]*//' -e 's/-bug//' -e 's/\.yang//' -e 's/--/ --/g'

test: clean out
	@for m in $(MODULES); do 					\
	  echo "trying $$m..." | tr -d '\012';				\
	  x=`echo $$m | $(SEDSCRIPT)`;					\
	  t=`echo $$m | sed -e 's/\.yang/.out/'`;			\
	  $(PYANG) --plugindir . -f tree $$x $$m -o out/$$t		\
	    || exit 1;							\
	  diff expect/$$t out/$$t > $$t.diff 				\
	    || { cat $$t.diff; exit 1; };				\
	  rm -f $$t.diff;						\
	  echo " ok";							\
	done

out:
	mkdir out

clean:
	rm -rf out *.diff
