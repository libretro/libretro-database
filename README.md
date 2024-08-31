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
|Commodore - Amiga|[WHDLoad](http://whdload.de/) > [No-Intro](http://datomatic.no-intro.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Commodore - CD32|[Redump](http://redump.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Commodore - CDTV|[Redump](http://redump.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
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
|Id Software - Doom|Unknown| |
|Id Software - Quake|Unknown| |
|Id Software - Quake II|Unknown| |
|Id Software - Quake III|Unknown| |
|Lutro|Unknown|
|MAME|MAME 0.37b5, 0.78, 0.139, 0.159|
|Magnavox - Odyssey2|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Mattel - Intellivision|[No-Intro](http://datomatic.no-intro.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)
|Microsoft - MSX|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Microsoft - MSX 2|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Microsoft - Xbox|[Redump](http://redump.org) (Note: there is no libretro emulator)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|MicroW8| |
|MrBoom| |
|NEC - PC-8001 - PC-8801.rdb|[TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|NEC - PC-98|[Redump](http://redump.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|NEC - PC Engine - TurboGrafx 16|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|NEC - PC Engine SuperGrafx|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|NEC - PC Engine CD - TurboGrafx-CD|[Redump](http://redump.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|NEC - PC-FX|[Redump](http://redump.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - e-Reader|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Family Computer Disk System|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Game Boy|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Game Boy Advance|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Game Boy Color|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - GameCube|[GameTDB](http://www.gametdb.com/) > [Redump](http://redump.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-database-gametdb](https://github.com/RobLoach/libretro-database-gametdb) [libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Nintendo 3DS|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Nintendo 64|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Nintendo 64 DD|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Nintendo DS|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Nintendo DSi|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Nintendo Entertainment System|[No-Intro](http://datomatic.no-intro.org) (iNES 1.0 headered, NES 2.0 headered, headerless)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Pokemon Mini|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Satellaview|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Sufami Turbo|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Super Nintendo Entertainment System|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Virtual Boy|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Wii|[GameTDB](http://www.gametdb.com/) > [Redump](http://redump.org)|[libretro-database-gametdb](https://github.com/RobLoach/libretro-database-gametdb) [libretro-dats](https://github.com/robloach/libretro-dats)|
|Nintendo - Wii (Digital)|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Philips - CD-i|[Redump](http://redump.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Phillips - Videopac+|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|PuzzleScript| |
|RCA - Studio II|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Rick Dangerous| |
|RPG Maker| |
|ScummVM|Gruby's ScummVM Adventure Pack|[libretro-database-scummvm](https://github.com/RobLoach/libretro-database-scummvm)|
|Sega - 32X|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - Dreamcast|[Redump](http://redump.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - Game Gear|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - Master System - Mark III|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - Mega CD - Sega CD|[Redump](http://redump.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - Mega Drive - Genesis|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - Naomi|[Redump](http://redump.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - Naomi 2|[Redump](http://redump.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - PICO|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - Saturn|[Redump](http://redump.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sega - SG-1000|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sharp - X1|[No-Intro](http://datomatic.no-intro.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sharp - X68000|[No-Intro](http://datomatic.no-intro.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sinclair - ZX 81|[TOSEC](https://www.tosecdev.org/)| |
|Sinclair - ZX Spectrum|[World of Spectrum](https://www.worldofspectrum.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sinclair - ZX Spectrum +3|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|SNK - Neo Geo CD|[Redump](http://redump.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|SNK - Neo Geo Pocket|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|SNK - Neo Geo Pocket Color|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sony - PlayStation|[Redump](http://redump.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sony - PlayStation 2|[Redump](http://redump.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sony - PlayStation 3|[GameTDB](http://www.gametdb.com/) > [Redump](http://redump.org) (Note: there is no libretro emulator)|[libretro-database-gametdb](https://github.com/RobLoach/libretro-database-gametdb) [libretro-dats](https://github.com/robloach/libretro-dats)|
|Sony - PlayStation 3 (PSN)|[No-Intro](http://datomatic.no-intro.org) (Note: there is no libretro emulator)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sony - PlayStation Portable|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sony - PlayStation Portable (PSN)|[No-Intro](http://datomatic.no-intro.org) > [Redump](http://redump.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Sony - PlayStation Vita|[No-Intro](http://datomatic.no-intro.org) (Note: there is no libretro emulator)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Spectravideo - SVI-318 - SVI-328|[TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|The 3DO Company - 3DO|[Redump](http://redump.org) > [TOSEC](https://www.tosecdev.org/)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Thomson - MO/TO|[TOSEC](https://www.tosecdev.org/)| |
|TIC-80|[tic80.com](https://tic80.com/play)|[libretro-database-tic80](https://github.com/robloach/libretro-database-tic80)|
|Tiger - Game.com|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Tomb Raider| |
|Uzebox|Unknown|
|Vircon32| |
|VTech - CreatiVision|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|VTech - V.Smile|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|WASM-4| |[libretro-database-wasm4](https://github.com/robloach/libretro-database-wasm-4)
|Watara - Supervision|[No-Intro](http://datomatic.no-intro.org)|[libretro-dats](https://github.com/robloach/libretro-dats)|
|Wolfenstein 3D| |

## Building

To build a complete set of RDB files for RetroArch or to generate a single RDB file, see [RetroArch/libretro-db/README.md](https://github.com/libretro/RetroArch/blob/master/libretro-db/README.md).

Alternatively, you can run the following command to rebuild all the RDBs locally:

```
make build
```

## Testing

Make sure filenames are Windows file system compatible, and are not too long...

```
find -exec basename '{}' ';' | egrep '^.{150,}$'
```

## Integrations

There are a few tools out there that allow integration with libretro's database.

- [RetroArch CleanNaming](https://github.com/sirsquall/retroarch_cleannaming): Python script that will rename your roms
