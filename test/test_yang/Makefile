PYANG = pyang -Wnone
PYANG_OLD_FLAGS = --keep-comments --canonical
PYANG_NEW_FLAGS = --keep-comments --yang-keep-blank-lines

MODULES ?= $(wildcard *.yang)

MODULES_NEW ?= b.yang
MODULES_OLD ?= $(filter-out $(MODULES_NEW), $(MODULES))



test: clean out
	@for m in $(MODULES_OLD); do 					\
	  echo -n "trying $$m...";					\
	  $(PYANG) $$m $(PYANG_OLD_FLAGS) -f yang -o out/$$m		\
	    || exit 1;							\
	  diff expect/$$m out/$$m > $$m.diff 				\
	    || { cat $$m.diff; exit 1; };				\
	  rm -f $$m.diff;						\
	  echo " ok";							\
	done
	@for m in $(MODULES_NEW); do 					\
	  echo -n "trying $$m...";					\
	  $(PYANG) $$m $(PYANG_NEW_FLAGS) -f yang -o out/$$m		\
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


