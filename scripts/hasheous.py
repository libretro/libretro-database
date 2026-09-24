#!/usr/bin/env python3
"""
Dictionary definitions taken from the following Hasheous source files:

- https://github.com/gaseous-project/hasheous/blob/main/hasheous-lib/Models/DataObjectItem.cs
- https://github.com/gaseous-project/hasheous/blob/main/hasheous-lib/Models/DataObjectItemModel.cs
- https://github.com/gaseous-project/hasheous/blob/main/hasheous-lib/Models/Signatures_Games.cs
- https://github.com/gaseous-project/gaseous-signature-parser/blob/main/gaseous-signature-parser/models/RomSignatureObject.cs
"""

import asyncio
import csv
import logging
import sqlite3
import sys
import time
import tomllib

from abc import ABC
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import Annotated, Any, ClassVar, Literal, NamedTuple, NewType, Optional, TypeAlias, TypedDict, override
from zipfile import ZipFile, ZipInfo

import aiofiles
import aiofiles.os
import backoff
import frozendict
import httpx

from aioitertools.asyncio import as_completed
from aiomultiprocess import Pool
from more_itertools import first_true, map_reduce
from pydantic import AfterValidator, AliasChoices, BaseModel, ByteSize, ConfigDict, DirectoryPath, Discriminator, Field, FieldSerializationInfo, FilePath, HttpUrl, OnErrorOmit, SerializerFunctionWrapHandler, StringConstraints, Tag, ValidationError, computed_field, field_serializer
from pydantic.alias_generators import to_pascal
from pydantic_settings import BaseSettings, CliApp, CliPositionalArg, CliSubCommand, SettingsConfigDict
from sqlalchemy import Column, Computed, ForeignKey, MetaData, String, Index, column, text
from sqlalchemy.dialects.sqlite import INTEGER, JSON, insert, Insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine
from sqlalchemy.util import is_non_string_iterable

from igdb import IgdbId
from dats import DAT_KEY_TABLE
from playlist import Playlist, PlaylistArgs, PlaylistConfig, PlaylistTitle
from sqlite import DatabaseModel, ExtractedRows, InsertInRowContext, RowAccumulator, RowDeduplicator, create_db, db_transaction
from utils import CliTuple, Crc, DEFAULT_HASHEOUS_CONCURRENCY, EmptyStringToNone, EmptyToNone, FrozenDict, FrozenJsonValue, IndexArgs, Md5, PoolArgs, Sha1, Sha256, FrozenTypedDict, VerboseArgs

METADATA_MAP_URL = "https://hasheous.org/api/v1/Dumps/MetadataMap.zip"

HasheousId = NewType('HasheousId', int)

class HasheousObject(DatabaseModel, ABC, frozen=True):
    pass

@dataclass(frozen=True)
class SignatureDataObject:
    __pydantic_config__: ClassVar[ConfigDict] = ConfigDict(alias_generator=to_pascal)
    __tablename__ = "HasheousSignatureDataObject"
    signature_id: int
    name: EmptyStringToNone[str] = None
    year: EmptyStringToNone[str] = None
    platform: EmptyStringToNone[str] = None
    source_id: EmptyStringToNone[int] = None
    publisher: EmptyStringToNone[str] = None
    metadata_source: EmptyStringToNone[str] = None

MappingStatus: TypeAlias = Literal["NotMapped", "Mapped", "MappedWithErrors"]
ImageId = Annotated[str, StringConstraints(to_upper=True)]

MatchMethodType: TypeAlias = Literal[
    "NoMatch",
    "Automatic",
    "Manual",
    "AutomaticTooManyMatches",
    "ManualByAdmin",
    "Voted",
]

@dataclass(frozen=True)
class MetadataItem:
    __pydantic_config__: ClassVar[ConfigDict] = ConfigDict(alias_generator=to_pascal)

    id: EmptyStringToNone[str]
    immutable_id: Annotated[EmptyStringToNone[str], Field(default=None)]
    """Missing from unmapped entries in newer dumps."""
    status: MappingStatus
    match_method: str
    source: str
    link: Annotated[EmptyStringToNone[HttpUrl], Field(default=None)]

DataObjectType: TypeAlias = Literal["None", "Company", "Platform", "Game", "ROM", "App"]

class MediaType(TypedDict, total=False):
    MediaType: str
    Media: str
    Number: int
    Count: int
    Side: str

class RomItem(HasheousObject, frozen=True, alias_generator=to_pascal):
    """
    Structure taken from https://github.com/gaseous-project/hasheous/blob/main/hasheous-lib/Schema/hasheous-1000.sql
    (specifically the Signatures_Roms table)
    """
    __tablename__ = "HasheousRomItem"
    __tableargs__ = (
        # These indexes are intentionally not unique, because some games on Hasheous
        # have multiple ROM entries with the same hash,
        # probably due to Hasheous fetching data about the same logical ROM from different sources.
        # Example: Asteroids Deluxe for the Atari 7800, id 296592;
        # the MD5 of a65f79ad4a0bbdecd59d5f7eb3623fd7 appears with ROM IDs 2591517 and 3455253
        # Our solution is the AllRoms table in match.py, which de-duplicates ROMs by hash and associates them with all relevant games.
        Index("ix_HasheousRomItem_crc_where_not_null", "crc", sqlite_where=column("crc").is_not(None)),
        Index("ix_HasheousRomItem_serial_where_not_null", "serial", sqlite_where=column("serial").is_not(None)),
        Index("ix_HasheousRomItem_md5_where_not_null", "md5", sqlite_where=column("md5").is_not(None)),
        Index("ix_HasheousRomItem_sha1_where_not_null", "sha1", sqlite_where=column("sha1").is_not(None)),
        Index("ix_HasheousRomItem_sha256_where_not_null", "sha256", sqlite_where=column("sha256").is_not(None)),
    )
    # Adds partial indexes to speed up lookups

    id: Annotated[int, Column(primary_key=True, index=True, unique=True)]
    name: EmptyStringToNone[str]
    score: int
    """
    The quality of this ROM's data. Better data means better score.
    See https://github.com/gaseous-project/hasheous/blob/main/hasheous-lib/Models/Signatures_Games.cs
    """
    attributes: Annotated[EmptyToNone[FrozenDict[str, FrozenJsonValue]], AfterValidator(frozendict.deepfreeze), Column(JSON(none_as_null=True))]
    """
    Source-specific fields, not all strings (e.g. TOSEC's `categories` is a list).
    Keep this type loose; `RomsAttribute` silently drops any ROM that fails validation.
    """
    rom_type: str
    size: ByteSize
    crc: EmptyToNone[Crc]
    md5: EmptyToNone[Md5]
    sha1: EmptyToNone[Sha1]
    sha256: EmptyToNone[Sha256]
    status: EmptyToNone[str]
    country: Annotated[EmptyToNone[FrozenDict[str, str]], Column(JSON(none_as_null=True))]
    language: Annotated[EmptyToNone[FrozenDict[str, str]], Column(JSON(none_as_null=True))]
    development_status: EmptyToNone[str]
    rom_type_media: EmptyToNone[str]
    media_detail: Annotated[EmptyToNone[FrozenTypedDict[MediaType]], Column(JSON(none_as_null=True))]
    media_label: EmptyToNone[str]
    signature_source: EmptyToNone[str]

    @computed_field(return_type=Annotated[str | None, Column("serial", String(), Computed("attributes ->> '$.serial'"), index=True, nullable=True)])
    @property
    def serial(self):
        return self.attributes.get("serial") if self.attributes else None

    @property
    @override
    def as_row(self) -> dict[str, Any]:
        # Exclude serial so we don't try to insert it into a computed column
        return self.model_dump(context='row', exclude={"serial"})

    @override
    @classmethod
    def insert(cls, metadata: MetaData) -> Insert:
        # Override the default insert to exclude the computed 'serial' column
        return super().insert(metadata).on_conflict_do_nothing()

type EmptyDict = Annotated[dict, Field(min_length=0, max_length=0)]

def attribute_discriminator(v: Any) -> str:
    match v:
        case CompanyAttribute() | {"attributeRelationType": "Company"}:
            return "Company"
        case PlatformAttribute() | {"attributeRelationType": "Platform"}:
            return "Platform"
        case RomsAttribute() | {"attributeRelationType": "ROM"}:
            return "ROMs"
        case CountryAttribute() | {"attributeName": "Country"}:
            return "Country"
        case LanguageAttribute() | {"attributeName": "Language"}:
            return "Language"
        case UnknownAttribute() | {"attributeType": str(), "attributeName": str(), "attributeRelationType": str(), "Value": _}:
            return "Unknown"
        case _:
            raise ValueError(f"Unable to determine attribute type for value: {v}")

@dataclass(frozen=True)
class CompanyAttribute:
    attribute_type: Annotated[Literal["ObjectRelationship"], Field(validation_alias='attributeType')]
    attribute_name: Annotated[str, Field(validation_alias='attributeName')]
    attribute_relation_type: Annotated[Literal["Company"], Field(validation_alias='attributeRelationType')]
    value: Annotated["CompanyDataObject", Field(validation_alias='Value')]

@dataclass(frozen=True)
class CountryAttribute:
    attribute_type: Annotated[Literal["ShortString"], Field(validation_alias='attributeType')]
    attribute_name: Annotated[Literal["Country"], Field(validation_alias='attributeName')]
    attribute_relation_type: Annotated[Literal["None"], Field(validation_alias='attributeRelationType')]
    value: Annotated[str, Field(validation_alias='Value')]

@dataclass(frozen=True)
class LanguageAttribute:
    attribute_type: Annotated[Literal["ShortString"], Field(validation_alias='attributeType')]
    attribute_name: Annotated[Literal["Language"], Field(validation_alias='attributeName')]
    attribute_relation_type: Annotated[Literal["None"], Field(validation_alias='attributeRelationType')]
    value: Annotated[str, Field(validation_alias='Value')]

@dataclass(frozen=True)
class PlatformAttribute:
    attribute_type: Annotated[Literal["ObjectRelationship"], Field(validation_alias='attributeType')]
    attribute_name: Annotated[Literal["Platform"], Field(validation_alias='attributeName')]
    attribute_relation_type: Annotated[Literal["Platform"], Field(validation_alias='attributeRelationType')]
    value: Annotated["PlatformDataObject", Field(validation_alias='Value')]
    id: Annotated[int, Field(validation_alias='Id')]

@dataclass(frozen=True)
class RomsAttribute:
    attribute_type: Annotated[Literal["EmbeddedList"], Field(validation_alias='attributeType')]
    attribute_name: Annotated[Literal["ROMs"], Field(validation_alias='attributeName')]
    attribute_relation_type: Annotated[Literal["ROM"], Field(validation_alias='attributeRelationType')]
    value: Annotated[tuple[OnErrorOmit[RomItem], ...], Field(validation_alias='Value')]

@dataclass(frozen=True)
class UnknownAttribute:
    attribute_type: Annotated[str, Field(validation_alias='attributeType')]
    attribute_name: Annotated[str, Field(validation_alias='attributeName')]
    attribute_relation_type: Annotated[str, Field(validation_alias='attributeRelationType')]
    value: Annotated[Any, Field(validation_alias='Value'), AfterValidator(frozendict.deepfreeze)]
    id: Annotated[int | None, Field(validation_alias='Id')] = None

Attribute = Annotated[
    Annotated[CompanyAttribute, Tag("Company")] |
    Annotated[CountryAttribute, Tag("Country")] |
    Annotated[LanguageAttribute, Tag("Language")] |
    Annotated[PlatformAttribute, Tag("Platform")] |
    Annotated[RomsAttribute, Tag("ROMs")] |
    Annotated[UnknownAttribute, Tag("Unknown")],
    Discriminator(attribute_discriminator)
]
DataObjectAttributeColumn = Annotated[
    "DataObject | None",
    Column(ForeignKey('HasheousDataObject.id'), index=True)
]

CompanyDataObjectAttributeColumn = Annotated[
    "CompanyDataObject | None",
    Column(ForeignKey('HasheousCompanyDataObject.id'), index=True)
]

PlatformDataObjectAttributeColumn = Annotated[
    "PlatformDataObject | None",
    Column(ForeignKey('HasheousPlatformDataObject.id'), index=True)
]

class DataObject(DatabaseModel, ABC, frozen=True, alias_generator=to_pascal):
    """
    Type info for attributes taken from https://github.com/gaseous-project/hasheous/blob/main/hasheous-lib/Classes/DataObjects.cs
    """

    id: Annotated[HasheousId, Column(INTEGER, primary_key=True)]
    name: str
    signature_data_objects: Annotated[tuple[SignatureDataObject, ...], Field(exclude=True)]
    metadata: Annotated[tuple[MetadataItem, ...], Field(exclude=True)]
    attributes: Annotated[tuple[Attribute, ...], Field(exclude=True)]
    # We may want to add created_date/update_date back
    # if we decide to start updating the index database incrementally
    #created_date: datetime
    #updated_date: datetime

    @field_serializer('platform', 'manufacturer', 'publisher', mode='wrap', check_fields=False)
    def _serialize_field(self, value: Any, handler: SerializerFunctionWrapHandler, info: FieldSerializationInfo[InsertInRowContext]):
        match (info.context, value):
            case (None, _):
                # If no context is given, serialize the field as usual
                return handler(value)
            case ('row', DataObject()):
                # If serializing for a database row, serialize nested DataObjects as their IDs
                return value.id
            case (_, _):
                # Otherwise, run the default serializer to handle other types or contexts
                return handler(value)

    def _get_igdb_id(self) -> IgdbId | None:
        """Returns the IGDB ID mapped to this DataObject, or None if there's no IGDB mapping."""
        igdb_metadata = first_true(self.metadata, pred=lambda m: m.source == "IGDB" and m.status == "Mapped")
        if not igdb_metadata:
            return None
        if not igdb_metadata.immutable_id:
            return None

        try:
            return IgdbId(int(igdb_metadata.immutable_id))
        except ValueError:
            return None

    @override
    @classmethod
    def insert(cls, metadata: MetaData) -> Insert:
        return super().insert(metadata).on_conflict_do_nothing()


class PlatformDataObject(DataObject, frozen=True, alias_generator=to_pascal):
    __tablename__ = "HasheousPlatformDataObject"
    object_type: Annotated[Literal["Platform"], Field(exclude=True)]

    @computed_field(return_type=IgdbId | None)
    @cached_property
    def igdb_id(self):
        """Returns the IGDB ID mapped to this DataObject, or None if there's no IGDB mapping."""
        return self._get_igdb_id()

    @computed_field(return_type=CompanyDataObjectAttributeColumn)
    @cached_property
    def manufacturer(self):
        attribute = first_true(self.attributes, pred=lambda a: a.attribute_name == "Manufacturer")
        return attribute.value if attribute and isinstance(attribute.value, CompanyDataObject) else None

class CompanyDataObject(DataObject, frozen=True, alias_generator=to_pascal):
    __tablename__ = "HasheousCompanyDataObject"
    object_type: Annotated[Literal["Company"], Field(exclude=True)]

    @computed_field(return_type=IgdbId | None)
    @cached_property
    def igdb_id(self):
        """Returns the IGDB ID mapped to this DataObject, or None if there's no IGDB mapping."""
        return self._get_igdb_id()

class GameDataObject(DataObject, frozen=True, alias_generator=to_pascal):
    __tablename__ = "HasheousGameDataObject"
    __tableargs__ = (
        Index("ix_HasheousGameDataObject_igdb_id_where_not_null", "igdb_id", sqlite_where=column("igdb_id").is_not(None)),
    )

    object_type: Annotated[Literal["Game"], Field(exclude=True)]

    @computed_field
    @cached_property
    def roms(self) -> tuple[RomItem, ...]:
        attribute = first_true(self.attributes, pred=lambda a: a.attribute_name == "ROMs")
        return tuple(attribute.value) if attribute and is_non_string_iterable(attribute.value) else ()

    @computed_field(return_type=IgdbId | None)
    @cached_property
    def igdb_id(self):
        """Returns the IGDB ID mapped to this DataObject, or None if there's no IGDB mapping."""
        return self._get_igdb_id()

    @computed_field(return_type=int | None)
    @cached_property
    def retroachievements_id(self):
        ra_metadata = first_true(self.metadata, pred=lambda m: m.source == "RetroAchievements" and m.status == "Mapped")
        if not ra_metadata:
            return None
        if not ra_metadata.immutable_id:
            return None

        try:
            return int(ra_metadata.immutable_id)
        except ValueError:
            return None

    @computed_field
    @cached_property
    def manufacturer(self) -> CompanyDataObjectAttributeColumn:
        attribute = first_true(self.attributes, pred=lambda a: a.attribute_name == "Manufacturer")
        return attribute.value if attribute and isinstance(attribute.value, CompanyDataObject) else None

    @computed_field
    @cached_property
    def publisher(self) -> CompanyDataObjectAttributeColumn:
        attribute = first_true(self.attributes, pred=lambda a: a.attribute_name == "Publisher")
        return attribute.value if attribute and isinstance(attribute.value, CompanyDataObject) else None

    @computed_field
    @cached_property
    def platform(self) -> PlatformDataObjectAttributeColumn:
        attribute = first_true(self.attributes, pred=lambda a: a.attribute_name == "Platform")
        return attribute.value if attribute and isinstance(attribute.value, PlatformDataObject) else None

    @computed_field
    @cached_property
    def country(self) -> tuple[str, ...]:
        # TODO: Need to provide an index on the country values for efficient querying
        attribute = first_true(self.attributes, pred=lambda a: a.attribute_name == "Country")
        if not attribute or not isinstance(attribute.value, str):
            return ()

        return tuple(c.strip() for c in attribute.value.split(','))

    @computed_field
    @cached_property
    def language(self) -> tuple[str, ...]:
        attribute = first_true(self.attributes, pred=lambda a: a.attribute_name == "Language")
        if not attribute or not isinstance(attribute.value, str):
            return ()

        return tuple(lang.strip() for lang in attribute.value.split(','))

class PlaylistDumpMapping(DatabaseModel, frozen=True):
    __tablename__ = "HasheousPlaylistDumpMapping"
    __tablekwargs__ = {"sqlite_with_rowid": False}
    playlist: Annotated[PlaylistTitle, Column(primary_key=True, index=True)]
    dump: Annotated[str, Column(primary_key=True, index=True)]

class GameDumpMapping(DatabaseModel, frozen=True):
    __tablename__ = "HasheousGameDumpMapping"
    __tablekwargs__ = {"sqlite_with_rowid": False}
    __tableargs__ = (
        Index("ix_HasheousGameDumpMapping_games_unique", "game", unique=True),
    )

    game: Annotated[HasheousId, Column(ForeignKey('HasheousGameDataObject.id'), primary_key=True, index=True)]
    dump: Annotated[str, Column(primary_key=True, index=True)]

HASHEOUS_OBJECT_TYPES = (
    GameDataObject,
    PlatformDataObject,
    CompanyDataObject,
    #SignatureDataObject,
    RomItem,
    PlaylistDumpMapping,
    GameDumpMapping,
)

class HasheousConfig(BaseModel, frozen=True):
    """How `match.py` interprets Hasheous's data."""

    regions_by_country_code: FrozenDict[str, str] = frozendict.frozendict()
    """
    Hasheous's country codes for the regions whose names it spells differently than the DAT files.
    The names of all other countries already match.
    """

    ignored_games: frozenset[int] = frozenset()
    """
    Hasheous games whose ROMs identify nothing, so `match.py` skips those ROMs under every game that lists them.
    """

class MatchRecord(NamedTuple):
    """
    A record of an attempt to match a game listed in one of this repo's DAT files
    with an entry in IGDB and/or Hasheous.
    Intended for output to a CSV file for later analysis.
    """

    name: str
    """
    The name of the game as listed in the DAT file.
    If the game is listed under multiple names,
    the first one found wins.
    """

    crc: Optional[str]
    """
    The CRC32 of the game's ROM, if available.
    """

    md5: Optional[str]
    """
    The MD5 hash of the game's ROM, if available.
    """

    sha1: Optional[str]
    """
    The SHA-1 hash of the game's ROM, if available.
    """

    serial: Optional[str]
    """
    The serial number of the game's ROM, if available.
    """

    hasheous_id: Optional[int]
    """
    The ID number of this game's entry on Hasheous, if one was found.
    """

    hasheous_url: Optional[str]
    """
    The URL of this game's entry on Hasheous, if one was found.
    """

    igdb_id: Optional[int]
    """
    The ID number of this game's entry on IGDB, if one was found.
    """

    igdb_url: Optional[str]
    """
    The URL of this game's entry on IGDB, if one was found.
    """

    igdb_release_id: Optional[int]
    """
    The ID number of this game's release on IGDB for the platform named by igdb_platform_id.
    """

    igdb_platform_id: Optional[int]
    """
    The ID number of the platform on IGDB that this game was released for.
    """

    @property
    def matched(self) -> bool:
        return \
            self.igdb_id is not None and \
            self.hasheous_id is not None and \
            (self.crc is not None or self.serial is not None)


class LoadedDump(NamedTuple):
    """The result of expanding one Hasheous dump into database rows."""

    game_ids: tuple[int, ...]
    """The IDs of the games that were kept, used to build the game-dump mappings."""

    rows: ExtractedRows

    loaded_games: int
    """How many games the archive held, before any were filtered out."""


_dat_keys: dict[Path, sqlite3.Connection] = {}


def _dat_key_lookup(dat_keys_path: Path) -> sqlite3.Connection:
    """
    Opens the DAT key index written by `dats.write_dat_key_index`, once per worker process.

    The file is opened immutable so that SQLite skips all locking
    and every worker can share the operating system's cache of it.
    """
    connection = _dat_keys.get(dat_keys_path)

    if connection is None:
        connection = sqlite3.connect(f"file:{dat_keys_path.as_posix()}?immutable=1", uri=True)
        _dat_keys[dat_keys_path] = connection

    return connection


def _relevant_rom_ids(game: GameDataObject, dat_keys: sqlite3.Connection) -> frozenset[int]:
    """
    Returns the IDs of `game`'s ROMs that some DAT file also describes.

    A ROM counts if any of its identifiers appears in the DAT corpus.
    CRCs and serials are what RetroArch identifies games by;
    MD5 and SHA-1 aren't, but they still tie a Hasheous entry to a DAT entry,
    so a match on either is just as good for our purposes.
    """
    query = f'SELECT 1 FROM "{DAT_KEY_TABLE}" WHERE value IN (?, ?, ?, ?) LIMIT 1'

    return frozenset(
        rom.id
        for rom in game.roms
        if dat_keys.execute(query, (rom.crc, rom.md5, rom.sha1, rom.serial)).fetchone()
    )


def _keep_only(rom_ids: frozenset[int]) -> Callable[[str, Mapping[str, Any]], bool]:
    """
    Builds a predicate that drops the rows of every ROM outside `rom_ids`.

    A game's other ROMs are dumps that no DAT file lists,
    so nothing downstream can ever refer to them.
    """
    def keep(tablename: str, row: Mapping[str, Any]) -> bool:
        match tablename:
            case RomItem.__tablename__:
                return row["id"] in rom_ids
            case name if name == f"{GameDataObject.__tablename__}_roms":
                return row[f"{RomItem.__tablename__}_id"] in rom_ids
            case _:
                return True

    return keep


GAMES_PER_CHUNK = 1000
"""
How many of an archive's games one worker task handles.

A dump is read in chunks rather than whole
so that neither the worker nor the process inserting the rows
ever holds more than a chunk's worth at once.
Microsoft DOS alone expands to roughly 700 MB of rows alone,
and several dumps are in flight at a time.
"""


def _game_entries(zip: ZipFile) -> list[ZipInfo]:
    """Returns the archive entries that describe games, in a stable order."""
    return [
        info for info in zip.infolist()
        if info.filename.endswith('.json') and info.filename != 'PlatformMapping.json'
    ]


async def count_zip_games(path: Path) -> int:
    """
    Returns how many games an archive holds, without parsing any of them.

    Only the archive's index is read, so this is cheap even for the largest dumps.
    """
    async with aiofiles.open(path, "rb") as zip_file:
        with ZipFile(zip_file.raw) as zip:
            return len(_game_entries(zip))


async def load_zip(
    path: Path,
    dat_keys_path: Path | None = None,
    offset: int = 0,
    limit: int | None = None,
) -> LoadedDump:
    """
    Loads part of a Hasheous dump archive and expands it into database rows.

    Runs in a worker process, so the caller only pays to insert the rows,
    not to build them.
    Games are read one at a time and discarded as soon as their rows are taken,
    because the largest dumps don't fit in memory as models all at once.

    :param dat_keys_path: A key index from `dats.write_dat_key_index`.
      When given, games and ROMs that no DAT file describes are left out;
      they can't contribute to an `.rdb`, and they outnumber the ones that can
      by more than ten to one.
    :param offset: The index of the first game to read.
    :param limit: How many games to read, or None to read to the end.
    """
    dat_keys = _dat_key_lookup(dat_keys_path) if dat_keys_path is not None else None
    accumulator = RowAccumulator(GameDataObject.__tablename__)
    game_ids: list[int] = []
    loaded_games = 0

    async with aiofiles.open(path, "rb") as zip_file:
        with ZipFile(zip_file.raw) as zip:
            entries = _game_entries(zip)
            end = len(entries) if limit is None else offset + limit

            for info in entries[offset:end]:
                game = GameDataObject.model_validate_json(zip.read(info))
                loaded_games += 1
                keep = None

                if dat_keys is not None:
                    rom_ids = _relevant_rom_ids(game, dat_keys)
                    if not rom_ids:
                        # Nothing in this game is anything a DAT file describes.
                        continue

                    keep = _keep_only(rom_ids)

                accumulator.add(game, keep=keep)
                game_ids.append(game.id)

    return LoadedDump(
        game_ids=tuple(game_ids),
        rows=accumulator.result(),
        loaded_games=loaded_games,
    )


def _on_backoff(details):
    print("Retrying after backoff:", details['target'].__name__, "with args:", details['args'], "and kwargs:", details['kwargs'], file=sys.stderr)

RETRY_CODES = (
    httpx.codes.REQUEST_TIMEOUT,
    httpx.codes.TOO_MANY_REQUESTS,
    httpx.codes.INTERNAL_SERVER_ERROR,
    httpx.codes.BAD_GATEWAY,
    httpx.codes.SERVICE_UNAVAILABLE,
    httpx.codes.GATEWAY_TIMEOUT,
)

HASHEOUS_BASE_URL = "https://hasheous.org/api/v1/Dumps/platforms/"

def _giveup(e: Exception):
    print("Exception raised during query:", e, file=sys.stderr)
    if not isinstance(e, httpx.HTTPStatusError):
        # Give up if query_endpoint failed with something besides HTTPStatusError
        return True

    if e.response.status_code in RETRY_CODES:
        # Don't give up on server errors (5xx), we might just be unlucky
        # or rate-limited (429), so we should back off and retry.
        return False

    return e.response.is_error

class FetchSubCommand(BaseModel, VerboseArgs):
    config: FilePath = Field(
        default=Path(__file__).parent.parent / 'playlists.toml',
        title="Playlist Config File",
        description="Path to the config file that defines available playlists.",
        validation_alias=AliasChoices('c', 'config'),
        validate_default=True,
    )

    dumps: CliTuple[str] = Field(
        default=(),
        validation_alias=AliasChoices('d', 'dumps'),
        description="""
            The names of the Hasheous dumps to fetch.
            If not specified, all 'hasheous' entries in 'config' plus 'Unknown Platform' will be fetched.
        """
    )

    outdir: CliPositionalArg[Path] = Field(
        default=Path(__file__).parent.parent / 'tmp' / 'hasheous',
        description="""
            The output directory for the fetched Hasheous dumps.
            Will be created if it doesn't exist.
        """
    )

    async def cli_cmd(self):
        await aiofiles.os.makedirs(self.outdir, exist_ok=True)

        if self.dumps:
            # If specific dumps were requested, use those plus "Unknown Platform"
            dumps = set(self.dumps)
        else:
            # Otherwise, fetch all playlists that specify a Hasheous dump (but include "Unknown Platform" too)
            async with aiofiles.open(self.config, 'rb') as f:
                config = PlaylistConfig.model_validate(tomllib.load(f.raw))

            dumps = set(chain.from_iterable(p.hasheous_dirs for p in config.playlists))

        dumps.add("Unknown Platform")
        # "Unknown Platform" entries don't identify a specific platform,
        # but a lot of them do have CRCs that can be useful.

        async with asyncio.TaskGroup() as group:
            @backoff.on_exception(backoff.expo, httpx.HTTPStatusError, max_tries=5, giveup=_giveup, on_backoff=_on_backoff)
            async def fetch_dump(name: str):
                dump_url = f"{HASHEOUS_BASE_URL}{name}.zip"
                print(f"Fetching {dump_url}")

                async with httpx.AsyncClient() as client:
                    async with client.stream("GET", dump_url, timeout=httpx.Timeout(None)) as response:
                        if response.status_code == 404:
                            print(f"Error: dump {name} not found at {dump_url}, skipping", file=sys.stderr)
                            return

                        response.raise_for_status()
                        content_type = response.headers.get('content-type')

                        if not content_type or 'application/zip' not in content_type.lower():
                            raise ValueError(f"Expected content type 'application/zip', got {content_type} for dump {name}")

                        outpath = self.outdir / f"{name}.zip"
                        async with aiofiles.open(outpath, "wb") as out_file:
                            async for chunk in response.aiter_bytes():
                                await out_file.write(chunk)

                print(f"Saved dump to {outpath}")

            for d in dumps:
                group.create_task(fetch_dump(d), name=d)
            # The task group will wait for all fetches to complete

class MetadataMatch(TypedDict):
    source: Literal["IGDB"] # Only IGDB is supported for now
    platformId: str
    gameId: str

class FixMatchBody(TypedDict):
    mD5: Optional[str]
    shA1: Optional[str]
    metadataMatches: Sequence[MetadataMatch]

# See https://github.com/gaseous-project/hasheous/wiki/API:-Submission-%E2%80%90-FixMatch for API guidance
async def submit_matches(tsv_path: Path, api_key: str, dry_run: bool = False, verbose: bool = False) -> None:
    def read_match(row: dict[str, str]) -> MatchRecord:
        def parse_optional_int(value: str) -> Optional[int]:
            value = value.strip()
            if not value:
                return None
            return int(value)

        def parse_optional_str(value: str) -> Optional[str]:
            value = value.strip()
            if not value:
                return None
            return value

        return MatchRecord(
            name=row['name'].strip(),
            crc=parse_optional_str(row['crc']),
            md5=parse_optional_str(row['md5']),
            sha1=parse_optional_str(row['sha1']),
            serial=parse_optional_str(row['serial']),
            hasheous_id=parse_optional_int(row['hasheous_id']),
            hasheous_url=parse_optional_str(row['hasheous_url']),
            igdb_id=parse_optional_int(row['igdb_id']),
            igdb_url=parse_optional_str(row['igdb_url']),
            igdb_release_id=parse_optional_int(row['igdb_release_id']),
            igdb_platform_id=parse_optional_int(row['igdb_platform_id']),
        )

    def can_submit(match: MatchRecord) -> bool:
        return match.igdb_id is not None and \
               match.hasheous_id is not None and \
               ((match.md5 or match.sha1) is not None) and \
               match.crc is not None

    def make_body(match: MatchRecord) -> FixMatchBody:
        metadata_matches: Sequence[MetadataMatch] = [{
            "source": "IGDB",
            "platformId": str(match.igdb_platform_id),
            "gameId": str(match.igdb_release_id),
        }]

        return FixMatchBody(
            mD5=match.md5,
            shA1=match.sha1,
            metadataMatches=metadata_matches,
        )

    async with aiofiles.open(tsv_path, "r", encoding="utf-8") as tsv_file:
        lines = await tsv_file.readlines()
        reader = csv.DictReader(lines, fieldnames=MatchRecord._fields, dialect='excel-tab')
        matches = (read_match(m) for m in reader)
        valid_matches = filter(can_submit, matches)
        raise NotImplementedError("Submission functionality is not yet implemented.")

class SubmitSubCommand(BaseModel, VerboseArgs):
    api_key: str  = Field(
        description="The Hasheous API key to use for submission. Overrides the HASHEOUS_API_KEY environment variable if provided.",
        validation_alias=AliasChoices('a', 'api-key'),
    )

    dry_run: bool = Field(
        default=False,
        description="Don't actually submit anything; just show what would be submitted.",
        validation_alias=AliasChoices('n', 'dry-run'),
    )

    matchfiles: CliPositionalArg[tuple[FilePath, ...]] = Field(
        description="One or more TSV files containing match data to submit, as generated by match.py's `generate` subcommand. Only rows that include an IGDB ID, a Hasheous ID, a CRC, and an MD5 or SHA1 will be included.",
    )

    async def cli_cmd(self):
        if self.verbose:
            print("Match files to submit:", self.matchfiles)
            print("Dry run:", self.dry_run)

        async with asyncio.TaskGroup() as group:
            for matchfile in self.matchfiles:
                group.create_task(
                    submit_matches(
                        matchfile,
                        self.api_key,
                        dry_run=self.dry_run,
                        verbose=self.verbose
                    ),
                    name=matchfile.stem
                )

PARENT_DIR = Path(__file__).parent.parent

class HasheousJob(NamedTuple):
    name: str
    playlists: set[Playlist]
    loaded: LoadedDump

_hasheous_index_log = logging.getLogger('hasheous.index')

async def _execute_with_bisect_on_error(tx: AsyncConnection, stmt, rows: Sequence[Mapping[str, Any]], log):
    """
    Attempt a bulk insert; on IntegrityError, bisect the batch to find the offending row.
    NOTE: This is a debugging aid — bisecting retries only happen on error,
    so the happy path has no overhead.
    """
    try:
        await tx.execute(stmt, rows)
    except Exception as e:
        if len(rows) == 1:
            # Base case: we've isolated the offender
            log.error("Offending row: %s", rows[0])
            raise

        mid = len(rows) // 2
        log.warning(
            "IntegrityError in batch of %d rows, bisecting into halves of %d and %d",
            len(rows), mid, len(rows) - mid
        )
        await _execute_with_bisect_on_error(tx, stmt, rows[:mid], log)
        await _execute_with_bisect_on_error(tx, stmt, rows[mid:], log)

async def _insert_hasheous_dump(db: AsyncEngine, metadata: MetaData, db_lock: asyncio.Lock, deduplicator: RowDeduplicator, job: HasheousJob) -> None:
    """Insert a Hasheous dump's already-expanded rows into the database."""
    log = _hasheous_index_log
    loaded = job.loaded
    log.debug("Inserting rows for %d games from %s", len(loaded.game_ids), job.name)

    # One transaction per dump, rather than one per table:
    # most of these tables only receive a handful of rows,
    # and a commit costs far more than the rows themselves.
    async with db_transaction(db, db_lock) as tx:
        for tablename, rows in chain(loaded.rows.objects, loaded.rows.relationships):
            assert tablename in metadata.tables, f"Table '{tablename}' is missing from the metadata"

            # The same game (or company, or signature, or ROM) may appear in several dumps,
            # so skip whatever's already been inserted.
            # Conflicts are still ignored, since a row may have arrived from another data source.
            if unseen := deduplicator.filter(tablename, rows):
                stmt = insert(metadata.tables[tablename]).on_conflict_do_nothing()
                await _execute_with_bisect_on_error(tx, stmt, unseen, log)
                log.debug("Inserted %d of %d rows into %s", len(unseen), len(rows), tablename)

        if playlist_dump_mappings := deduplicator.filter(
            PlaylistDumpMapping.__tablename__,
            ({"playlist": p.title, "dump": job.name} for p in job.playlists),
        ):
            await tx.execute(
                insert(metadata.tables[PlaylistDumpMapping.__tablename__]).on_conflict_do_nothing(),
                playlist_dump_mappings
            )

        if game_dump_mappings := deduplicator.filter(
            GameDumpMapping.__tablename__,
            ({"dump": job.name, "game": game_id} for game_id in loaded.game_ids),
        ):
            await tx.execute(
                insert(metadata.tables[GameDumpMapping.__tablename__]).on_conflict_do_nothing(),
                game_dump_mappings
            )

        await tx.commit()

    log.info("Inserted %d games from %s", len(loaded.game_ids), job.name)


async def index_hasheous(
    *,
    db: AsyncEngine,
    metadata: MetaData,
    db_lock: asyncio.Lock,
    playlists: Iterable[Playlist],
    hasheous_path: DirectoryPath,
    pool: Pool,
    concurrency: int = DEFAULT_HASHEOUS_CONCURRENCY,
    dat_keys_path: Path | None = None,
) -> None:
    """Load and index Hasheous dump data into the database."""
    log = _hasheous_index_log
    playlists = tuple(playlists)

    requested_dumps = set(chain.from_iterable(p.hasheous_dirs for p in playlists)) | {'Unknown Platform'}

    deduplicator = RowDeduplicator(metadata)

    # Loading a dump is much faster than inserting it,
    # so without a limit every archive would be loaded and held in memory
    # long before the database caught up.
    # The limit is released only once a dump's rows have been inserted.
    in_flight = asyncio.Semaphore(concurrency)

    async def chunk(name: str, path: Path, playlists_for_dump: set[Playlist], offset: int) -> None:
        async with in_flight:
            log.debug("Loading %s from game %d", path, offset)
            loaded = await pool.apply(load_zip, (path, dat_keys_path, offset, GAMES_PER_CHUNK))
            log.info(
                "Loaded %d of %d games from %s (from game %d)",
                len(loaded.game_ids), loaded.loaded_games, path, offset
            )
            await _insert_hasheous_dump(
                db, metadata, db_lock, deduplicator,
                HasheousJob(name, playlists_for_dump, loaded)
            )

    async def job(name: str) -> None:
        path = hasheous_path / f"{name}.zip"

        # Read the archive in chunks, so that no single task
        # has to hold a whole dump's worth of rows in memory.
        total = await pool.apply(count_zip_games, (path,))

        # Get all playlists that reference this Hasheous dump
        # (except the implicit "Unknown Platform" dump,
        # but it'll be included if explicitly named)
        referencing_playlists = {p for p in playlists if name in p.hasheous_dirs}

        async with asyncio.TaskGroup() as chunks:
            for offset in range(0, total, GAMES_PER_CHUNK):
                chunks.create_task(
                    chunk(name, path, referencing_playlists, offset),
                    name=f"{name}+{offset}"
                )

        log.info("Finished %s (%d games)", name, total)

    async with asyncio.TaskGroup() as group:
        log.info("Inserting data from %d dump archives", len(requested_dumps))
        for name in requested_dumps:
            group.create_task(job(name), name=name)

    log.info("Finished inserting data")


class IndexSubCommand(BaseModel, PlaylistArgs, IndexArgs, VerboseArgs, PoolArgs):
    hasheous_path: DirectoryPath = Field(
        default=PARENT_DIR / 'tmp' / 'hasheous',
        description="Path to the directory containing Hasheous ZIP dumps fetched with `hasheous.py fetch`.",
        validation_alias=AliasChoices('s', 'hasheous'),
        validate_default=True,
    )

    output: Path = Field(
        default=PARENT_DIR / 'tmp' / 'hasheous.db',
        description="Path to the output SQLite database file.",
        validation_alias=AliasChoices('o', 'output'),
        validate_default=True,
    )

    _db_lock = asyncio.Lock()
    _log = logging.getLogger('hasheous.index')

    async def cli_cmd(self):
        start = time.perf_counter()

        log_handler = logging.StreamHandler()
        log_handler.setFormatter(logging.Formatter('[%(asctime)s][%(name)s][%(taskName)s] %(message)s'))
        sqlalchemy_engine_log = logging.getLogger('sqlalchemy.engine.Engine')
        sqlalchemy_engine_log.addHandler(log_handler)

        self._log.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        self._log.addHandler(log_handler)
        if self.verbose:
            # Log the SQL table creation statements being executed,
            # but we'll lower the level later during data insertion
            # so we don't get overwhelmed with output.
            sqlalchemy_engine_log.setLevel(logging.INFO)

        self.output.parent.mkdir(parents=True, exist_ok=True)

        if self.output.exists() and not self.force:
            raise FileExistsError(f"Output database file '{self.output}' already exists. Use --force to overwrite.")

        # Remove existing database file if it exists
        self.output.unlink(missing_ok=True)

        async with aiofiles.open(self.config, "r") as config_file:
            config = PlaylistConfig.model_validate(tomllib.loads(await config_file.read()))

        if self.playlists:
            playlists = tuple(p for p in config.playlists if p.title in self.playlists)
        else:
            playlists = config.playlists

        # Create async engine with SQLite
        db, metadata = await create_db(self.output, HASHEOUS_OBJECT_TYPES)
        sqlalchemy_engine_log.setLevel(logging.WARNING)

        async with self.create_pool() as pool:
            await index_hasheous(db=db, metadata=metadata, db_lock=self._db_lock, playlists=playlists, hasheous_path=self.hasheous_path, pool=pool)

        self._log.info("Finished inserting data")

        async with db.connect() as connection:
            # Run the SQLite optimizer to improve performance on all tables (0x10000),
            # but don't take too long (0x00010)
            await connection.execute(text("PRAGMA optimize = 0x10012"))

        # Close the engine
        await db.dispose()

        end = time.perf_counter()
        elapsed = timedelta(seconds=end - start)
        self._log.info(f"Elapsed time: %s", elapsed)

class HasheousCommand(BaseSettings):
    fetch: CliSubCommand[FetchSubCommand]
    submit: CliSubCommand[SubmitSubCommand]
    index: CliSubCommand[IndexSubCommand]
    model_config = SettingsConfigDict(
        case_sensitive=False,
        cli_avoid_json=True,
        cli_implicit_flags=True,
        cli_kebab_case=True,
        cli_parse_args=True,
        extra="ignore",
    )

    def cli_cmd(self) -> None:
        CliApp.run_subcommand(self)


__all__ = (
    "Attribute",
    "DataObject",
    "DataObjectType",
    "HasheousConfig",
    "HasheousId",
    "HASHEOUS_OBJECT_TYPES",
    "index_hasheous",
    "load_zip",
    "MappingStatus",
    "MatchMethodType",
    "MatchRecord",
    "MediaType",
    "METADATA_MAP_URL",
    "MetadataItem",
    "RomItem",
    "SignatureDataObject",
)

if __name__ == "__main__":
    CliApp.run(HasheousCommand)
