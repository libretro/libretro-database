#!/usr/bin/env python3

"""
Matches this repo's DAT files to IGDB and Hasheous,
and derives metadata for RetroArch's `.rdb` databases from them.

- `index` joins all three sources into one SQLite database.
- `generate` writes one DAT file per playlist to `lookatalldat/`,
  holding whatever the index can add to the entries that RetroArch's databases already have.
  libretro-super's `libretro-build-database.sh` compiles it after every other DAT file.

DAT entries are only ever matched by the identifiers that RetroArch itself uses,
i.e. by CRC32 or by serial; never by name.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time

from collections import Counter, defaultdict
from collections.abc import Callable, Collection, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from functools import cache, partial
from itertools import chain
from pathlib import Path
from typing import Annotated, Any, NamedTuple

import pe
import pycountry

from aiomultiprocess.types import ProxyException

from pydantic import AliasChoices, BaseModel, DirectoryPath, Field, FilePath
from pydantic_settings import BaseSettings, CliSubCommand, SettingsConfigDict, CliApp
from sqlalchemy import CheckConstraint, ForeignKey, MetaData, Column, Row, Select, String, Index, column, select, text, true, type_coerce
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine
from sqlalchemy.sql.functions import coalesce, count
from titlecase import titlecase

from dats import DAT_OBJECT_TYPES, ClrMamePro, CompiledEntry, DatTable, ParsedDatFile, compile_dats_async, encode_dat, get_dat_match, index_dats, write_dat_key_index, Game as DatGame, PlaylistGameMapping as DatPlaylistGameMapping, Rom as DatRom
from igdb import (
    IGDB_OBJECT_TYPES,
    DumpIdType,
    IgdbConfig,
    Playlist,
    PlaylistConfig,
    RegionConfig,
    index_igdb,
    AgeRating as IgdbAgeRating,
    AgeRatingCategory as IgdbAgeRatingCategory,
    AgeRatingOrganization as IgdbAgeRatingOrganization,
    Company as IgdbCompany,
    Franchise as IgdbFranchise,
    Game as IgdbGame,
    Genre as IgdbGenre,
    InvolvedCompany as IgdbInvolvedCompany,
    Keyword as IgdbKeyword,
    Language as IgdbLanguage,
    LanguageSupport as IgdbLanguageSupport,
    MultiplayerMode as IgdbMultiplayerMode,
    Platform as IgdbPlatform,
    PlayerPerspective as IgdbPlayerPerspective,
    PlaylistMapping as IgdbPlaylistMapping,
    ReleaseDate as IgdbReleaseDate,
)
from hasheous import HASHEOUS_OBJECT_TYPES, index_hasheous, GameDataObject as HasheousGameDataObject, GameDumpMapping as HasheousGameDumpMapping, RomItem as HasheousRomItem
from utils import CliTuple, DEFAULT_DAT_CONCURRENCY, DEFAULT_HASHEOUS_CONCURRENCY, DEFAULT_IGDB_CONCURRENCY, IndexArgs, PlaylistArgs, PoolArgs, RowId, Sha256, VerboseArgs, build_metadata, create_db, create_deferred_indexes, DatabaseModel, Crc, Md5, Sha1, db_transaction

class AllRoms(DatabaseModel, frozen=True):
    __tablename__ = "AllRoms"
    __tableargs__ = (
        CheckConstraint("dat_rom IS NOT NULL OR hasheous_rom IS NOT NULL", name="dat_or_hasheous_rom_not_null"),
        Index("ix_AllRoms", "dat_rom", "hasheous_rom", "crc", "serial", "md5", "sha1", unique=True),
        Index("ix_AllRoms_dat_rom_where_not_null", "dat_rom", unique=True, sqlite_where=column("dat_rom").is_not(None)),
        # Not unique: several DAT ROMs may share a serial and so match the same Hasheous ROM.
        Index("ix_AllRoms_hasheous_rom_where_not_null", "hasheous_rom", sqlite_where=column("hasheous_rom").is_not(None)),
        Index("ix_AllRoms_dat_rom_crc_where_not_null", "dat_rom", "crc", unique=True, sqlite_where=column("crc").is_not(None) & column("dat_rom").is_not(None)),
        Index("ix_AllRoms_hasheous_crc_where_not_null", "hasheous_rom", "crc", unique=True, sqlite_where=column("crc").is_not(None) & column("hasheous_rom").is_not(None)),
        Index("ix_AllRoms_serial_where_not_null", "serial", sqlite_where=column("serial").is_not(None)),
        Index("ix_AllRoms_dat_rom_md5_where_not_null", "dat_rom", "md5", unique=True, sqlite_where=column("md5").is_not(None) & column("dat_rom").is_not(None)),
        Index("ix_AllRoms_hasheous_rom_md5_where_not_null", "hasheous_rom", "md5", unique=True, sqlite_where=column("md5").is_not(None) & column("hasheous_rom").is_not(None)),
        Index("ix_AllRoms_dat_rom_sha1_where_not_null", "dat_rom", "sha1", unique=True, sqlite_where=column("sha1").is_not(None) & column("dat_rom").is_not(None)),
        Index("ix_AllRoms_hasheous_rom_sha1_where_not_null", "hasheous_rom", "sha1", unique=True, sqlite_where=column("sha1").is_not(None) & column("hasheous_rom").is_not(None)),
        # None of the DAT files have SHA256 hashes, so we don't need a column or index for that,
        # but having the SHA256 from a Hasheous object can help us with matching
        Index("ix_AllRoms_hasheous_rom_sha256_where_not_null", "hasheous_rom", "sha256", unique=True, sqlite_where=column("sha256").is_not(None) & column("hasheous_rom").is_not(None)),
    )

    # These columns are deliberately not unique on their own.
    # Hasheous lists the same hash under several ROM entries
    # (see RomItem's class docstring), and some of those hashes are junk
    # (over a thousand rows carry the SHA-256 of an empty file),
    # so the uniqueness that this table actually relies on
    # is declared as the partial composite indexes in __tableargs__ above.
    dat_rom: Annotated[RowId | None, Column(ForeignKey("DatRom.rowid"), nullable=True, index=True)] = None
    hasheous_rom: Annotated[int | None, Column(ForeignKey("HasheousRomItem.id"), nullable=True, index=True)] = None
    crc: Annotated[Crc | None, Column(String, nullable=True, index=True)] = None
    serial: Annotated[str | None, Column(String, nullable=True, index=True)] = None
    md5: Annotated[Md5 | None, Column(String, nullable=True, index=True)] = None
    sha1: Annotated[Sha1 | None, Column(String, nullable=True, index=True)] = None
    sha256: Annotated[Sha256 | None, Column(String, nullable=True, index=True)] = None

PARENT_DIR = Path(__file__).parent.parent
class CommonArgs:
    igdb_path: DirectoryPath = Field(
        default=PARENT_DIR / 'tmp' / 'igdb',
        description="Path to the directory containing IGDB JSON files fetched with `igdb.py fetch`.",
        validation_alias=AliasChoices('i', 'igdb'),
        validate_default=True,
    )

    hasheous_path: DirectoryPath = Field(
        default=PARENT_DIR / 'tmp' / 'hasheous',
        description="Path to the directory containing Hasheous ZIP dumps fetched with `hasheous.py fetch`.",
        validation_alias=AliasChoices('s', 'hasheous'),
        validate_default=True,
    )

    dat_dirs: CliTuple[DirectoryPath] = Field(
        default=(PARENT_DIR / 'dat', PARENT_DIR / 'metadat',),
        description="Paths to the directories containing existing DAT files to scan for games to process.",
        validation_alias=AliasChoices('d', 'dat'),
        validate_default=True,
    )

OUTDIR_NAME = "lookatalldat"

BUILD_DAT_DIRS: tuple[str, ...] = (
    "metadat",
    "metadat/goodtools",
    "metadat/analog",
    "metadat/barcode",
    "metadat/bbfc",
    "metadat/developer",
    "metadat/elspa",
    "metadat/esrb",
    "metadat/franchise",
    "metadat/magazine/famitsu",
    "metadat/magazine/edge",
    "metadat/magazine/edge_review",
    "metadat/maxusers",
    "metadat/origin",
    "metadat/publisher",
    "metadat/releasemonth",
    "metadat/releaseyear",
    "metadat/genre",
    "metadat/rumble",
    "metadat/serial",
    "metadat/enhancement_hw",
    "metadat/tgdb",
    "metadat/headered",
    "metadat/hacks",
    "metadat/homebrew",
    "metadat/mame-nonmerged",
    "metadat/mame-split",
    "metadat/mame-member",
    "metadat/mame",
    "metadat/fbneo-merged",
    "metadat/fbneo-split",
    "metadat/fbneo-member",
    "metadat/tosec",
    "metadat/libretro-dats",
    "metadat/redump",
    "metadat/no-intro",
    "dat",
)
"""
The directories that libretro-super's `libretro-build-database.sh` looks in for `<rdb name>.dat`,
relative to the root of this repo.
See https://github.com/libretro/libretro-super/blob/master/libretro-build-database.sh

Listed in the order the script passes them to `c_converter`,
which is also their precedence from lowest to highest:
when two files describe the same entry, the later one wins.
The script reads `lookatalldat` last of all, so it isn't listed here.
"""


def rdb_source_dats(root: Path, title: str) -> tuple[Path, ...]:
    """
    Returns the DAT files that `libretro-build-database.sh` compiles into `<title>.rdb`
    (not counting the one that `generate` writes), in the order it compiles them.
    """
    return tuple(
        path
        for directory in BUILD_DAT_DIRS
        if (path := root / directory / f"{title}.dat").is_file()
    )


def match_key(playlist: Playlist) -> str:
    """
    The field that `c_converter` identifies a playlist's `.rdb` entries by.

    This has to agree with the match key that `libretro-build-database.sh` gives the playlist,
    as it does for every playlist in `playlists.toml` that the script builds.
    """
    return f"rom.{playlist.id_type}"


RDB_FIELDS: tuple[str, ...] = (
    "developer",
    "publisher",
    "genre",
    "franchise",
    "perspective",
    "releaseyear",
    "releasemonth",
    "users",
    "coop",
    "rumble",
    "analog",
    "origin",
    "esrb_rating",
    "pegi_rating",
    "cero_rating",
    "platform_exclusive",
    "console_exclusive",
    "achievements",
    "tags",
    "language",
    "region",
)
"""
The fields that generated DAT files may contain besides each entry's name and key,
in the order they're written.

Each one is compiled by `c_converter` (see `rdb_mappings` in `libretro-db/c_converter.c`)
and read back by RetroArch (see `database_info.c` and `menu/menu_explore.c`).
Only `tags` needs a `c_converter` newer than upstream's, which ignores it.

Deliberately left out:

- `bbfc_rating`: RetroArch reads it, but `c_converter` never writes it.
- `elspa_rating`: ELSPA stopped rating games in 2003, and IGDB doesn't track it.
- `description`, `score`, `category`, `media`, `controls`, `artstyle`,
  `gameplay`, `narrative`, `pacing`, `setting`, `visual`, `vehicular`:
  none of our sources has a field that means the same thing.
"""

MULTI_VALUE_SEPARATOR = " / "
"""
Joins multiple values in one field.

Matches the convention of the existing DAT files (e.g. `developer "Capcom / Arika"`),
and `menu_explore.c` splits on it.
"""

TAG_SEPARATORS = re.compile(r"[/,|]")
"""
The characters that `menu_explore.c` splits multi-valued fields on.

A few IGDB keywords contain them (e.g. "day/night cycle"),
which would turn into tags that don't exist.
"""

TRANSLATION_TAG = re.compile(r"[(\[]T[-+]|\[tr\b")
"""
Marks a fan translation in No-Intro (e.g. "(T-En by ...)"), GoodTools (e.g. "[T+Eng]") or TOSEC (e.g. "[tr fr]") names.

A translation isn't in the languages of the game it translates.
"""

WORLDWIDE = 8

PRECISE_MONTH_FORMATS = frozenset((0, 1))
"""IGDB date formats `YYYYMMDD` and `YYYYMM`; the others don't pin down a month."""

SINGLE_PLAYER_MODE = 1
COOP_MODE = 3

CONSOLE_PLATFORM_TYPES = frozenset((1, 5))
"""IGDB's platform types for consoles and portable consoles."""


def playlist_igdb_platforms(playlist: Playlist) -> frozenset[int] | None:
    """
    Returns the IGDB platforms that a playlist's query selects games by,
    or None if it selects them some other way (e.g. by engine or ID).
    """
    where = playlist.igdb_query.where or ""
    match = re.search(r"\bplatforms\s*=\s*\(([\d,\s]+)\)", where)
    if not match:
        return None

    return frozenset(int(p) for p in match[1].split(",") if p.strip())


def language_name(name: str | None) -> str | None:
    """
    Returns a language's name without its regional variant (e.g. IGDB's "Spanish (Mexico)"),
    or None if it's a code or a combination rather than a name (e.g. Hasheous's "Pt-BR" or "Multi-5").
    """
    if not name:
        return None

    name = re.sub(r"\s*\([^()]*\)$", "", name)
    return name if len(name) > 2 and re.fullmatch(r"[A-Z][a-z]+(?: [A-Z][a-z]+)*", name) else None


def country_region(code: str | None, name: str | None, regions_by_code: Mapping[str, str], aliases: Mapping[str, str]) -> str | None:
    """
    Spells one of Hasheous's countries the way the DAT files spell regions,
    or returns None if it isn't a country at all (e.g. "Unset", or a bare code like "ss").

    :param regions_by_code: See `HasheousConfig.regions_by_country_code`.
    :param aliases: See `RegionConfig.aliases`.
    """
    if code and (region := regions_by_code.get(code)):
        return region

    if name and name != "Unset" and re.fullmatch(r"[A-Z][A-Za-z]*(?: [A-Za-z]+)*", name):
        return aliases.get(name, name)

    return None


def hasheous_game_region(value: str, regions_by_code: Mapping[str, str], aliases: Mapping[str, str]) -> str | None:
    """Parses one of the countries that Hasheous lists for a whole game, e.g. "Japan (JP)"."""
    if match := re.fullmatch(r"(.*?)\s*\(([^()]*)\)", value):
        return country_region(match[2], match[1], regions_by_code, aliases)

    return country_region(None, value, regions_by_code, aliases)


def json_object(value: str | None) -> dict[str, Any]:
    """Parses a JSON object, or returns an empty one if `value` is anything else."""
    parsed = json.loads(value) if value else None
    return parsed if isinstance(parsed, dict) else {}


def explore_key(value: str) -> bytes:
    """
    Returns what RetroArch's Explore menu identifies a value by
    (see `ex_hash32_nocase_filtered` in `menu/menu_explore.c`):
    its bytes without spaces or punctuation below `'0'`, with ASCII letters lowercased.

    Explore lists values with the same key as one,
    under whichever spelling it read first.
    """
    return bytes(b | 0x20 if 0x41 <= b <= 0x5A else b for b in value.encode("utf-8", "surrogateescape") if b >= 0x30)


class Spellings:
    """
    The spellings that the existing DAT files use for one field's values,
    so that a value from IGDB can be written the way they already spell it.

    Where the DATs disagree, the spelling used by the most playlists' DATs wins;
    a tie goes to the one used by more entries.
    """

    def __init__(self, uses: Iterable[tuple[str, str, int]]) -> None:
        """
        :param uses: How many entries of which playlist's DATs use each value, as `(value, playlist, entries)`.
          A value that lists several (e.g. "Capcom / Arika") counts for itself and for each of them.
        """
        playlists: dict[str, set[str]] = defaultdict(set)
        entries: Counter[str] = Counter()
        for value, playlist, n in uses:
            for spelling in {value, *(part.strip() for part in TAG_SEPARATORS.split(value))}:
                playlists[spelling].add(playlist)
                entries[spelling] += n

        self._by_key: dict[bytes, str] = {}
        for spelling in sorted(playlists, key=lambda s: (-len(playlists[s]), -entries[s], s)):
            if key := explore_key(spelling):
                self._by_key.setdefault(key, spelling)

    def respell(self, value: str) -> str:
        """Returns how the DATs spell `value` (see `explore_key`), or `value` if they don't use it."""
        return self._by_key.get(explore_key(value), value)


SPELLING_FIELDS: Mapping[str, tuple[str, ...]] = {
    "company": ("developer", "publisher"),
    "genre": ("genre",),
    "franchise": ("franchise",),
    "tags": ("tags",),
}
"""
The DAT fields whose spellings values from IGDB adopt, grouped by what they name.
Developers and publishers are both companies (as `menu_explore.c` also treats them).
"""


def tag_case(keyword: str, spellings: Sequence[tuple[re.Pattern[str], str]], uppercase: Sequence[re.Pattern[str]]) -> str:
    """
    Title-cases an IGDB keyword (which IGDB writes in lowercase) into a tag.

    Each part of a hyphenated word is title-cased as if it were a title of its own
    (e.g. "Fake In-Game Advertising", "Built-In", "GBA-to-GC").

    :param spellings: See `IgdbConfig.tag_spellings`.
    :param uppercase: See `IgdbConfig.tag_uppercase`.
    """
    def spell(word: str, **_: Any) -> str | None:
        # e.g. "(ww2)" or "lgbtq+"
        prefix, core, suffix = re.fullmatch(r"(\W*)(.*?)(\W*)", word).groups()
        for pattern, template in spellings:
            if match := pattern.fullmatch(core):
                return prefix + match.expand(template) + suffix

        if any(pattern.fullmatch(core) for pattern in uppercase):
            return prefix + core.upper() + suffix

        if "-" in core:
            # titlecase would lowercase the small words of a compound even at its start (e.g. "in-Game")
            return prefix + titlecase(core.replace("-", " "), callback=spell).replace(" ", "-") + suffix

        return None

    return titlecase(keyword, callback=spell)


@dataclass(frozen=True, slots=True)
class ReleaseDate:
    platform: int
    region: int
    year: int
    month: int | None
    format: int


@dataclass(frozen=True, slots=True)
class MultiplayerMode:
    platform: int | None
    max_players: int | None
    coop: bool


@dataclass(slots=True)
class IgdbInfo:
    name: str
    franchise: str | None = None
    franchises: list[str] = field(default_factory=list)
    developers: list[str] = field(default_factory=list)
    developer_countries: set[int | None] = field(default_factory=set)
    """ISO 3166-1 numeric codes."""

    publishers: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    perspectives: list[str] = field(default_factory=list)
    platforms: set[int] = field(default_factory=set)
    game_modes: set[int] = field(default_factory=set)
    keywords: set[int] = field(default_factory=set)
    languages: list[str] = field(default_factory=list)
    releases: list[ReleaseDate] = field(default_factory=list)
    multiplayer: list[MultiplayerMode] = field(default_factory=list)
    age_ratings: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))


class HasheousLink(NamedTuple):
    """One Hasheous game that lists a ROM, as recorded in the `AllRoms` table."""

    game: int
    igdb: int | None
    retroachievements: int | None
    dump: str

    countries: tuple[str, ...]
    """The regions that Hasheous says this very ROM was released in, most prominent first."""

    languages: tuple[str, ...]
    """The languages that Hasheous says this very ROM is in."""


@dataclass
class Catalog:
    """Everything that the generated DAT files are derived from, loaded into memory."""

    igdb: dict[int, IgdbInfo]
    igdb_playlists: dict[str, frozenset[int]]
    links_by_crc: dict[str, list[HasheousLink]]
    links_by_serial: dict[str, list[HasheousLink]]

    tags: dict[int, str]
    """The tag that each IGDB keyword becomes, if any."""

    platform_types: dict[int, int | None]
    """Each IGDB platform's type (see `CONSOLE_PLATFORM_TYPES`)."""

    igdb_config: IgdbConfig
    """How to interpret IGDB's data. `tags` and `platform_types` already reflect its overrides."""

    region_config: RegionConfig
    """How to read and spell the regions that DAT files name."""

    hasheous_countries: dict[int, frozenset[str]]
    """The regions that Hasheous lists for each of its games, across all of the game's ROMs."""

    hasheous_languages: dict[int, frozenset[str]]
    """The languages that Hasheous lists for each of its games, across all of the game's ROMs."""

    @classmethod
    async def load(cls, connection: AsyncConnection, metadata: MetaData, config: PlaylistConfig) -> Catalog:
        """
        :param metadata: The tables that the `index` subcommand wrote to the database that `connection` reads.
        """
        index = IndexReader(connection, metadata)
        regions_by_code, aliases = config.hasheous.regions_by_country_code, config.regions.aliases
        links_by_crc, links_by_serial = await index.hasheous_links(regions_by_code, aliases)
        spellings = await index.dat_spellings()

        return cls(
            igdb=await index.igdb_games(spellings, config.igdb.genre_overrides),
            igdb_playlists=await index.igdb_playlists(),
            links_by_crc=links_by_crc,
            links_by_serial=links_by_serial,
            tags=await index.igdb_tags(config.igdb, spellings["tags"]),
            platform_types=await index.igdb_platform_types(config.igdb.platform_type_overrides),
            igdb_config=config.igdb,
            region_config=config.regions,
            hasheous_countries=await index.hasheous_values("country", partial(hasheous_game_region, regions_by_code=regions_by_code, aliases=aliases)),
            hasheous_languages=await index.hasheous_values("language", language_name),
        )


def grouped[K, V](pairs: Iterable[tuple[K, V] | Row[tuple[K, V]]]) -> dict[K, frozenset[V]]:
    """Groups the second item of each pair by the first."""
    groups: dict[K, set[V]] = defaultdict(set)
    for key, value in pairs:
        groups[key].add(value)

    return {key: frozenset(values) for key, values in groups.items()}


@dataclass(frozen=True)
class IndexReader:
    """Reads what a `Catalog` holds from the database that the `index` subcommand writes."""

    connection: AsyncConnection
    metadata: MetaData

    async def dat_spellings(self) -> dict[str, Spellings]:
        """Loads how the existing DAT files spell the values of each group of `SPELLING_FIELDS`."""
        game, mapping = DatGame.table(self.metadata), DatPlaylistGameMapping.table(self.metadata)

        async def uses(field: str) -> Sequence[Row]:
            value = game.c[field]
            return await self._rows(
                select(value, mapping.c.playlist, count())
                .join(mapping, mapping.c.game == game.c.rowid)
                .where(value.is_not(None))
                .group_by(value, mapping.c.playlist)
            )

        return {
            group: Spellings(chain.from_iterable([await uses(f) for f in fields]))
            for group, fields in SPELLING_FIELDS.items()
        }

    async def igdb_games(self, spellings: Mapping[str, Spellings], genre_overrides: Mapping[int, str]) -> dict[int, IgdbInfo]:
        """
        Loads what the generated DAT files use of each IGDB game, keyed by its ID.

        :param spellings: How the DAT files spell each group of `SPELLING_FIELDS`, which the games' names adopt.
        :param genre_overrides: See `IgdbConfig.genre_overrides`.
        """
        game, franchise = IgdbGame.table(self.metadata), IgdbFranchise.table(self.metadata)
        query = select(game.c.id, game.c.name, franchise.c.name).outerjoin(franchise, franchise.c.id == game.c.franchise)
        games = {
            id: IgdbInfo(name=name, franchise=spellings["franchise"].respell(franchise_name) if franchise_name else None)
            for id, name, franchise_name in await self._rows(query)
        }

        await self._add_igdb_relations(games, spellings, genre_overrides)
        await self._add_igdb_languages(games)
        await self._add_igdb_companies(games, spellings["company"])
        await self._add_igdb_releases(games)
        await self._add_igdb_multiplayer_modes(games)
        await self._add_igdb_age_ratings(games)
        return games

    async def igdb_playlists(self) -> dict[str, frozenset[int]]:
        """Loads the IGDB games that each playlist's query selects."""
        mapping = IgdbPlaylistMapping.table(self.metadata)
        return grouped(await self._rows(select(mapping.c.title, mapping.c.game)))

    async def igdb_tags(self, config: IgdbConfig, spellings: Spellings) -> dict[int, str]:
        """
        Loads the tag that each IGDB keyword becomes, if any.

        :param config: Its `keyword_overrides`, `tag_spellings`, and `tag_uppercase` apply.
        :param spellings: How the DAT files spell tags, which the tags adopt.
        """
        keyword = IgdbKeyword.table(self.metadata)
        names = {id: name for id, name in await self._rows(select(keyword.c.id, keyword.c.name))}
        tag_spellings = [(re.compile(pattern, re.IGNORECASE), template) for pattern, template in config.tag_spellings.items()]
        tag_uppercase = [re.compile(pattern, re.IGNORECASE) for pattern in config.tag_uppercase]

        tags: dict[int, str] = {}
        for id, name in names.items():
            tag = tag_case(names.get(config.keyword_overrides.get(id, id), name), tag_spellings, tag_uppercase)
            if not TAG_SEPARATORS.search(tag):
                tags[id] = spellings.respell(tag)

        return tags

    async def igdb_platform_types(self, overrides: Mapping[int, int]) -> dict[int, int | None]:
        """
        Loads each IGDB platform's type.

        :param overrides: See `IgdbConfig.platform_type_overrides`.
        """
        platform = IgdbPlatform.table(self.metadata)
        types = {id: type for id, type in await self._rows(select(platform.c.id, platform.c.platform_type))}
        return {**types, **overrides}

    async def hasheous_links(self, regions_by_code: Mapping[str, str], aliases: Mapping[str, str]) -> tuple[dict[str, list[HasheousLink]], dict[str, list[HasheousLink]]]:
        """
        Loads the Hasheous games that list each ROM in `AllRoms`,
        keyed by the ROM's CRC32 (in lowercase) and by its serial (in uppercase).

        :param regions_by_code: See `HasheousConfig.regions_by_country_code`.
        :param aliases: See `RegionConfig.aliases`.
        """
        # Most ROMs share their countries and languages with many others,
        # so each distinct JSON value is only parsed once
        @cache
        def countries(value: str | None) -> tuple[str, ...]:
            regions = (country_region(code, name, regions_by_code, aliases) for code, name in json_object(value).items())
            return tuple(dict.fromkeys(filter(None, regions)))

        @cache
        def languages(value: str | None) -> tuple[str, ...]:
            return tuple(dict.fromkeys(filter(None, map(language_name, json_object(value).values()))))

        by_crc: dict[str, list[HasheousLink]] = defaultdict(list)
        by_serial: dict[str, list[HasheousLink]] = defaultdict(list)

        for crc, serial, game, igdb, retroachievements, dump, rom_countries, rom_languages in await self._rows(self._hasheous_links_query()):
            link = HasheousLink(game, igdb, retroachievements, dump, countries(rom_countries), languages(rom_languages))
            if crc:
                by_crc[crc.lower()].append(link)
            if serial:
                by_serial[serial.upper()].append(link)

        return dict(by_crc), dict(by_serial)

    async def hasheous_values(self, field: str, parse: Callable[[str], str | None]) -> dict[int, frozenset[str]]:
        """
        Loads what one of the multi-valued fields of each Hasheous game lists, across all of the game's ROMs.

        :param parse: Returns the value to keep for each listed one, or None to leave it out.
        """
        rows = await self._rows(select(*HasheousGameDataObject.relationship_columns(self.metadata, field)))
        return grouped((game, parsed) for game, value in rows if (parsed := parse(value)))

    async def _add_igdb_relations(self, games: Mapping[int, IgdbInfo], spellings: Mapping[str, Spellings], genre_overrides: Mapping[int, str]) -> None:
        """
        :param spellings: See `igdb_games`.
        :param genre_overrides: See `IgdbConfig.genre_overrides`.
        """
        for info, _, name in await self._igdb_related_names(games, "franchises", IgdbFranchise, order_by="id"):
            if (name := spellings["franchise"].respell(name)) not in info.franchises:
                info.franchises.append(name)

        for info, id, name in await self._igdb_related_names(games, "genres", IgdbGenre, order_by="name"):
            if (name := spellings["genre"].respell(genre_overrides.get(id, name))) not in info.genres:
                info.genres.append(name)

        for info, _, name in await self._igdb_related_names(games, "player_perspectives", IgdbPlayerPerspective, order_by="id"):
            info.perspectives.append(name)

        for info, platform in await self._igdb_related_ids(games, "platforms"):
            info.platforms.add(platform)

        for info, mode in await self._igdb_related_ids(games, "game_modes"):
            info.game_modes.add(mode)

        for info, keyword in await self._igdb_related_ids(games, "keywords"):
            info.keywords.add(keyword)

    async def _add_igdb_languages(self, games: Mapping[int, IgdbInfo]) -> None:
        game, support_id = IgdbGame.relationship_columns(self.metadata, "language_supports")
        support, language = IgdbLanguageSupport.table(self.metadata), IgdbLanguage.table(self.metadata)
        query = (
            select(game, language.c.name)
            .join(support, support.c.id == support_id)
            .join(language, language.c.id == support.c.language)
            .order_by(language.c.id)
        )

        for info, name in await self._rows_by_game(games, query):
            # Whether a language is supported in audio, subtitles, or the interface makes no difference here
            if (name := language_name(name)) and name not in info.languages:
                info.languages.append(name)

    async def _add_igdb_companies(self, games: Mapping[int, IgdbInfo], spellings: Spellings) -> None:
        """:param spellings: How the DAT files spell companies, which the companies' names adopt."""
        involved, company = IgdbInvolvedCompany.table(self.metadata), IgdbCompany.table(self.metadata)
        query = (
            select(involved.c.game, company.c.name, company.c.country, involved.c.developer, involved.c.publisher)
            .join(company, company.c.id == involved.c.company)
            .order_by(involved.c.id)
        )

        for info, name, country, developer, publisher in await self._rows_by_game(games, query):
            name = spellings.respell(name)
            if developer and name not in info.developers:
                info.developers.append(name)
                info.developer_countries.add(country)
            if publisher and name not in info.publishers:
                info.publishers.append(name)

    async def _add_igdb_releases(self, games: Mapping[int, IgdbInfo]) -> None:
        release = IgdbReleaseDate.table(self.metadata)
        query = (
            select(release.c.game, release.c.platform, release.c.release_region, release.c.y, release.c.m, release.c.date_format)
            .where(release.c.y.is_not(None))
        )

        for info, platform, region, year, month, format in await self._rows_by_game(games, query):
            info.releases.append(ReleaseDate(platform, region, year, month, format))

    async def _add_igdb_multiplayer_modes(self, games: Mapping[int, IgdbInfo]) -> None:
        mode = IgdbMultiplayerMode.table(self.metadata)
        query = select(mode.c.game, mode.c.platform, mode.c.offlinemax, mode.c.offlinecoopmax, mode.c.offlinecoop)

        for info, platform, offlinemax, offlinecoopmax, offlinecoop in await self._rows_by_game(games, query):
            max_players = max((n for n in (offlinemax, offlinecoopmax) if n), default=None)
            info.multiplayer.append(MultiplayerMode(platform, max_players, bool(offlinecoop)))

    async def _add_igdb_age_ratings(self, games: Mapping[int, IgdbInfo]) -> None:
        game, rating_id = IgdbGame.relationship_columns(self.metadata, "age_ratings")
        age_rating, organization, category = (
            IgdbAgeRating.table(self.metadata),
            IgdbAgeRatingOrganization.table(self.metadata),
            IgdbAgeRatingCategory.table(self.metadata),
        )
        query = (
            select(game, organization.c.name, category.c.rating)
            .join(age_rating, age_rating.c.id == rating_id)
            .join(organization, organization.c.id == age_rating.c.organization)
            .join(category, category.c.id == age_rating.c.rating_category)
        )

        for info, board, rating in await self._rows_by_game(games, query):
            info.age_ratings[board].add(rating)

    async def _igdb_related_names(self, games: Mapping[int, IgdbInfo], field: str, related: type[DatabaseModel], order_by: str) -> Iterator[Any]:
        """Loads the IDs and names of the objects that one of each IGDB game's fields refers to, ordered by `related`'s `order_by` column."""
        game, related_id = IgdbGame.relationship_columns(self.metadata, field)
        table = related.table(self.metadata)
        query = select(game, table.c.id, table.c.name).join(table, table.c.id == related_id).order_by(table.c[order_by])
        return await self._rows_by_game(games, query)

    async def _igdb_related_ids(self, games: Mapping[int, IgdbInfo], field: str) -> Iterator[Any]:
        """Loads the IDs of the objects that one of each IGDB game's fields refers to."""
        return await self._rows_by_game(games, select(*IgdbGame.relationship_columns(self.metadata, field)))

    async def _rows_by_game(self, games: Mapping[int, IgdbInfo], query: Select) -> Iterator[Any]:
        """
        Runs a query whose first column is an IGDB game's ID,
        replacing it with that game's `IgdbInfo` and skipping the rows of unknown games.
        """
        rows = await self._rows(query)
        # Lazily, since collecting hundreds of thousands of new tuples at once keeps the garbage collector busy
        return ((games[id], *values) for id, *values in rows if id in games)

    def _hasheous_links_query(self) -> Select:
        all_roms, rom = AllRoms.table(self.metadata), HasheousRomItem.table(self.metadata)
        game, dump = HasheousGameDataObject.table(self.metadata), HasheousGameDumpMapping.table(self.metadata)
        game_id, rom_id = HasheousGameDataObject.relationship_columns(self.metadata, "roms")

        return (
            select(
                all_roms.c.crc,
                all_roms.c.serial,
                game.c.id,
                game.c.igdb_id,
                game.c.retroachievements_id,
                dump.c.dump,
                # Read as text, so that `hasheous_links` can parse each distinct value just once
                type_coerce(rom.c.country, String),
                type_coerce(rom.c.language, String),
            )
            .join_from(all_roms, rom, rom.c.id == all_roms.c.hasheous_rom)
            .join(rom_id.table, rom_id == all_roms.c.hasheous_rom)
            .join(game, game.c.id == game_id)
            .join(dump, dump.c.game == game.c.id)
            .where(all_roms.c.hasheous_rom.is_not(None))
        )

    async def _rows(self, query: Select) -> Sequence[Row]:
        return (await self.connection.execute(query)).all()


type FieldValue = str | int | bool
"""The value of one of `RDB_FIELDS`, before it's written to a DAT file."""


class Derivation(NamedTuple):
    fields: dict[str, FieldValue]
    """
    Every field our sources could fill in for an entry, whether or not the entry already has it,
    in the order of `RDB_FIELDS`.
    """

    igdb: int | None
    """The IGDB game the entry was matched to, if any."""

    hasheous_games: frozenset[int]
    """The Hasheous games whose ROMs the entry was matched to."""

    ambiguous: bool
    """Whether the entry's ROMs pointed to several IGDB games equally, so none was chosen."""

    @property
    def sources(self) -> dict[str, Any]:
        """
        The IDs of the games that `fields` were derived from, as extra DAT fields for debugging.
        `c_converter` leaves fields it doesn't know out of the `.rdb`.
        """
        return {"igdb_id": self.igdb, "hasheous_id": tuple(sorted(self.hasheous_games))}


def entry_label(entry: CompiledEntry) -> dict[str, str]:
    """
    Returns the field that names an entry, if any.

    Some DATs name their games with `comment` instead of `name` (e.g. `metadat/origin`).
    `c_converter` leaves `comment` out of the `.rdb`, so an entry named only by one has no name there.
    """
    for key in ("name", "comment"):
        if isinstance(value := entry.game.get(key), str):
            return {key: value}

    return {}


def entry_name(entry: CompiledEntry) -> str | None:
    """Returns an entry's name, or its comment if it has no name (see `entry_label`)."""
    return next(iter(entry_label(entry).values()), None)


def name_regions(entry: CompiledEntry, known: Collection[str]) -> tuple[str, ...]:
    """
    Returns the regions in `known` that the first parenthesized tag of an entry's name to list any lists,
    like No-Intro's "(USA, Europe)", MAME's "(Japan, set 2)", or the second tag of "Tiny Troops (CD) (Europe)".
    """
    for tag in re.findall(r"\(([^()]*)\)", entry_name(entry) or ""):
        if regions := tuple(r for part in tag.split(",") if (r := part.strip()) in known):
            return regions

    return ()


def entry_regions(entry: CompiledEntry, igdb_regions: Mapping[str, tuple[int, ...]]) -> tuple[str, ...]:
    """
    Returns the regions an entry was released in,
    from its `region` field or else from its name,
    as far as they can be mapped to IGDB's release regions.

    :param igdb_regions: See `RegionConfig.igdb`.
    """
    region = entry.game.get("region")
    if isinstance(region, str) and region:
        return tuple(r.strip() for r in re.split(r"[,/|]", region) if r.strip())

    return name_regions(entry, igdb_regions)


def dump_regions(entry: CompiledEntry, named: tuple[str, ...], derived: str | None, aliases: Mapping[str, str]) -> tuple[str, ...]:
    """
    Returns the regions that an entry's dump is from, as far as they're known:
    the entry's own `region` field, else the regions its name lists, else the region derived for it.

    :param aliases: See `RegionConfig.aliases`.
    """
    if isinstance(existing := entry.game.get("region"), str) and existing:
        return (aliases.get(existing, existing),)

    return named or ((derived,) if derived else ())


def igdb_release_regions(regions: Iterable[str], igdb_regions: Mapping[str, tuple[int, ...]]) -> frozenset[int]:
    """
    Returns the IGDB release regions that DAT regions map to.

    :param igdb_regions: See `RegionConfig.igdb`.
    """
    return frozenset(r for region in regions for r in igdb_regions.get(region, ()))


def developer_origin(countries: Collection[int | None], overrides: Mapping[int, str]) -> str | None:
    """
    Returns the country that all of a game's developers are from,
    spelled the way the existing `metadat/origin` DATs spell it.

    :param countries: ISO 3166-1 numeric codes.
    :param overrides: See `IgdbConfig.origin_overrides`.
    """
    if len(countries) != 1 or (code := next(iter(countries))) is None:
        return None

    if origin := overrides.get(code):
        return origin

    country = pycountry.countries.get(numeric=f"{code:03}")
    return (getattr(country, "common_name", None) or country.name) if country else None


def company_fields(info: IgdbInfo, origin_overrides: Mapping[int, str]) -> dict[str, FieldValue]:
    """:param origin_overrides: See `IgdbConfig.origin_overrides`."""
    fields: dict[str, FieldValue] = {}
    if info.developers:
        fields["developer"] = MULTI_VALUE_SEPARATOR.join(info.developers)

    if origin := developer_origin(info.developer_countries, origin_overrides):
        fields["origin"] = origin

    if info.publishers:
        fields["publisher"] = MULTI_VALUE_SEPARATOR.join(info.publishers)

    return fields


def classification_fields(info: IgdbInfo) -> dict[str, FieldValue]:
    fields: dict[str, FieldValue] = {}
    if info.genres:
        fields["genre"] = MULTI_VALUE_SEPARATOR.join(info.genres)

    if info.franchise:
        fields["franchise"] = info.franchise
    elif len(info.franchises) == 1:
        fields["franchise"] = info.franchises[0]

    if info.perspectives:
        fields["perspective"] = MULTI_VALUE_SEPARATOR.join(info.perspectives)

    return fields


def agreed_languages(claims: Iterable[Sequence[str]]) -> Sequence[str] | None:
    """
    Returns the languages that a source gives for an entry, or None if its records disagree.

    :param claims: The languages that each of the source's records gives for the entry.
      A source that only says the entry is in one of several languages
      (e.g. a game whose regional releases are in different languages)
      should give each language as a claim of its own.
    """
    claims = [c for c in claims if c]
    return claims[0] if claims and len({frozenset(c) for c in claims}) == 1 else None


def agreed_region(claims: Iterable[Sequence[str]], named: Sequence[str]) -> str | None:
    """
    Returns the region that a source says an entry is primarily from, or None if its records disagree.

    :param claims: The regions that each of the source's records gives for the entry,
      most prominent first (e.g. `("USA", "Europe")` for No-Intro's "(USA, Europe)").
      A source that only says the entry is from one of several regions
      (e.g. a game released in several) should give each region as a claim of its own.
    :param named: The regions that the entry's own name lists, if any.
      If there are some, the first of them that any claim includes is returned instead,
      which is how the existing DAT files fill in their `region` fields.
    """
    claims = [c for c in claims if c]
    if not claims:
        return None

    if named:
        return next((r for r in named if any(r in c for c in claims)), None)

    firsts = {c[0] for c in claims}
    return firsts.pop() if len(firsts) == 1 else None


class Deriver:
    """Derives `.rdb` fields for the entries of one playlist."""

    def __init__(self, catalog: Catalog, playlist: Playlist) -> None:
        self.catalog = catalog
        self.regions = catalog.region_config
        self.playlist = playlist
        self.dumps = frozenset(playlist.hasheous_dirs)
        self.igdb_games = catalog.igdb_playlists.get(playlist.title, frozenset())
        self.platforms = playlist_igdb_platforms(playlist)
        self.by_serial = playlist.id_type == "serial"

    def derive(self, entry: CompiledEntry) -> Derivation:
        links_per_rom = [self._links(rom) for rom in self._roms(entry)]
        links = list(chain.from_iterable(links_per_rom))
        chosen, ambiguous = self._choose_igdb(links_per_rom)
        info = self.catalog.igdb[chosen] if chosen is not None else None
        fields = self._igdb_fields(info, entry) if info else {}

        if any(link.retroachievements is not None for link in links):
            fields["achievements"] = True

        named = tuple(self.regions.aliases.get(r, r) for r in name_regions(entry, self.regions.all))
        if region := self._region(links, info, named):
            fields["region"] = region

        if language := self._language(entry, links, info, dump_regions(entry, named, region, self.regions.aliases)):
            fields["language"] = language

        return Derivation(
            {f: fields[f] for f in RDB_FIELDS if f in fields},
            chosen,
            frozenset(link.game for link in links),
            ambiguous,
        )

    def _roms(self, entry: CompiledEntry) -> list[DatTable]:
        """
        Returns an entry's ROM records.

        On platforms identified by serial,
        a serial that a DAT only gives for the whole game counts as a ROM of its own.
        """
        roms = [rom for rom in entry.roms or (entry.game.get("rom"),) if isinstance(rom, Mapping)]
        serial = entry.game.get("serial")
        if self.by_serial and isinstance(serial, str) and not any(rom.get("serial") for rom in roms):
            roms.append({"serial": serial})

        return roms

    def _links(self, rom: Mapping[str, Any]) -> list[HasheousLink]:
        """
        Finds the Hasheous games listing a ROM by the identifiers RetroArch itself uses:
        its CRC32, or failing that (on platforms identified by serial) its serial.
        """
        crc, serial = rom.get("crc"), rom.get("serial")
        links = self.catalog.links_by_crc.get(crc.lower()) if isinstance(crc, str) else None
        if not links and self.by_serial and isinstance(serial, str):
            # A serial identifies a game, not a dump, so it's the last resort
            links = self.catalog.links_by_serial.get(serial.upper())

        return [link for link in links or () if link.dump in self.dumps]

    def _choose_igdb(self, links_per_rom: Iterable[Iterable[HasheousLink]]) -> tuple[int | None, bool]:
        """
        Returns the IGDB game that most of an entry's ROMs are linked to, if any,
        and whether several games tied for that.

        Each ROM gets one vote per IGDB game, however many Hasheous entries repeat it.
        A tie chooses nothing: Hasheous sometimes lists one ROM under several games
        that are mapped to different IGDB entries (e.g. SimCity and SimCity 2000),
        and the identifiers alone can't say which is right.
        """
        votes = Counter(
            igdb
            for links in links_per_rom
            for igdb in {link.igdb for link in links if link.igdb in self.igdb_games}
        )
        most = max(votes.values(), default=0)
        tied = [igdb for igdb, n in votes.items() if n == most]
        return (tied[0], False) if len(tied) == 1 else (None, len(tied) > 1)

    def _on_platform(self, platform: int | None) -> bool:
        return self.platforms is None or platform is None or platform in self.platforms

    def _igdb_fields(self, info: IgdbInfo, entry: CompiledEntry) -> dict[str, FieldValue]:
        regions = entry_regions(entry, self.regions.igdb)
        return {
            **company_fields(info, self.catalog.igdb_config.origin_overrides),
            **classification_fields(info),
            **self._keyword_fields(info),
            **self._release_fields(info, regions),
            **self._player_fields(info),
            **self._rating_fields(info, regions),
            **self._exclusivity_fields(info),
        }

    def _keyword_fields(self, info: IgdbInfo) -> dict[str, FieldValue]:
        fields: dict[str, FieldValue] = {}
        if info.keywords & self.catalog.igdb_config.rumble_keywords:
            fields["rumble"] = True

        if info.keywords & self.catalog.igdb_config.analog_keywords:
            fields["analog"] = True

        if tags := sorted({tag for keyword in info.keywords if (tag := self.catalog.tags.get(keyword))}):
            fields["tags"] = MULTI_VALUE_SEPARATOR.join(tags)

        return fields

    def _release_fields(self, info: IgdbInfo, regions: Sequence[str]) -> dict[str, FieldValue]:
        """:param regions: The regions the entry is from (see `entry_regions`)."""
        releases = [r for r in info.releases if self._on_platform(r.platform)]
        if not releases:
            return {}

        wanted = igdb_release_regions(regions, self.regions.igdb)
        matching = [r for r in releases if r.region in wanted] or [r for r in releases if r.region == WORLDWIDE]
        if not matching:
            if regions:
                # The game came out in a region IGDB has no date for;
                # another region's date could be years off.
                return {}
            matching = releases

        earliest = min(matching, key=lambda r: (r.year, r.month or 13))
        fields: dict[str, FieldValue] = {"releaseyear": earliest.year}
        if earliest.month and earliest.format in PRECISE_MONTH_FORMATS:
            fields["releasemonth"] = earliest.month

        return fields

    def _player_fields(self, info: IgdbInfo) -> dict[str, FieldValue]:
        modes = [m for m in info.multiplayer if self._on_platform(m.platform)]
        fields: dict[str, FieldValue] = {}

        if players := max((m.max_players for m in modes if m.max_players), default=None):
            fields["users"] = max(players, 1)
        elif info.game_modes == {SINGLE_PLAYER_MODE}:
            fields["users"] = 1

        if any(m.coop for m in modes) or (not modes and COOP_MODE in info.game_modes and self.platforms is not None):
            fields["coop"] = True

        return fields

    def _rating_fields(self, info: IgdbInfo, regions: Sequence[str]) -> dict[str, FieldValue]:
        """:param regions: The regions the entry is from (see `entry_regions`)."""
        fields: dict[str, FieldValue] = {}
        wanted = igdb_release_regions(regions, self.regions.igdb)

        igdb_config = self.catalog.igdb_config
        for organization, board in igdb_config.rating_boards.items():
            ratings = info.age_ratings.get(organization, set()) - igdb_config.ignored_age_ratings
            if len(ratings) != 1:
                continue

            if wanted and not (wanted & board.regions):
                # e.g. an ESRB rating on a Japan-only ROM
                continue

            releases = [r for r in info.releases if self._on_platform(r.platform) and r.region in board.regions]
            if releases and min(r.year for r in releases) >= board.founded:
                fields[board.field] = next(iter(ratings))

        return fields

    def _exclusivity_fields(self, info: IgdbInfo) -> dict[str, FieldValue]:
        fields: dict[str, FieldValue] = {}
        if self.platforms and info.platforms:
            fields["platform_exclusive"] = info.platforms <= self.platforms

        platform_types = {self.catalog.platform_types.get(p) for p in info.platforms}
        if platform_types and None not in platform_types:
            fields["console_exclusive"] = platform_types <= CONSOLE_PLATFORM_TYPES

        return fields

    def _language(self, entry: CompiledEntry, links: Sequence[HasheousLink], info: IgdbInfo | None, regions: Sequence[str]) -> str | None:
        """
        Returns the languages of an entry's dump.

        Hasheous knows them for some ROMs (from No-Intro's language tags).
        Otherwise, the languages that Hasheous or IGDB list for the whole game
        only say which ones a particular dump is in if there's just one,
        since a game's regional releases are usually in different languages,
        and only if it's a language of the regions the dump is from (see `RegionConfig.languages`).

        :param regions: The regions the entry is from, if known.
        """
        if languages := agreed_languages(link.languages for link in links):
            return MULTI_VALUE_SEPARATOR.join(languages)

        if TRANSLATION_TAG.search(entry_name(entry) or ""):
            return None

        region_languages = self.regions.languages
        expected = frozenset().union(*(region_languages[r] for r in regions)) if all(r in region_languages for r in regions) else frozenset()
        sources: tuple[Iterable[Sequence[str]], ...] = (
            ((language,) for game in {l.game for l in links} for language in self.catalog.hasheous_languages.get(game, ())),
            ((language,) for language in (info.languages if info else ())),
        )

        for claims in sources:
            if (languages := agreed_languages(claims)) and (not expected or expected.issuperset(languages)):
                return MULTI_VALUE_SEPARATOR.join(languages)

        return None

    def _region(self, links: Sequence[HasheousLink], info: IgdbInfo | None, named: Sequence[str]) -> str | None:
        """
        Returns the one region that an entry's dump was released in.

        Hasheous knows it for most ROMs (from No-Intro's region tags).
        Otherwise, the regions that Hasheous or IGDB list for the whole game
        only say which one a particular dump is from if there's just one.

        :param named: The regions that the entry's own name lists, if any.
          The first one that a source agrees with is used,
          which is how the existing DAT files fill in their `region` fields.
        """
        release_regions = self.catalog.igdb_config.release_regions
        igdb_regions = {
            release_regions[r.region]
            for r in (info.releases if info else ())
            if self._on_platform(r.platform) and r.region in release_regions
        }

        sources: tuple[Iterable[Sequence[str]], ...] = (
            (link.countries for link in links),
            ((region,) for game in {l.game for l in links} for region in self.catalog.hasheous_countries.get(game, ())),
            ((region,) for region in igdb_regions),
        )

        for claims in sources:
            if region := agreed_region(claims, named):
                return region

        return None


def missing_fields(entry: CompiledEntry, fields: Mapping[str, FieldValue]) -> dict[str, FieldValue]:
    """
    Returns the fields that an entry doesn't already have.

    The existing DAT files are curated,
    so anything they already say about a game takes precedence over what we derive.
    """
    missing = {k: v for k, v in fields.items() if k not in entry.game}

    existing_year = entry.game.get("releaseyear")
    if "releasemonth" in missing and existing_year is not None and existing_year != str(fields.get("releaseyear")):
        # A month from some other year's release would make for a wrong date
        del missing["releasemonth"]

    return missing


def dat_header(playlist: Playlist) -> ClrMamePro:
    """Returns the header of the DAT file that `generate` writes for `playlist`."""
    return ClrMamePro.model_validate({
        "name": playlist.title,
        "description": f"{playlist.title} (IGDB and Hasheous metadata)",
        "comment": (
            "Generated by scripts/match.py from IGDB, Hasheous, and this repo's DAT files. "
            "Only lists fields that no other DAT file provides; compile it after all of them."
        ),
        "homepage": "https://github.com/libretro/libretro-database",
    })


def key_rom(id_type: DumpIdType, key: str) -> DatRom:
    """
    Returns a `rom` record that identifies an entry by its key.

    It's deliberately left unvalidated, which would lowercase a CRC:
    `c_converter` matches keys case-sensitively, exactly as the other DAT files spell them.
    """
    return DatRom.model_construct(serial=key) if id_type == "serial" else DatRom.model_construct(crc=key)


class GenerateSubCommand(BaseModel, PlaylistArgs, PoolArgs, VerboseArgs):
    """
    Generate one DAT file per playlist that fills in the gaps of RetroArch's databases
    with data from IGDB and Hasheous.

    Each generated DAT only lists entries that the playlist's `.rdb` already has
    (as compiled from this repo's DAT files by libretro-super's `libretro-build-database.sh`),
    keyed exactly as they are there,
    and only the fields that none of the existing DAT files provide.
    Compiling it last therefore adds fields to existing entries
    without adding, removing, reordering, or changing anything else.
    """

    input: FilePath = Field(
        default=PARENT_DIR / 'tmp' / 'index.db',
        description="Path to the input SQLite database file, as generated by the `index` subcommand.",
        validation_alias=AliasChoices('i', 'input'),
        validate_default=True,
    )

    outdir: Path = Field(
        default=PARENT_DIR / OUTDIR_NAME,
        description="Path to the output directory where generated DAT files will be written.",
        validation_alias=AliasChoices('o', 'outdir'),
        validate_default=True,
    )

    _log = logging.getLogger('match.generate')

    async def cli_cmd(self) -> None:
        start = time.perf_counter()
        show_logs(self._log.name, verbose=self.verbose)

        config = PlaylistConfig.load(self.config)
        playlists = config.playlists_titled(self.playlists)
        self.outdir.mkdir(parents=True, exist_ok=True)

        db = create_async_engine(f"sqlite+aiosqlite:///file:{self.input.as_posix()}?mode=ro&uri=true")

        self._log.info("Loading IGDB and Hasheous data from %s", self.input)
        async with db.connect() as connection:
            catalog = await Catalog.load(connection, build_metadata(MODEL_TYPES), config)
        await db.dispose()

        # Parsing the existing DAT files is the slow part, so it's spread across processes
        async with self.create_pool() as pool:
            async def generate(playlist: Playlist) -> GenerateStats | None:
                path = self.outdir / f"{playlist.title}.dat"
                sources = rdb_source_dats(PARENT_DIR, playlist.title)
                if not sources:
                    self._log.warning("No DAT files compile into %s.rdb; skipping", playlist.title)
                    path.unlink(missing_ok=True)
                    return None

                try:
                    entries = await pool.apply(compile_dats_async, (sources, match_key(playlist)))
                except (pe.ParseError, ProxyException) as e:
                    # (ProxyException is how the pool reports a ParseError raised in a worker)
                    # c_converter aborts on the same error, so this .rdb can't be built at all
                    self._log.error("Can't parse the DAT files for %s.rdb: %s", playlist.title, e)
                    path.unlink(missing_ok=True)
                    return None

                return self._generate_dat(catalog, playlist, entries, path)

            tasks = [asyncio.create_task(generate(p), name=p.title) for p in playlists]
            results = await asyncio.gather(*tasks)

        stats = [s for s in results if s is not None]
        self._log.info("Summary:\n%s", GenerateStats.table(stats))
        self._log.info("Elapsed time: %s", timedelta(seconds=time.perf_counter() - start))

    def _generate_dat(self, catalog: Catalog, playlist: Playlist, entries: Mapping[str, CompiledEntry], path: Path) -> GenerateStats:
        deriver = Deriver(catalog, playlist)
        stats = GenerateStats(playlist.title, entries=len(entries))
        games: list[DatGame] = []

        for key, entry in entries.items():
            derivation = deriver.derive(entry)
            stats.record(derivation)

            new_fields = missing_fields(entry, derivation.fields)
            if not new_fields:
                continue

            if get_dat_match(entry.game, match_key(playlist)) != key:
                # c_converter keyed this entry by some other field (see compile_dats),
                # so the `rom` record that would identify it here
                # would overwrite the entry's own `rom` record with a different value
                stats.rekeyed += 1
                continue

            stats.filled.update(new_fields.keys())
            games.append(DatGame.model_validate({
                # The same name (or comment) that the entry ends up with anyway, for readability
                **entry_label(entry),
                **new_fields,
                **derivation.sources,
                "rom": (key_rom(playlist.id_type, key),),
            }))

        stats.written = len(games)
        if games:
            # c_converter reads bytes, and so may the DAT files this echoes names and keys from
            with path.open("w", encoding="utf-8", errors="surrogateescape", newline="\n") as out:
                encode_dat(ParsedDatFile((dat_header(playlist), *games)).to_dat(), out)
        else:
            path.unlink(missing_ok=True)

        self._log.info(
            "%s: %d of %d entries matched to IGDB, %d DAT entries written",
            playlist.title, stats.igdb, stats.entries, stats.written,
        )
        return stats


@dataclass
class GenerateStats:
    playlist: str
    entries: int = 0
    hasheous: int = 0
    igdb: int = 0
    ambiguous: int = 0
    rekeyed: int = 0
    written: int = 0
    filled: Counter[str] = field(default_factory=Counter)

    def record(self, derivation: Derivation) -> None:
        """Counts what the sources know about one entry."""
        self.hasheous += bool(derivation.hasheous_games)
        self.igdb += derivation.igdb is not None
        self.ambiguous += derivation.ambiguous

    @staticmethod
    def table(stats: Iterable[GenerateStats]) -> str:
        stats = sorted(stats, key=lambda s: s.playlist)
        header = ("playlist", "entries", "hasheous", "igdb", "ambiguous", "rekeyed", "written", *RDB_FIELDS)
        rows = [header]
        for s in stats:
            rows.append((s.playlist, s.entries, s.hasheous, s.igdb, s.ambiguous, s.rekeyed, s.written, *(s.filled[f] for f in RDB_FIELDS)))

        totals = ("TOTAL", *(sum(r[i] for r in rows[1:]) for i in range(1, len(header))))
        rows.append(totals)
        return "\n".join("\t".join(str(c) for c in r) for r in rows)


MODEL_TYPES = (
    *IGDB_OBJECT_TYPES,
    *HASHEOUS_OBJECT_TYPES,
    *DAT_OBJECT_TYPES,
    AllRoms,
)

log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('[%(asctime)s][%(name)s][%(taskName)s] %(message)s'))
sqlalchemy_engine_log = logging.getLogger('sqlalchemy.engine.Engine')
sqlalchemy_engine_log.addHandler(log_handler)


def show_logs(*names: str, verbose: bool) -> None:
    """Prints what the named loggers log, including debug messages if `verbose`."""
    for name in names:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        logger.addHandler(log_handler)


class IndexSubCommand(BaseModel, CommonArgs, PlaylistArgs, IndexArgs, PoolArgs, VerboseArgs):
    """Build a single SQLite index database containing IGDB, DAT, and Hasheous data."""

    output: Path = Field(
        default=PARENT_DIR / 'tmp' / 'index.db',
        description="Path to the output SQLite database file.",
        validation_alias=AliasChoices('o', 'output'),
        validate_default=True,
    )

    filter_hasheous: bool = Field(
        default=True,
        description="""
            Skip Hasheous games and ROMs that no DAT file describes.
            They can't contribute to an `.rdb`, and they outnumber the ones that can
            by more than ten to one.
            Turn this off to index every Hasheous entry.
        """,
    )

    _db_lock = asyncio.Lock()
    _log = logging.getLogger('match.index')

    async def cli_cmd(self) -> None:
        start = time.perf_counter()
        show_logs(self._log.name, 'hasheous.index', 'igdb.index', 'dats.index', verbose=self.verbose)

        if self.verbose:
            sqlalchemy_engine_log.setLevel(logging.INFO)

        self.output.parent.mkdir(parents=True, exist_ok=True)

        if self.output.exists() and not self.force:
            raise FileExistsError(f"Output database file '{self.output}' already exists. Use --force to overwrite.")

        # Remove existing database file if it exists
        self.output.unlink(missing_ok=True)

        playlists = PlaylistConfig.load(self.config).playlists_titled(self.playlists)

        # Create a single database with tables for all three data sources
        db, metadata = await create_db(self.output, MODEL_TYPES)
        sqlalchemy_engine_log.setLevel(logging.WARNING)

        # Run all three indexing tasks concurrently against the same database

        async with self.create_pool() as pool:
            async with asyncio.TaskGroup() as group:
                # IGDB has no ROM data, so it can run alongside anything.
                group.create_task(
                    index_igdb(db=db, metadata=metadata, db_lock=self._db_lock, playlists=playlists, igdb_path=self.igdb_path, pool=pool, concurrency=self.concurrency or DEFAULT_IGDB_CONCURRENCY),
                    name="IGDB"
                )

                # The DAT files come first, because they decide
                # which of Hasheous's much larger dumps are worth indexing at all.
                await index_dats(db=db, metadata=metadata, db_lock=self._db_lock, playlists=playlists, dat_dirs=self.dat_dirs, pool=pool, concurrency=self.concurrency or DEFAULT_DAT_CONCURRENCY)

                dat_keys_path = None
                if self.filter_hasheous:
                    dat_keys_path = await write_dat_key_index(db, metadata, self.output.with_suffix(".datkeys.db"))

                group.create_task(
                    index_hasheous(db=db, metadata=metadata, db_lock=self._db_lock, playlists=playlists, hasheous_path=self.hasheous_path, pool=pool, concurrency=self.concurrency or DEFAULT_HASHEOUS_CONCURRENCY, dat_keys_path=dat_keys_path),
                    name="Hasheous"
                )


        # Now that every row is in, build the indexes that were held back
        # while the tables were being filled.
        # Combining the ROM data needs them, so this has to happen first.
        self._log.info("Building deferred indexes")
        await create_deferred_indexes(db, metadata)

        await self._insert_allrom_mappings(db=db, db_lock=self._db_lock, metadata=metadata)

        async with db.connect() as connection:
            # Run the SQLite optimizer to improve performance on all tables (0x10000),
            # but don't take too long (0x00010)
            await connection.execute(text("PRAGMA optimize = 0x10012"))

        # Close the engine
        await db.dispose()

        self._log.info("Elapsed time: %s", timedelta(seconds=time.perf_counter() - start))

    # The columns that a DAT ROM and a Hasheous ROM can be matched on,
    # from most to least trustworthy.
    # A weaker identifier is only consulted for ROMs that a stronger one didn't match.
    _HASH_MATCH_COLUMNS = ("sha1", "md5", "crc")

    _MAX_GAMES_PER_SERIAL = 8
    """
    How many DAT games a serial may be shared by before it stops counting as an identifier.

    A game's regional releases and revisions legitimately share one serial,
    which is why this isn't simply one:
    99.88% of the serials in the DAT files are shared by eight games or fewer.
    Beyond that are the placeholders that stand in for a serial nobody recorded --
    `00000000-00` alone covers 330 games, and `NTRJ`, `MK-0000-00` and `XXXXXXXX-XX`
    cover dozens each. Matching on one of those would attach
    some unrelated game's metadata to every ROM that carries it.
    """

    async def _insert_allrom_mappings(self, db: AsyncEngine, db_lock: asyncio.Lock, metadata: MetaData) -> None:
        self._log.debug("Aggregating ROM data into one table")
        allroms = AllRoms.table(metadata)
        datrom = DatRom.table(metadata)
        hasheousrom = HasheousRomItem.table(metadata)

        # A Hasheous ROM that some AllRoms row has already claimed.
        # Each Hasheous ROM may only be attached to one AllRoms row,
        # so later (weaker) matching passes have to skip the ones already taken.
        already_claimed = (
            select(allroms.c.hasheous_rom)
            .where(allroms.c.hasheous_rom == hasheousrom.c.id)
            # Correlate the Hasheous side only, so that AllRoms stays
            # in the subquery's own FROM clause instead of being correlated away.
            .correlate(hasheousrom)
            .exists()
        )

        async with db_transaction(db, db_lock) as tx:
            # Seed the table with every ROM that the DAT files know about.
            # DatRom's hashes are unique, so these rows can't collide with each other.
            self._log.debug("Seeding %s from %s", AllRoms.__tablename__, DatRom.__tablename__)
            await tx.execute(
                insert(allroms).from_select(
                    ["dat_rom", "crc", "serial", "md5", "sha1"],
                    select(
                        datrom.c.rowid.label("dat_rom"),
                        datrom.c.crc,
                        datrom.c.serial,
                        datrom.c.md5,
                        datrom.c.sha1,
                    )
                    # SQLite can't tell an upsert's ON from a join's ON
                    # unless the SELECT it reads from has a WHERE clause.
                    .where(true())
                ).on_conflict_do_nothing()
            )

            # Attach each Hasheous ROM to the DAT ROM it matches, strongest hash first.
            # SQLite can't take several conflict targets in one upsert,
            # so the merge is done as a series of UPDATE ... FROM statements
            # instead of one INSERT ... ON CONFLICT DO UPDATE.
            for match_column in self._HASH_MATCH_COLUMNS:
                result = await tx.execute(
                    allroms.update()
                        .where(
                            allroms.c.hasheous_rom.is_(None),
                            allroms.c[match_column].is_not(None),
                            allroms.c[match_column] == hasheousrom.c[match_column],
                            ~already_claimed,
                        )
                        .values(
                            hasheous_rom=hasheousrom.c.id,
                            crc=coalesce(allroms.c.crc, hasheousrom.c.crc),
                            serial=coalesce(allroms.c.serial, hasheousrom.c.serial),
                            md5=coalesce(allroms.c.md5, hasheousrom.c.md5),
                            sha1=coalesce(allroms.c.sha1, hasheousrom.c.sha1),
                            sha256=coalesce(allroms.c.sha256, hasheousrom.c.sha256),
                        )
                )
                self._log.info("Matched %d ROMs on %s", result.rowcount, match_column)

            # Serials identify a game, not a particular dump of it:
            # the same disc can be dumped many ways, and a fan translation
            # or a mod usually keeps the serial of whatever it was built from.
            # So a serial match may legitimately be many DAT ROMs to one Hasheous ROM,
            # and it must not copy that ROM's hashes across,
            # since those describe a different dump than the one the DAT file lists.
            game_roms = DatGame.relationship_table(metadata, "roms")
            overused_serials = (
                select(game_roms.c.serial)
                .where(game_roms.c.serial.is_not(None))
                .group_by(game_roms.c.serial)
                .having(count(game_roms.c.game.distinct()) > self._MAX_GAMES_PER_SERIAL)
                .scalar_subquery()
            )

            result = await tx.execute(
                allroms.update()
                    .where(
                        allroms.c.hasheous_rom.is_(None),
                        allroms.c.serial.is_not(None),
                        allroms.c.serial == hasheousrom.c.serial,
                        allroms.c.serial.not_in(overused_serials),
                    )
                    .values(hasheous_rom=hasheousrom.c.id)
            )
            self._log.info("Matched %d ROMs on serial", result.rowcount)

            # Whatever Hasheous knows about but the DAT files don't gets its own row.
            result = await tx.execute(
                insert(allroms).from_select(
                    ["hasheous_rom", "crc", "serial", "md5", "sha1", "sha256"],
                    select(
                        hasheousrom.c.id.label("hasheous_rom"),
                        hasheousrom.c.crc,
                        hasheousrom.c.serial,
                        hasheousrom.c.md5,
                        hasheousrom.c.sha1,
                        hasheousrom.c.sha256,
                    ).where(~already_claimed)
                ).on_conflict_do_nothing()
            )
            self._log.info("Inserted %d unmatched Hasheous ROMs", result.rowcount)

            await tx.commit()


class MatchCommand(BaseSettings):
    generate: CliSubCommand[GenerateSubCommand]
    index: CliSubCommand[IndexSubCommand]

    model_config = SettingsConfigDict(
        case_sensitive=False,
        cli_avoid_json=True,
        cli_implicit_flags=True,
        cli_kebab_case=True,
        cli_parse_args=True,
        extra="ignore",
    )

    def cli_cmd(self):
        CliApp.run_subcommand(self)

if __name__ == "__main__":
    CliApp.run(MatchCommand)
