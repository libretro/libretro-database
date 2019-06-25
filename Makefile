# libretro-database
#
# This file provides some install and building commands for libretro-database.
#
# make install
#     Installs the needed files to the given DESTDIR and INSTALLDIR.
#
# make build
#     Builds the RDB files using libretro-super.

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

libretro-super:
	git clone https://github.com/libretro/libretro-super.git

libretro-super/retroarch: libretro-super
	cd libretro-super && SHALLOW_CLONE=1 ./libretro-fetch.sh retroarch

build: libretro-super/retroarch
	rm -rf libretro-super/retroarch/media/libretrodb/dat
	rm -rf libretro-super/retroarch/media/libretrodb/metadat
	rm -rf libretro-super/retroarch/media/libretrodb/rdb
	cp -rf dat metadat rdb libretro-super/retroarch/media/libretrodb
	cd libretro-super && ./libretro-build-database.sh
	rm -rf rdb
	cp -rf libretro-super/retroarch/media/libretrodb/rdb .
