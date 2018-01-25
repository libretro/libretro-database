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
|FB Alpha - Arcade Games|FB Alpha v0.2.97.42|
|GCE - Vectrex|[No-Intro](http://datomatic.no-intro.org)|
|Id Software - Doom|Unknown|
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
|Quake|Unknown|
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
|Uzebox|Unknown|

## Building

To build the RDB files, run the following commands...

```
git clone https://github.com/libretro/libretro-super.git
cd libretro-super
./libretro-fetch.sh retroarch
./libretro-build-database.sh
```

You will find the updated RDB files over in the retroarch/media directory.
