PYANG = pyang -Wnone

MODULES ?= $(wildcard *.yang)

test: clean out
	@for m in $(MODULES); do 					\
	  echo -n "trying $$m...";					\
	  $(PYANG) $$m --keep-comments --canonical -f yang -o out/$$m	\
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


