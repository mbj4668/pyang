PYANG := $(PYANG) -Wnone

MODULES ?= $(wildcard *.yang)

SEDSCRIPT = sed -e 's/[^-]*//' -e 's/\.yang//' -e 's/--/ --/g'

HOME := $(shell pwd)/out
SYSPATH := $(shell python -c 'import sys; print(sys.prefix + "/share/yang/modules")')
SEDEXPR := "s:_HOME_:$(HOME):g;s:_ROOT_:$(W):g"
ifneq ($(wildcard $(SYSPATH)),)
SEDEXPR := $(SEDEXPR)";s@_SYSPATH_@:$(SYSPATH)@g"
else
SEDEXPR := $(SEDEXPR)";s@_SYSPATH_@@g"
endif

test: clean out
	@for m in $(MODULES); do 					\
	  echo "trying $$m..." | tr -d '\012';				\
	  x=`echo $$m | $(SEDSCRIPT)`;					\
	  o=`echo $$m | sed -e 's/\.yang/.stderr/'`;			\
	  HOME=$(HOME) $(PYANG) --verbose $$x $$m 2>out/$$o		\
	    || exit 1;							\
	  sed -e $(SEDEXPR) expect/$$o | diff - out/$$o > $$o.diff	\
	    || { cat $$o.diff; exit 1; };				\
	  rm -f $$o.diff;						\
	  echo " ok";							\
	done

out:
	mkdir out

clean:
	rm -rf out *diff


