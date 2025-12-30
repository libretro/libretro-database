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
	mkdir -p $(DESTDIR)$(INSTALLDIR)/metadat
	cp -ar -t $(DESTDIR)$(INSTALLDIR)/metadat metadat/arcade
	find $(DESTDIR)$(INSTALLDIR) -type f -name "*.zip" -delete
	find $(DESTDIR)$(INSTALLDIR) -type f -name "*.xml" -delete

test-install: all
	DESTDIR=/tmp/build $(MAKE) install

libretro-super:
	git clone https://github.com/libretro/libretro-super.git

libretro-super/retroarch: libretro-super
	cd libretro-super && SHALLOW_CLONE=1 ./libretro-fetch.sh retroarch

build: libretro-super/retroarch update-arcade
	rm -rf libretro-super/retroarch/media/libretrodb/dat
	rm -rf libretro-super/retroarch/media/libretrodb/metadat
	rm -rf libretro-super/retroarch/media/libretrodb/rdb
	cp -rf dat metadat rdb libretro-super/retroarch/media/libretrodb
	cd libretro-super && ./libretro-build-database.sh
	rm -rf rdb
	cp -rf libretro-super/retroarch/media/libretrodb/rdb .

# Updates the Arcade DAT files at metadat/arcade
update-arcade:
	rm -rf metadat/arcade/*.dat
	curl -o "metadat/arcade/DICE.dat" "https://raw.githubusercontent.com/mittonk/dice-libretro/refs/heads/main/dice_xml.dat"
	curl -o "metadat/arcade/FinalBurn Neo.dat" "https://raw.githubusercontent.com/libretro/FBNeo/refs/heads/master/dats/FinalBurn%20Neo%20(ClrMame%20Pro%20XML%2C%20Arcade%20only).dat"
	curl -o "metadat/arcade/MAME 0.37b5.dat" "https://raw.githubusercontent.com/libretro/mame2000-libretro/refs/heads/master/metadata/MAME%200.37b5%20XML.dat"
	curl -o "metadat/arcade/MAME 2003.dat" "https://raw.githubusercontent.com/libretro/mame2003-libretro/refs/heads/master/metadata/mame2003.xml"
	curl -o "metadat/arcade/MAME 2003 Plus.dat" "https://raw.githubusercontent.com/libretro/mame2003-plus-libretro/refs/heads/master/metadata/mame2003-plus.xml"
	curl -o "metadat/arcade/MAME 2010.dat" "https://raw.githubusercontent.com/libretro/mame2010-libretro/refs/heads/master/metadata/mame2010.xml"
