# Libretro Database

The github repository for databases used by RetroArch. The repository contains several different kinds of files:

- __Game information database files__.
  - __`.dat`__ constituent files from many [sources](#sources) and across many categories of metadata. Alternative additional sources can be easily added and maintained in a self-contained constituent. Some `.dat` files may overlap partly or completely in the games they cover (see [precedence](#precedence)), while some `.dat` files cover an exclusive niche of games.
  - __`.rdb`__ files used by RetroArch, compiled and amalgmated from the `.dat` files. [RetroArch Database format](https://github.com/libretro/RetroArch/tree/68b3e5d8e02aff753e01a1f6f8969891910b2e0b/libretro-db#readme) (_no relation to Redis .RDB files_) accomodates RetroArch's [wide range of hardware/OS compatibility](https://www.retroarch.com/index.php?page=platforms).
- __Cheat code `.cht` files__. These are game-specific, remain in plain text, and are used as-is by RetroArch. The repository contains one unitary folder for each system, unlike the multifaceted storage of dat files.
- __Admin/management scripts__ and files.

### RetroArch's Usage of the Database

Libretro databases allow RetroArch to provide several automated catalogging functions:

- __Validation__. Reject or accept files when using the [Import Scanner / Playlist Generator](https://docs.libretro.com/guides/roms-playlists-thumbnails/#working-with-playlists) based on whether the ROM checksum matches the checksum of a known verified completely intact (aka  "properly dumped") file.
- __Game Naming__. Assign a definitive and uniform display name for each game in a playlist regardless of filename.
- __Thumbnail Images__. Download and display thumbnail images for games based on the uniform name assigned by the database, regardless of filename. (Note: thumbnails are not directly assigned by the database or by checksum association, but as a secondary effect of databased *game name* assignment if a matching thumbnail is available on the server. Also see: [Flexible Name Matching Algorithm](https://docs.libretro.com/guides/roms-playlists-thumbnails/#custom-thumbnails))
- __Category Search__. A reference search (named "Explore") that allows the user to search for games by category criteria, e.g. by Developer, Release Year, Genre, and other attributes/metadata.
- __Per-Game Information View__. Provide an in-app viewable informational screen for each game (Game > Information > Database Entry)

### Key Field
The key field for matching generally varies by console typical file size (i.e. media type).

- __CRC checksum__ for systems with smaller file sizes, i.e. game media before the advent of disc-based games.
- __Serial Number__ found within the ROM file, for larger files like disc-based games, to avoid computing checksums on large files. The serial is not metadata but encoded within the game's binary data, which is scanned (in applicable cases) as a byte array by RetroArch.

CRC and serial also serve as RetroArch's primary index.

Current [build script code](https://github.com/libretro/libretro-super/blob/master/libretro-build-database.sh#L288) can be viewed as a reference for which type of key field RetroArch uses for each console system.

### Precedence
Databases earlier in the list have precedence over items later in the list.  E.g. definitions in `dat` will over-ride `metadat` in the final `.rdb` compile if any info conflicts for the same item (i.e. for the same key field).

### Fields Specified in Game Information Databases

Database entries generally at minimum specify 1) a game's name, i.e. the display name that RetroArch will assign in playlists and 2) [key field](#key-field) data for matching.  Further metadata for each game is often sourced from multiple databases.  Databases often contain checksum/hashes for informational completeness even in cases where the [key field](#key-field) for matching is the game's internal serial number rather than checksum.

Example of database entry within [`metadat/no-intro/Atari - 2600.dat`](https://github.com/libretro/libretro-database/blob/master/metadat/no-intro/Atari%20-%202600.dat) for the European region version of _Asteroids_:
```
game (
	name "Asteroids (Europe)"
	description "Asteroids (Europe)"
	region "Europe"
	rom ( name "Asteroids (Europe).a26" size 8192 crc 0A2F8288 md5 8CF0D333BBE85B9549B1E6B1E2390B8D sha1 1CB8F057ACAD6DC65FEF07D3202088FF4AE355CD )
)
```

## Repository Contents

The non-exhaustive list below serves as a guide to various folders/files in the repository.

- [`cht`](cht) Cheat codes to various games, collected from any available source on the web including by manual contributions from users who haved used RetroArch's built-in [memory address/value search feature](https://docs.libretro.com/guides/cheat-codes/#retroarch-new-cheat-code-searching) to construct new cheat codes.
- [`cursors`](cursors) Methods to query playlists.
- [`dat`](dat) Mostly customized DAT files maintained by the libretro team, including items that do/did not have contemporary documentation by upstream database groups (e.g. "Virtual Console" variants of SNES games), and games for monolithic non-generalized cores (Cave Story, Doom, Quake, etc). Also includes some imports from upstream groups in order to establish [precedence](#precedence) in the compilation, e.g. GameCube data from GameTDB, although most dats from upstream groups reside in [`metadat`](metadat).
- [`metadat`](metadat) Several principal third-party DATs (e.g. No-Intro, Redump, and TOSEC), plus various collections of metadata (Note: some may be deprecated or incomplete). Examples:
  - [`bbfc`](metadat/bbfc) British Board of Film Classification's ratings for age-appropriateness.
  - [`elspa`](metadat/elspa) Age-appropriateness/content ratings from the Entertainment and Leisure Software Publishers Association aka the Association for UK Interactive Entertainment ("Ukie").
  - [`hacks`](metadat/hacks) Data for modified (or "hacked") versions of commercially released games.  Many of these data are set by direct manual commits on the Libretro Github.
  - [`homebrew`](metadat/homebrew) Data for non-officially-published games created by independent creators/programmers.
  - [`libretro-dats`](metadat/libretro-dats) Ad hoc databases for items that were/are not covered by upstream database groups. Currently includes fan translations of SNES games, and an additional FDS dat that mostly overlaps with other sources/dats and may be redundant.
  - [`no-intro`](metadat/no-intro) Bulk import from upstream No-Intro databases. Generally non-disc-based systems.
  - [`redump`](metadat/redump) Bulk import from upstream Redump databases. Generally disc-based systems.
  - [`tosec`](metadat/tosec) Bulk import from upstream TOSEC databases.
  - And more
- [`rdb`](rdb) The compiled RetroArch database files
- [`scripts`](scripts) Various scripts that are used to maintain the database files

#### Pre-emptive Databases

Some databases are maintained even if RetroArch currently has no core for the games/system, e.g. GP32, Vita, Original Xbox, and PS3.

## Sources

Many source databases are in use as listed below.  The table focusses on the 3rd party sources that predominantly cover each specific console library, but other/multiple sources including manual github contributions are maintained and all are compiled together in the final `.rdb` files (see [Repository Contents](#repository-contents) and github History for each dat for details). ">" signs below indicate the [precedence](#precedence) order when multiple sources overlap for the same subset of games/data.

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
### Other

**Folder structure revisions.** The [build script](https://github.com/libretro/libretro-super/blob/master/libretro-build-database.sh) specifies exact `.dat` files and folders in the repository, therefore organizational revisions to the file/folder structure should have corresponding revisions in the build script.

__Adding New Database: Example__
- Creat new `metadata/nameofnewdatabasefolder` and appropriately named `.dat` files e.g. `Sony - PlayStation.dat`
- Add the new entry to `libretro-build-database.sh`
- Run ``make build`` to build the RDB files
- New types for RetroArch's `Explore` tab will need some updates to RetroArch.


# Contributions

A vast majority of the database's game information originates from routine imports from upstream data groups (No-Intro, Redump, TOSEC, GameTDB, etc). General best practice for corrections or additions is for a contributor to go through the channels/process of the relevant upstream group. Upstream changes made by the database groups will eventually be imported to the Libretro databases. A "fix" to Libretro's copy of the database would be overwritten and lost with the next import from upstream. 

In cases where the `.dat` in question is created and maintained by Libretro or does not receive bulk over-writes, github contributions are accepted.  Refer to the [repository contents list](#repository-contents) above and to github Histories for information about which libretro databases are applicable for github contributions.

# Databases and RetroArch Thumbnails

Currently there is no automatic process for updating libretro [thumbnail repository](https://github.com/libretro-thumbnails/libretro-thumbnails#libretro-thumbnails) image filenames based on game name updates in databases.  Databases assign a game name (aka playlist item name or displayed game title) based on a game file's checksum, but thumbnails are only assigned if the thumbnail server image filename matches the game name or the ROM filename (with some [flexibility](https://docs.libretro.com/guides/roms-playlists-thumbnails/#custom-thumbnails)). To help fix a thumbnail, for example in a case where a database game name has been definitively/correctly updated in a way that no longer matches the repository thumbnail name, follow the [Thumbnail Repository readme](https://docs.libretro.com/guides/roms-playlists-thumbnails/#contributing-thumbnails-how-to) and [How-To documentation](https://docs.libretro.com/guides/roms-playlists-thumbnails/#contributing-thumbnails-how-to).

# Integrations

There are a few tools out there that allow integration with libretro's database.

- [RetroArch CleanNaming](https://github.com/sirsquall/retroarch_cleannaming): Python script that will rename your roms
