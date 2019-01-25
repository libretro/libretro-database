PREFIX := /usr
INSTALLDIR := $(PREFIX)/share/libretro/database

all:
	@echo "Nothing to make for libretro-database."

install:
	mkdir -p $(DESTDIR)$(INSTALLDIR)
	cp -ar -t $(DESTDIR)$(INSTALLDIR) cht cursors rdb
	find $(DESTDIR)$(INSTALLDIR) -type f -name "*.zip" -delete
	find $(DESTDIR)$(INSTALLDIR) -type f -name "*.xml" -delete

test-install: all
	DESTDIR=/tmp/build $(MAKE) install
