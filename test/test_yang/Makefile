PYANG = pyang -Wnone
PYANG_OLD_FLAGS = --keep-comments --canonical
PYANG_NEW_FLAGS = --keep-comments --yang-keep-blank-lines

MODULES ?= $(wildcard *.yang)



test: clean out
	@for m in $(MODULES); do 					\
	  echo -n "trying $$m (old flags)...";				\
	  $(PYANG) $$m $(PYANG_OLD_FLAGS) -f yang -o out/$$m		\
	    || exit 1;							\
	  diff expect/$$m out/$$m > $$m.diff 				\
	    || { cat $$m.diff; exit 1; };				\
	  rm -f $$m.diff;						\
	  echo " ok";							\
	done
	@for m in $(MODULES); do 					\
	  echo -n "trying $$m (new flags)...";				\
	  $(PYANG) $$m $(PYANG_NEW_FLAGS) -f yang -o out2/$$m		\
	    || exit 1;							\
	  diff expect2/$$m out2/$$m > $$m.diff 				\
	    || { cat $$m.diff; exit 1; };				\
	  rm -f $$m.diff;						\
	  echo " ok";							\
	done

out:
	mkdir out out2

clean:
	rm -rf out out2 *diff


