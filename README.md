# RetroArch Database

RetroArch incoporates a ROM scanning system to automatically produce playlists. Each ROM that is scanned by the playlist generator is checked against a database of ROMs that are known to be good copies.

## Contents

- [`cht`](cht) Cheats to various games
- [`cursors`](cursors) Provides methods in order to query the playlists
- [`dat`](dat) Customized DAT files, maintained by the libretro team
- [`metadat`](metadat) Different metadata and third-party DATs available to the systems
- [`rdb`](rdb) The compiled RetroArch database files
- [`scripts`](scripts) Various scripts that are used to maintain the database files

## Sources

Generally, RetroArch's scanner is configured for ROMs that have been validated by [No-Intro](http://datomatic.no-intro.org) or Redump DAT files but many other source databases are also in use.

|System|Source|Repository|
|----|---|---|
|Amstrad - CPC| [Clean CPC DB](https://github.com/clean-cpc-db/dat) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Amstrad - GX4000|[TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Arduboy Inc - Arduboy|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Atari - 2600|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Atari - 5200|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Atari - 7800|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Atari - 8-bit|[No-Intro](http://datomatic.no-intro.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Atari - Jaguar| [No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Atari - Lynx|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Atari - ST|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Atomiswave| |
|Bandai - WonderSwan|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Bandai - WonderSwan Color|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Cannonball| |
|Casio - Loopy|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Casio - PV-1000|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Cave Story|[CaveStory.org (English or Japanese)](http://www.cavestory.org)|
|ChaiLove| |
|CHIP-8| |
|Coleco - ColecoVision|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Commodore - 64|[No-Intro](http://datomatic.no-intro.org) (Note: cartridges, tapes and Preservation Project disk images)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Commodore - Amiga|WHDLoad > [No-Intro](http://datomatic.no-intro.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Commodore - CD32|Redump > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Commodore - CDTV|Redump > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Commodore - PET|[TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Commodore - Plus-4|[No-Intro](http://datomatic.no-intro.org) (Note: cartridges only)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Commodore - VIC-20|[No-Intro](http://datomatic.no-intro.org) (Note: cartridges only)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Dinothawr| |
|DOS|[Total DOS Collection](http://www.totaldoscollection.org/)|[libretro-database-dos](https://github.com/robloach/libretro-database-dos)|
|Emerson - Arcadia 2001|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Entex - Adventure Vision|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Epoch - Super Cassette Vision|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Fairchild - Channel F|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|FinalBurn Neo - Arcade Games 1.0.0.03|[FBNeo/dats](https://github.com/libretro/FBNeo/tree/master/dats)|
|Flashback| |
|Funtech - Super Acan|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|GamePark - GP32|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|GCE - Vectrex|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Handheld Electronic Game| |
|Hartung - Game Master|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Infocom - Z-Machine|[TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Jump 'n Bump| |
|LeapFrog - Leapster Learning Game System|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|LowRes NX| |
|Id Software - Doom|Unknown|[libretro-database-doom](https://github.com/libretro/libretro-database/blob/master/dat/DOOM.dat)|
|Id Software - Quake|Unknown|[libretro-database-quake](https://github.com/libretro/libretro-database/blob/master/dat/Quake1.dat)|
|Lutro|Unknown|
|MAME|MAME 0.37b5, 0.78, 0.139, 0.159|
|Magnavox - Odyssey2|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Mattel - Intellivision|[No-Intro](http://datomatic.no-intro.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Microsoft - MSX|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Microsoft - MSX 2|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Microsoft - Xbox|Redump (Note: there is no libretro emulator)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|MicroW8| |
|MrBoom| |
|NEC - PC-8001 - PC-8801.rdb|[TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|NEC - PC-98|Redump > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|NEC - PC Engine - TurboGrafx 16|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|NEC - PC Engine SuperGrafx|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|NEC - PC Engine CD - TurboGrafx-CD|Redump > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|NEC - PC-FX|Redump > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Family Computer Disk System|[No-Intro](http://datomatic.no-intro.org)|
|Nintendo - Nintendo DS|[No-Intro](http://datomatic.no-intro.org)|
|Nintendo - Game Boy|[No-Intro](http://datomatic.no-intro.org)|
|Nintendo - Game Boy Advance|[No-Intro](http://datomatic.no-intro.org)|
|Nintendo - Game Boy Color|[No-Intro](http://datomatic.no-intro.org)|
|Nintendo - Nintendo 64|[No-Intro](http://datomatic.no-intro.org)|
|Nintendo - Nintendo Entertainment System|[No-Intro](http://datomatic.no-intro.org)|
|Nintendo - Super Nintendo Entertainment System|[No-Intro](http://datomatic.no-intro.org)|
|Nintendo - Virtual Boy|[No-Intro](http://datomatic.no-intro.org)|
|Phillips - Videopac+|[No-Intro](http://datomatic.no-intro.org)|
|ScummVM|Gruby's ScummVM Adventure Pack|[libretro-database-scummvm](https://github.com/RobLoach/libretro-database-scummvm)|
|Sega - 32X|[No-Intro](http://datomatic.no-intro.org)|
|Sega - Dreamcast|Redump > Trurip > TOSEC|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - Game Gear|[No-Intro](http://datomatic.no-intro.org)|
|Sega - Master System - Mark III|[No-Intro](http://datomatic.no-intro.org)|
|Sega - Mega Drive - Genesis|[No-Intro](http://datomatic.no-intro.org)|
|Sega - Mega CD - Sega CD|Redump|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - Saturn|Redump > Trurip > TOSEC|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - SG-1000|[No-Intro](http://datomatic.no-intro.org)|
|Sony - PlayStation|Redump > Trurip > TOSEC|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sony - PlayStation Portable|[No-Intro](http://datomatic.no-intro.org)|[libretro-database-dos](https://github.com/robloach/libretro-database-dos)|
|SNK - Neo Geo Pocket|[No-Intro](http://datomatic.no-intro.org)|
|SNK - Neo Geo Pocket Color|[No-Intro](http://datomatic.no-intro.org)|
|SNK - Neo Geo CD|Redump|[libretro-dats](https://github.com/robloach/libretro-dats)|
|The 3DO Company - 3DO|Redump > Trurip > TOSEC|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Thomson - MO/TO|[ScreenScraper](https://www.screenscraper.fr)|[libretro-database-thomson](https://github.com/Zlika/libretro-database-thomson)|
|Uzebox|Unknown|

## Building

To build a complete set of RDB files for RetroArch or to generate a single RDB file, see [RetroArch/libretro-db/README.md](https://github.com/libretro/RetroArch/blob/master/libretro-db/README.md).

Alternatively, you can run the following command to rebuild all the RDBs locally:

```
make build
```
