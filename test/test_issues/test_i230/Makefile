test:
	PYANG_PLUGINPATH=. pyang -f yin example-sports.yang \
			 -o example-sports.yin
	pyang -f tree --tree-path=sports/person/name example-sports.yang \
		-o example-sports.tree
	pyang -f omni --omni-path=sports/person/name example-sports.yang \
		-o example-sports.omni
	rm -f *.yin *.tree *.omni

