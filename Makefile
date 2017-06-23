DESTDIR := /tmp/libretro-database

all:
	@echo "Nothing to make for libretro-database."

install:
	mkdir -p $(DESTDIR)
	cp -ar * $(DESTDIR)
	rm -rf $(DESTDIR)/metadat
	rm $(DESTDIR)/Makefile
	rm $(DESTDIR)/configure
