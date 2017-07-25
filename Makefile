PREFIX := /usr
INSTALLDIR := $(PREFIX)/share/libretro/database

all:
	@echo "Nothing to make for libretro-database."

install:
	mkdir -p $(DESTDIR)$(INSTALLDIR)
	cp -ar -t $(DESTDIR)$(INSTALLDIR) cht cursors rdb

test-install: all
	DESTDIR=/tmp/build $(MAKE) install
