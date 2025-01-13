# Libretro Database

The github repository for databases used by RetroArch.

## Overview
RetroArch relies on databases to provide several catalogging functions:

- __Validation__. Reject or accept files when using the [Import Scanner / Playlist Generator](https://docs.libretro.com/guides/roms-playlists-thumbnails/#working-with-playlists) based on whether the ROM checksum matches the checksum of a known verified completely intact (aka  "properly dumped") file.
- __Game Naming__. Assign a definitive and uniform display name for each game file regardless of filename.
- __Thumbnail Images__. Download and display thumbnail images for each game based on the uniform name assigned by the database, regardless of filename
- __Category Search__. A reference search (named "Explore") that allows the user to search for games by category criteria, e.g. by Developer, Release Year, Genre, and other attributes/metadata.
- __Per-Game Information__. Provide an in-app viewable informational screen for each game (Game > Information > Database Entry)

#### Key Field
The key field for matching varies by file size, i.e. by console media type.

- __CRC checksum__ for systems with smaller file sizes, i.e. game media before the advent of disc-based games.
- __Serial Number__ within the ROM file for larger files like disc-based systems. [Edit: How does this work? It searches the binary data? Is it a certain sector to look for?  This is NOT metadata?]

Current program code publicly viewable [LINK] shows which type of key field RetroArch uses for each console system.

#### Game Data in Repository
Database entries at minimum contain fields for 1) a game's name, i.e. the display name that RetroArch will assign and 2) checksum/hash for identifying a particular file.  Ideally the entries include further metadata such as a description (to disambiguate variants that may justifiably receive the same game name as another variant), 


## Repository Contents

The repository contains many constituent databases that are compiled into `.rdb` files used by RetroArch. _(Note: several items described below are not compiled into RetroArch's game database files, e.g. Cheats, but are described here because they reside within the github database repository.)_ [EDIT: NOTE, separate into "Game Information Databases", ??"Functional/Maintenance", "Other"]??

- [`cht`](cht) Cheat codes to various games, collected from any available source on the web including by manual contributions by users who haved used RetroArch's built-in [memory address/value search feature](https://docs.libretro.com/guides/cheat-codes/#retroarch-new-cheat-code-searching) to construct new cheat codes. 
- [`cursors`](cursors) Provides methods in order to query the playlists
- [`dat`](dat) Customized DAT files maintained by the libretro team, including items that do/did not have contemporary documentation by upstream catalogging groups, e.g. "Virtual Console" variants of SNES games. Also includes some imports from upstream in order to establish precedence in the compilation, e.g. GameCube data from GameTDB.
    - SNES Virtual Console Variants 
- [`metadat`](metadat) Various metadata and third-party DATs. Examples:
  - [`no-intro`](metadat/no-intro) Bulk import from upstream No-Intro databases. Generally non-disc-based systems.
  - [`redump`](metadat/redump) Bulk import from upstream Redump databases. Generally disc-based systems.
  - [`hacks`](metadat/hacks) Data for modified (or "hacked") versions of commercially released games.  These data are set by direct manual commits on the Libretro Github.
  - [`homebrew`](metadat/homebrew) Data for non-officially-published games created by independent creators/programmers
  - [`libretro-dats`](metadat/libretro-dats) E.g. [EDIT: maybe "ad hoc databases for items not covered by upstream bla bla] Fan translations of SNES games, and [NOTE] FDS? Why FDS, check if covered elsewhere
  - And more
- [`rdb`](rdb) The compiled RetroArch database files
- [`scripts`](scripts) Various scripts that are used to maintain the database files

#### Precedence
Databases earlier in the list have precedence over items later in the list.  Definitions in `dat` will over-ride `metadat` in the final `.rdb` compile if any info conflicts for the same item.

#### Pre-emptive Databases

Some databases are maintained even if RetroArch currently has no core for the games/system, e.g. GP32, Vita, Original Xbox, and PS3.

## Sources

Many source databases are in use, as listed below.  A large majority of games commonly used in RetroArch are covered by [No-Intro](http://datomatic.no-intro.org) or [Redump](http://redump.org/downloads/) DAT files. ">" signs below mean that the multiple listed sources are compiled with the given [precedence](#precedence).

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

# Maintenance / Technical Usage

## Building

To build a complete set of RDB files for RetroArch or to generate a single RDB file, see [RetroArch/libretro-db/README.md](https://github.com/libretro/RetroArch/blob/master/libretro-db/README.md).

Alternatively, you can run the following command to rebuild all the RDBs locally:

```
make build
```

## Testing

Make sure filenames are Windows file system compatible, and are not too long (eg. [ecryptfs limits filenames to 143 characters](https://unix.stackexchange.com/questions/32795/what-is-the-maximum-allowed-filename-and-folder-size-with-ecryptfs/32834#32834))...

```
find -exec basename '{}' ';' | egrep '^.{144,}$'
```

## Integrations

There are a few tools out there that allow integration with libretro's database.

- [RetroArch CleanNaming](https://github.com/sirsquall/retroarch_cleannaming): Python script that will rename your roms
