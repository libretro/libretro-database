DESTDIR := /tmp/libretro-database

all:
	@echo "Nothing to make for libretro-database."

install:
	mkdir -p $(DESTDIR)
	cp -ar * $(DESTDIR)
	rm -rf $(DESTDIR)/metadat $(DESTDIR)/scripts $(DESTDIR)/dat $(DESTDIR)/Makefile $(DESTDIR)/configure
