all:
	@echo "Nothing to make for libretro-database."

install:
ifneq ($(DESTDIR),)
	mkdir -p $(DESTDIR)
	cp -ar * $(DESTDIR)
	rm -rf $(DESTDIR)/metadat $(DESTDIR)/scripts $(DESTDIR)/dat $(DESTDIR)/Makefile $(DESTDIR)/configure
else
	@echo "Define DESTDIR if you are installing files to a specific directory."
endif
