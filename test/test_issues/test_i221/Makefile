define BANNER
\n\
=============================== WARNING ==============================\n\
Problems with unicode suport:\n\
  - 'pyang' did not crash but unicode characters were striped\n\
\n
endef

define CLOSE
 =====================================================================
endef

PYANG = pyang -Werror -WWBAD_MODULE_NAME --keep-comments

MODULES ?= $(wildcard *.yang)

test: clean $(MODULES:.yang=.diff)
	$(MAKE) clean

%.yin: %.yang
	@echo "$<:"
	@echo -n "generating yin... "
	@$(PYANG) -f yin -o $@ $<
	@if [ ! -f $@ ]; then\
		echo "\nERROR: pyang crash (yang with unicode))";\
		exit 1;\
	fi

gen/%.yang: %.yin
	@mkdir -p gen
	@echo "generating yang from generated yin..."
	@$(PYANG) -f yang -o $@ $<
	@if [ ! -f $@ ]; then\
		echo "\nERROR: pyang crash (yin with unicode))";\
		exit 1;\
	fi

%.diff: gen/%.yang
	@echo "comparing $(subst gen/,,$<) with $<... "
	@diff -bw $(subst gen/,,$<) $< > $@ ||\
		{ echo "$(BANNER)"; cat $@; echo "$(CLOSE)"; }
	@echo "ok\n\n"

clean:
	@rm -rf *.yin *.diff gen
