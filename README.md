# RetroArch Database

RetroArch incoporates a ROM scanning system to automatically produce playlists. Each ROM that is scanned by the playlist generator is checked against a database of ROMs that are known to be good copies.

## Contents

- [`cht`](cht) Cheats to various games
- [`cursors`](cursors) Provides methods in order to query the playlists
- [`dat`](dat) Customized DAT files, maintained by the libretro team
- [`metadata`](metadata) Different metadata and third-party DATs available to the systems
- [`rdb`](rdb) The compiled RetroArch database files
- [`scripts`](scripts) Various scripts that are used to maintain the database files

## Sources

Generally, RetroArch's scanner is configured for ROMs that have been validated by [No-Intro](http://datomatic.no-intro.org) or Redump DAT files but many other source databases are also in use.

|System|Source|Repository|
|----|---|---|
|The 3DO Company - 3DO|Redump > Trurip > TOSEC|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Atari - 2600|[No-Intro](http://datomatic.no-intro.org)|
|Atari - 7800|[No-Intro](http://datomatic.no-intro.org)|
|Atari - Jaguar| [No-Intro](http://datomatic.no-intro.org)|
|Atari - Lynx|[No-Intro](http://datomatic.no-intro.org)|
|Bandai - WonderSwan|[No-Intro](http://datomatic.no-intro.org)|
|Bandai - WonderSwan Color|[No-Intro](http://datomatic.no-intro.org)|
|Cave Story|[CaveStory.org (English or Japanese)](http://www.cavestory.org)|
|DOS|[Total DOS Collection](http://www.totaldoscollection.org/)|[libretro-database-dos](https://github.com/robloach/libretro-database-dos)|
|FinalBurn Alpha - Arcade Games|pre-0.2.97.44|[lr-fbalpha dats](https://github.com/libretro/fbalpha/tree/master/dats)|
|FinalBurn Neo - Arcade Games|0.2.97.44 (WIP)|[lr-FBNeo dats](https://github.com/libretro/fbneo/tree/master/dats)|
|GCE - Vectrex|[No-Intro](http://datomatic.no-intro.org)|
|Id Software - Doom|Unknown|[libretro-database-doom](https://github.com/libretro/libretro-database/blob/master/dat/DOOM.dat)|
|Id Software - Quake|Unknown|[libretro-database-quake](https://github.com/libretro/libretro-database/blob/master/dat/Quake1.dat)|
|Lutro|Unknown|
|Magnavox - Odyssey2|[No-Intro](http://datomatic.no-intro.org)|
|MAME|MAME 0.37b5, 0.78, 0.139, 0.159|
|Microsoft - MSX|[No-Intro](http://datomatic.no-intro.org)|
|Microsoft - MSX 2|[No-Intro](http://datomatic.no-intro.org)|
|NEC - PC Engine CD - TurboGrafx-CD|Redump > Trurip > TOSEC|[libretro-dats](https://github.com/robloach/libretro-dats)|
|NEC - PC Engine - TurboGrafx 16|[No-Intro](http://datomatic.no-intro.org)|
|NEC - SuperGrafx|[No-Intro](http://datomatic.no-intro.org)|
|NEC - PC-FX|Redump > Trurip > TOSEC|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Famicom Disk System|[No-Intro](http://datomatic.no-intro.org)|
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
|Thomson - MO/TO|[ScreenScraper](https://www.screenscraper.fr)|[libretro-database-thomson](https://github.com/Zlika/libretro-database-thomson)|
|Uzebox|Unknown|

## Building

To build a complete set of RDB files for RetroArch or to generate a single RDB file, see [RetroArch/libretro-db/README.md](https://github.com/libretro/RetroArch/blob/master/libretro-db/README.md).

Alternatively, you can run the following command to rebuild all the RDBs locally:

```
make build
```
