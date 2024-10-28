test:
	$(PYANG) --print-error-code \
	--deviation-module deviation-problem-dev.yang \
	deviation-problem.yang 2>&1 | grep KEY_BAD_CONFIG > /dev/null
