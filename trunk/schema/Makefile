RNC = hello-server.rnc yin-html.rnc
.PHONY: all clean

all: $(RNC)

yin-html.rng: yin.rng
	@touch $@

%.rnc: %.rng
	trang -I rng -O rnc $< $@

clean:
	rm -f *.rnc
