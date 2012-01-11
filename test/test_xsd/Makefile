PYANG = pyang -Wnone

MODULES = a b c

test: clean ietf-inet-types.xsd
	@for m in $(MODULES); do 					\
	  echo -n "checking $$m...";					\
	  $(PYANG) $$m.yang || exit 1;					\
	  echo -n " generating xsd...";					\
	  $(PYANG) -f xsd -o $$m.xsd $$m.yang || exit 1;		\
	  echo " check xsd and xml...";					\
	  xmllint --noout --schema $$m.xsd $$m.xml || exit 1;		\
	  if [ -f $$m.bad.xml ]; then					\
	    echo " check xsd and bad xml...";				\
	    xmllint --noout --schema $$m.xsd $$m.bad.xml && exit 0;	\
	  fi;								\
	  echo -n " generating xsd (global ct)...";			\
	  $(PYANG) -f xsd --xsd-global-complex-types 			\
	      -o $$m.ct.xsd $$m.yang || exit 1;				\
	  echo " check xsd and xml...";					\
	  xmllint --noout --schema $$m.ct.xsd $$m.xml || exit 1;	\
	  if [ -f $$m.bad.xml ]; then					\
	    echo " check xsd and bad xml...";				\
	    xmllint --noout --schema $$m.xsd $$m.bad.xml && exit 0;	\
	  fi;								\
	  echo " ok";							\
	done

ietf-inet-types.xsd: ../../modules/ietf-inet-types.yang
	$(PYANG) -f xsd $< -o $@

clean:
	rm -rf *.xsd


