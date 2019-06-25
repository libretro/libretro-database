#! /usr/bin/env bash
# vim: set ts=3 sw=3 noet ft=sh : bash

# BSDs don't have readlink -f
read_link()
{
	TARGET_FILE="$1"
	cd $(dirname "$TARGET_FILE")
	TARGET_FILE=$(basename "$TARGET_FILE")

	while [ -L "$TARGET_FILE" ]
	do
		TARGET_FILE=$(readlink "$TARGET_FILE")
		cd $(dirname "$TARGET_FILE")
		TARGET_FILE=$(basename "$TARGET_FILE")
	done

	PHYS_DIR=$(pwd -P)
	RESULT="$PHYS_DIR/$TARGET_FILE"
	echo $RESULT
}

SCRIPT=$(read_link "$0")
echo "Script: $SCRIPT"
BASE_DIR=$(dirname .)
LIBRETRODATABASE_BASE_DIR="$BASE_DIR/"
RDB_DIR="${LIBRETRODATABASE_BASE_DIR}/rdb"
LIBRETRODB_BASE_DIR=$BASE_DIR
LIBRETRODATABASE_DAT_DIR=${LIBRETRODATABASE_BASE_DIR}/dat
LIBRETRODATABASE_META_DAT_DIR=${LIBRETRODATABASE_BASE_DIR}/metadat

die()
{
	echo $1
	#exit 1
}

echo $LIBRETRODB_BASE


# $1 is name
# $2 is match key
build_libretro_database() {
	cd "$BASE_DIR"
	if [ -d "$LIBRETRODB_BASE_DIR" ]; then
		DBFILE=${BASE_DIR}/${LIBRETRODB_BASE_DIR}/db.rdb
		cd "${LIBRETRODB_BASE_DIR}"
		echo "=== Building ${1} ==="
		COMMAND='${BASE_DIR}/${LIBRETRODB_BASE_DIR}/c_converter ${DBFILE} "${2}"'

		#Check if meta DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/${1}.dat"'
		fi

		#Check if meta goodtools is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/goodtools/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/goodtools/${1}.dat"'
		fi

		#Check if meta analog DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/analog/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/analog/${1}.dat"'
		fi

		#Check if meta barcode DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/barcode/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/barcode/${1}.dat"'
		fi

		#Check if meta BBFC DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/bbfc/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/bbfc/${1}.dat"'
		fi

		#Check if meta developer DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/developer/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/developer/${1}.dat"'
		fi

		#Check if meta ELSPA DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/elspa/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/elspa/${1}.dat"'
		fi

		#Check if meta ESRB DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/esrb/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/esrb/${1}.dat"'
		fi

		#Check if meta franchise DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/franchise/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/franchise/${1}.dat"'
		fi

		#Check if meta Famitsu magazine DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/magazine/famitsu/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/magazine/famitsu/${1}.dat"'
		fi

		#Check if meta Edge magazine DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/magazine/edge/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/magazine/edge/${1}.dat"'
		fi

		#Check if meta Edge magazine review DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/magazine/edge_review/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/magazine/edge_review/${1}.dat"'
		fi

		#Check if meta maxusers DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/maxusers/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/maxusers/${1}.dat"'
		fi

		#Check if meta origin DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/origin/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/origin/${1}.dat"'
		fi

		#Check if meta publisher DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/publisher/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/publisher/${1}.dat"'
		fi

		#Check if meta releasemonth DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/releasemonth/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/releasemonth/${1}.dat"'
		fi

		#Check if meta releaseyear DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/releaseyear/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/releaseyear/${1}.dat"'
		fi

		#Check if meta rumble DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/rumble/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/rumble/${1}.dat"'
		fi

		#Check if meta serial DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/serial/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/serial/${1}.dat"'
		fi

		#Check if meta enhancement HW DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/enhancement_hw/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/enhancement_hw/${1}.dat"'
		fi

		#Check if meta TGDB DAT is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/tgdb/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/tgdb/${1}.dat"'
		fi

		#Check if meta hacks is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/hacks/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/hacks/${1}.dat"'
		fi

		#Check for the MAME folders
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/mame-nonmerged/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/mame-nonmerged/${1}.dat"'
		fi
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/mame-split/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/mame-split/${1}.dat"'
		fi
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/mame-member/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/mame-member/${1}.dat"'
		fi
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/mame/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/mame/${1}.dat"'
		fi

		#Check for Final Burn Alpha folders
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/fba-merged/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/fba-merged/${1}.dat"'
		fi
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/fba-split/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/fba-split/${1}.dat"'
		fi
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/fba-member/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/fba-member/${1}.dat"'
		fi

		#Check if meta libretro-dats folder is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/libretro-dats/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/libretro-dats/${1}.dat"'
		fi

		#Check if meta redump is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/redump/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/redump/${1}.dat"'
		fi

		#Check if meta no-intro is there
		if [ -f "${LIBRETRODATABASE_META_DAT_DIR}/no-intro/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_META_DAT_DIR}/no-intro/${1}.dat"'
		fi

		#Check if main DAT is there
		if [ -f "${LIBRETRODATABASE_DAT_DIR}/${1}.dat" ]; then
			COMMAND+=' "${LIBRETRODATABASE_DAT_DIR}/${1}.dat"'
		fi

		eval ${COMMAND}
		if [ -f ${DBFILE} ]; then
			mv ${DBFILE} "${RDB_DIR}/${1}.rdb"
		fi
	fi
}

build_libretro_databases() {
	build_libretro_database "Amstrad - CPC" "rom.crc"
	build_libretro_database "Mattel - Intellivision" "rom.crc"
	build_libretro_database "ScummVM" "rom.crc"
	build_libretro_database "DOS" "rom.crc"
	build_libretro_database "Lutro" "rom.name"
	build_libretro_database "ChaiLove" "rom.crc"
	build_libretro_database "TIC-80" "rom.crc"
	build_libretro_database "MrBoom" "rom.crc"
	build_libretro_database "Cannonball" "rom.crc"
	build_libretro_database "Nintendo - Super Nintendo Entertainment System" "rom.crc"
	build_libretro_database "Nintendo - Super Nintendo Entertainment System Hacks" "rom.crc"
	build_libretro_database "Sony - PlayStation" "rom.serial"
	build_libretro_database "Sony - PlayStation 3" "rom.serial"
	build_libretro_database "Atari - Jaguar" "rom.crc"
	build_libretro_database "Nintendo - Nintendo 64" "rom.crc"
	build_libretro_database "Nintendo - Nintendo 64DD" "rom.crc"
	build_libretro_database "Nintendo - Virtual Boy" "rom.crc"
	build_libretro_database "Atari - 2600" "rom.crc"
	build_libretro_database "Atari - 5200" "rom.crc"
	build_libretro_database "Atari - 7800" "rom.crc"
	build_libretro_database "Atari - Lynx" "rom.crc"
	build_libretro_database "Atari - ST" "rom.crc"
	build_libretro_database "Bandai - WonderSwan" "rom.crc"
	build_libretro_database "Bandai - WonderSwan Color" "rom.crc"
	build_libretro_database "Casio - Loopy" "rom.crc"
	build_libretro_database "Casio - PV-1000" "rom.crc"
	build_libretro_database "Coleco - ColecoVision" "rom.crc"
	build_libretro_database "Commodore - 64" "rom.crc"
	build_libretro_database "Commodore - Amiga" "rom.crc"
	build_libretro_database "Commodore - Plus-4" "rom.crc"
	build_libretro_database "Commodore - VIC-20" "rom.crc"
	build_libretro_database "Dinothawr" "rom.crc"
	build_libretro_database "Emerson - Arcadia 2001" "rom.crc"
	build_libretro_database "Entex - Adventure Vision" "rom.crc"
	build_libretro_database "Epoch - Super Cassette Vision" "rom.crc"
	build_libretro_database "Fairchild - Channel F" "rom.crc"
	build_libretro_database "Funtech - Super Acan" "rom.crc"
	build_libretro_database "Handheld Electronic Game" "rom.crc"
	build_libretro_database "GamePark - GP32" "rom.crc"
	build_libretro_database "GCE - Vectrex" "rom.crc"
	build_libretro_database "Hartung - Game Master" "rom.crc"
	build_libretro_database "LeapFrog - Leapster Learning Game System" "rom.crc"
	build_libretro_database "Magnavox - Odyssey2" "rom.crc"
	build_libretro_database "Microsoft - MSX" "rom.crc"
	build_libretro_database "Microsoft - MSX2" "rom.crc"
	build_libretro_database "Microsoft - Xbox" "rom.crc"
	build_libretro_database "NEC - PC Engine CD - TurboGrafx-CD" "rom.crc"
	build_libretro_database "NEC - PC Engine - TurboGrafx 16" "rom.crc"
	build_libretro_database "NEC - PC Engine SuperGrafx" "rom.crc"
	build_libretro_database "NEC - PC-FX" "rom.crc"
	build_libretro_database "Nintendo - Family Computer Disk System" "rom.crc"
	build_libretro_database "Nintendo - Game Boy" "rom.crc"
	build_libretro_database "Nintendo - Game Boy Advance" "rom.crc"
	build_libretro_database "Nintendo - e-Reader" "rom.crc"
	build_libretro_database "Nintendo - Game Boy Color" "rom.crc"
	build_libretro_database "Nintendo - GameCube" "rom.serial"
	build_libretro_database "Nintendo - Nintendo 3DS" "rom.crc"
	build_libretro_database "Nintendo - Nintendo 3DS (Digital)" "rom.crc"
	build_libretro_database "Nintendo - Nintendo DS" "rom.crc"
	build_libretro_database "Nintendo - Nintendo DS (Download Play)" "rom.crc"
	build_libretro_database "Nintendo - Nintendo DSi" "rom.crc"
	build_libretro_database "Nintendo - Nintendo DSi (Digital)" "rom.crc"
	build_libretro_database "Nintendo - Nintendo Entertainment System" "rom.crc"
	build_libretro_database "Nintendo - Pokemon Mini" "rom.crc"
	build_libretro_database "Nintendo - Satellaview" "rom.crc"
	build_libretro_database "Nintendo - Sufami Turbo" "rom.crc"
	build_libretro_database "Nintendo - Wii" "rom.serial"
	build_libretro_database "Nintendo - Wii (Digital)" "rom.crc"
	build_libretro_database "The 3DO Company - 3DO" "rom.crc"
	build_libretro_database "Philips - Videopac+" "rom.crc"
	build_libretro_database "RCA - Studio II" "rom.crc"
	build_libretro_database "Rick Dangerous" "rom.crc"
	build_libretro_database "Sega - 32X" "rom.crc"
	build_libretro_database "Sega - Dreamcast" "rom.crc"
	build_libretro_database "Sega - Game Gear" "rom.crc"
	build_libretro_database "Sega - Master System - Mark III" "rom.crc"
	build_libretro_database "Sega - Mega-CD - Sega CD" "rom.crc"
	build_libretro_database "Sega - Mega Drive - Genesis" "rom.crc"
	build_libretro_database "Sega - PICO" "rom.crc"
	build_libretro_database "Sega - Saturn" "rom.crc"
	build_libretro_database "Sega - SG-1000" "rom.crc"
	build_libretro_database "Sharp - X68000" "rom.crc"
	build_libretro_database "Sinclair - ZX Spectrum" "rom.crc"
	build_libretro_database "Sinclair - ZX Spectrum +3" "rom.crc"
	build_libretro_database "Sinclair - ZX 81" "rom.crc"
	build_libretro_database "SNK - Neo Geo CD" "rom.crc"
	build_libretro_database "SNK - Neo Geo Pocket" "rom.crc"
	build_libretro_database "SNK - Neo Geo Pocket Color" "rom.crc"
	build_libretro_database "Sony - PlayStation 2" "rom.serial"
	build_libretro_database "Sony - PlayStation 3 (PSN)" "rom.crc"
	build_libretro_database "Sony - PlayStation Portable" "rom.serial"
	build_libretro_database "Sony - PlayStation Portable (PSN)" "rom.crc"
	build_libretro_database "Sony - PlayStation Portable (PSX2PSP)" "rom.crc"
	build_libretro_database "Sony - PlayStation Portable (UMD Music)" "rom.crc"
	build_libretro_database "Sony - PlayStation Portable (UMD Video)" "rom.crc"
	build_libretro_database "Sony - PlayStation Vita" "rom.serial"
	build_libretro_database "Thomson - MOTO" "rom.crc"
	build_libretro_database "Tiger - Game.com" "rom.crc"
	build_libretro_database "Tomb Raider" "rom.crc"
	build_libretro_database "Uzebox" "rom.crc"
	build_libretro_database "VTech - CreatiVision" "rom.crc"
	build_libretro_database "VTech - V.Smile" "rom.crc"
	build_libretro_database "Watara - Supervision" "rom.crc"
	build_libretro_database "MAME" "rom.crc"
	build_libretro_database "MAME 2000" "rom.crc"
	build_libretro_database "MAME 2003" "rom.crc"
	build_libretro_database "MAME 2003-Plus" "rom.crc"
	build_libretro_database "MAME 2010" "rom.crc"
	build_libretro_database "MAME 2015" "rom.crc"
	build_libretro_database "MAME 2016" "rom.crc"
	build_libretro_database "FB Alpha - Arcade Games" "rom.crc"
	build_libretro_database "DOOM" "rom.crc"
	build_libretro_database "Cave Story" "rom.crc"
	build_libretro_database "Quake1" "rom.crc"
	build_libretro_database "RPG Maker" "rom.crc"
	build_libretro_database "Flashback" "rom.crc"
}

build_libretrodb
build_libretro_databases
