# Libretro Database

The github repository for databases used by RetroArch.

## RetroArch's Usage of the Database

Libretro databases allow RetroArch to provide several automated cataloging functions:

- __Validation__. Reject or accept files when using the [Import Scanner / Playlist Generator](https://docs.libretro.com/guides/roms-playlists-thumbnails/#working-with-playlists) based on whether the ROM checksum matches the checksum of a known verified completely intact (aka  "properly dumped") file.
- __Game Naming__. Assign a definitive and uniform display name for each game in a playlist regardless of filename.
- __Thumbnail Images__. Download and display thumbnail images for games based on the uniform name assigned by the database, regardless of filename. (Thumbnails are __not__ directly assigned by the database or by checksum association, but as a secondary effect of databased *game name* assignment if a matching thumbnail is available on the server. Also see: [Flexible Name Matching Algorithm](https://docs.libretro.com/guides/roms-playlists-thumbnails/#custom-thumbnails).)
- __Category Search ("Explore")__. Allows the user to find/view games that match selected criteria, e.g. by Developer, Release Year, Genre, and other attributes/metadata.
- __Per-Game Information View__. Provide an in-app viewable informational screen for each game (Game > Information > Database Entry).

## Repository Contents

### File Types

- __Game information database files__.
  - __`.dat`__ files in the clrmamepro DAT format, from many [sources](#sources) and across many categories of metadata. The system of dats is multifaceted: alternative or additional sources can be easily added and maintained in a self-contained constituent, some dats may overlap in the games they cover (see [precedence](#precedence)), and some dats cover an exclusive niche of games or attributes.
  - __`.rdb`__ files used by RetroArch, compiled and amalgamated from the `.dat` files. [RetroArch Database format](https://github.com/libretro/RetroArch/blob/master/libretro-db/README.md) (_no relation to Redis .RDB files_) accommodates RetroArch's [wide range of hardware/OS platforms](https://www.retroarch.com/index.php?page=platforms).
- __`.cht` cheat code files__. These are game-specific, remain in plain text, and are used as-is by RetroArch if manually selected by the user (see [Cheat Code Documentation](https://docs.libretro.com/guides/cheat-codes/)). Cheat codes are collected from any available source on the web including by manual [contributions from users](https://github.com/libretro/libretro-database/pulls?q=is%3Apr+is%3Aclosed+cheats) who have used RetroArch's built-in [memory address/value search feature](https://docs.libretro.com/guides/cheat-codes/#retroarch-new-cheat-code-searching) to construct new cheat codes. The repository contains one folder for each system (unlike dats), and multiple different cheat files may exist for the same game.
- __Admin/management scripts__ and files.

### Folder Guide

The non-exhaustive list below serves as a guide to various folders in the repository.

- [`cht`](cht) Cheat codes.
- [`cursors`](cursors) Methods to query playlists.
- [`dat`](dat) Customized DAT files maintained by the libretro team, including:
  - Subset data coverage for games or variants that do/did not have contemporary documentation by upstream database groups, e.g. Virtual Console variants of SNES games, fan translations of NEC PC-98 games, and a superceded squib for PSP Minis.
  - Game data for monolithic non-generalized cores, e.g. Cave Story, Doom, Quake, etc.
  - Data adapted from upstream sources that cover a relatively small number of systems and can therefore can be housed together in a single repository folder without conflict, e.g. DOS, ScummVM, and GameTDB coverage of GameCube and Wii data.  (Though many dats from upstream groups reside in [`metadat`](metadat).)
- [`metadat`](metadat) Several principal third-party DATs (e.g. No-Intro, Redump, MAME, TOSEC) that each cover a large number of systems and therefore require their own folders in the repository, plus various collections of metadata (some of which may be deprecated). Examples:
  - [`bbfc`](metadat/bbfc) British Board of Film Classification's ratings for age-appropriateness.
  - [`elspa`](metadat/elspa) Age-appropriateness/content ratings from the Entertainment and Leisure Software Publishers Association aka the Association for UK Interactive Entertainment ("Ukie").
  - [`fbneo-split`](metadat/fbneo-split) Includes an XML database (sourced from Logiqx's DTD ROM Management) for special use in arcade ROM scanning: it must be manually selected by the user when running a Manual Scan, it defines the component files within each ROM archive, and is not part of the `.rdb` compile. Also contains a typical `.dat`.
  - [`mame`](metadat/mame) Similar to `fbneo-split` above.
  - [`hacks`](metadat/hacks) Data for modified (or "hacked") versions of commercially released games.  Many of these data are set by direct manual commits on the Libretro Github.
  - [`homebrew`](metadat/homebrew) Data for non-officially-published games created by independent creators/programmers.
  - [`libretro-dats`](metadat/libretro-dats) Ad hoc databases for items that were/are not covered by upstream database groups. Currently includes fan translations of SNES games, and an additional FDS dat that may be redundant with other sources.
  - [`no-intro`](metadat/no-intro) Bulk import from upstream No-Intro databases. Generally non-disc-based systems.
  - [`redump`](metadat/redump) Bulk import from upstream Redump databases. Generally disc-based systems.
  - [`tosec`](metadat/tosec) Bulk import from upstream TOSEC databases. TOSEC data overlaps with and goes beyond other data sets (No-Intro, Redump), but has lower [precedence](#precedence) in libretro and so generally serves as a secondary stopgap.
  - And more
- [`rdb`](rdb) The compiled RetroArch database files
- [`scripts`](scripts) Various scripts that are used to maintain the database files

## Fields & Headers

### Key Field
The key field for matching varies by console typical file size (i.e. original media type).

- __CRC checksum__ for systems with smaller file sizes, e.g. games before the advent of disc-based consoles.
- __Serial Number__ for larger files like disc-based games, to avoid computing checksums on large files. Found within the ROM file. The serial is not metadata but encoded within the game's binary data, which is scanned (in applicable cases) as a byte array by RetroArch.

CRC and serial also serve as RetroArch's primary index.

Current [build script code](https://github.com/libretro/libretro-super/blob/master/libretro-build-database.sh#L245) can be viewed as a reference for which type of key field RetroArch uses for each console system.

### Fields Specified in Game Information Databases

Database entries for games at minimum specify 1) a game's name, i.e. the display name that RetroArch will assign in playlists and 2) [key field](#key-field) data for matching/indexing and for identifying a file.  Further optional metadata may appear.  For reasons of informational completeness, future-proofing, and compatibility outside RetroArch, databases contain checksum and cryptographic hashes regardless of the key used for matching.

Example of database entry within [`metadat/no-intro/Atari - 2600.dat`](https://github.com/libretro/libretro-database/blob/master/metadat/no-intro/Atari%20-%202600.dat) for the European region version of _Asteroids_:
```
game (
	name "Asteroids (Europe)"
	description "Asteroids (Europe)"
	region "Europe"
	rom ( name "Asteroids (Europe).a26" size 8192 crc 0A2F8288 md5 8CF0D333BBE85B9549B1E6B1E2390B8D sha1 1CB8F057ACAD6DC65FEF07D3202088FF4AE355CD )
)
```
If other `Atari - 2600.dat` files exist in the repository and contain further metadata for the same crc, the data would be compiled together in the `.rdb`.  For example, [`metadat/developer/Atari - 2600.dat`](https://github.com/libretro/libretro-database/blob/master/metadat/developer/Atari%20-%202600.dat#L296) would confer `developer "Atari"` to the above data.

### Header Guidelines for DATs

__`description`__. The `description " "` and `comment " "` fields within a libretro dat's `clrmamepro ( )` header should be used to clarify the origin, source, and/or purpose of the data and file.  The description and comment header fields are __intended for documentation__ purposes, are ignored by RetroArch, and can be freely changed without issue.  For example, if a .dat includes 3rd party upstream data processed through a github author's build/scrape script(s), the comment and description (or other appropriate header fields) should contain information about _both_ those aspects of the dat's origin.  If the .dat file is meant to cover a particular niche of data, the description field should explain it.  

__`name`__. The `name` field (and filename) of a `.dat` file header should match the `database` field that is specified in the [.info file for the cores that use it](https://github.com/libretro/libretro-super/tree/master/dist/info) (often but not always `Manufacturer - Systemname` or similar).

## Precedence
Databases earlier in the list have precedence over items later in the list.  E.g. definitions in `/dat` will over-ride `/metadat` in the final `.rdb` compile if any info conflicts for the same game (i.e. for the same key field).

## Sources

Many source databases are in use as listed below.  The table focusses on the 3rd party sources that predominantly cover each specific console library, but other/multiple sources including manual github contributions are maintained and all are compiled together in the final `.rdb` files (see [Repository Folder Guide](#folder-guide) and each dat's github History for details). ">" signs below indicate the [precedence](#precedence) order when multiple sources overlap for the same subset of games/data.

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

__Pre-emptive Databases__. Some databases are maintained even if RetroArch currently has no core for the games/system, e.g. GP32, Vita, Original Xbox, and PS3.

## Maintenance / Technical Usage

### Building

To build a complete set of RDB files for RetroArch or to generate a single RDB file, see [RetroArch/libretro-db/README.md](https://github.com/libretro/RetroArch/blob/master/libretro-db/README.md).

Alternatively, you can run the following command to rebuild all the RDBs locally:

```
make build
```

### Testing

Make sure filenames are Windows file system compatible, and are not too long (eg. [ecryptfs limits filenames to 143 characters](https://unix.stackexchange.com/questions/32795/what-is-the-maximum-allowed-filename-and-folder-size-with-ecryptfs/32834#32834))...

```
find -exec basename '{}' ';' | egrep '^.{144,}$'
```

## Contributions

### Small-Scale Corrections

A vast majority of the database's game information originates from routine imports from upstream data groups (No-Intro, Redump, TOSEC, GameTDB, etc). In cases where the `.dat` for the entry at issue originates from an upstream group, best practice is for a contributor to go through the channels/process of that group. Upstream changes made by the database groups will eventually be imported to the Libretro databases. A seemingly helpful "fix" to Libretro's copy of the database would be overwritten and lost by the next import from upstream. 

In cases where the `.dat` in question is created and maintained by Libretro or does not receive bulk over-writes, github contributions are accepted.  Refer to the [repository folder guide](#folder-guide) above and to github Histories for information about which libretro databases are applicable for github contributions.

### Folder Structure Revisions

The [build script](https://github.com/libretro/libretro-super/blob/master/libretro-build-database.sh) specifies exact `.dat` files and folders in the repository, therefore organizational housekeeping revisions to the file/folder structure (e.g. combining two metadata fragments into one unified folder and file) require corresponding revisions in the build script.

### Adding A New Database

- Create new `metadata/nameofnewdatabasefolder` and appropriately named system `.dat` file(s) e.g. `Sony - PlayStation.dat` with new data
- Add the new entry to `libretro-build-database.sh`
- Run ``make build`` to build the RDB files
- New types for RetroArch's `Explore` tab require updates to RetroArch code.

## Databases and RetroArch Thumbnails

Currently there is no automatic correspondence between game name updates in databases and image filename updates in the thumbnail repository, so database updates may break thumbnail retrieval.  See the [Thumbnail Repository Readme](https://github.com/libretro-thumbnails/libretro-thumbnails#libretro-thumbnails) and [How to Contribute to Thumbnails Guide](https://docs.libretro.com/guides/roms-playlists-thumbnails/#contributing-thumbnails-how-to) for documentation about thumbnail handling.

## Integrations

There are a few tools out there that allow integration with libretro's database.

- [RetroArch CleanNaming](https://github.com/sirsquall/retroarch_cleannaming): Python script that will rename your roms
