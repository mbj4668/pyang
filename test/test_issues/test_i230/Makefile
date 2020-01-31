test:
	PYANG_PLUGINPATH=. $(PYANG) -f yin example-sports.yang \
			 -o example-sports.yin
	$(PYANG) -f tree --tree-path=sports/person/name example-sports.yang \
		-o example-sports.tree
	$(PYANG) -f omni --omni-path=sports/person/name example-sports.yang \
		-o example-sports.omni
	rm -f *.yin *.tree *.omni

