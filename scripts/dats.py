#!/usr/bin/env python3

import asyncio
import logging
import re
import sys
import time
import tomllib

from abc import ABC
from collections.abc import Collection, Iterable, Iterator, Sequence
from datetime import timedelta
from functools import cache
from io import StringIO
from itertools import chain, repeat, product
from os import PathLike
from pathlib import Path
from typing import IO, Annotated, Any, BinaryIO, ClassVar, Literal, LiteralString, NamedTuple, Self, TextIO, TypedDict

import aiofiles
import aioitertools.builtins as aiobuiltins
import aiofiles.ospath as aiopath
import pe

from aiomultiprocess import Pool
from frozendict import frozendict
from more_itertools import map_reduce, partition, prepend
from pe.actions import Pack
from pe.operators import Class, Star
from pydantic import AfterValidator, AliasChoices, BaseModel, ByteSize, DirectoryPath, Field, FilePath, GetPydanticSchema, ModelWrapValidatorHandler, OnErrorOmit, RootModel, TypeAdapter, ValidationInfo, computed_field, model_validator
from pydantic_core import from_json, core_schema
from pydantic_settings import BaseSettings, CliApp, CliPositionalArg, CliSubCommand, SettingsConfigDict
from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, MetaData, column, select, text
from sqlalchemy.dialects.sqlite import JSON, insert
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.sql.functions import coalesce

from playlist import Playlist, PlaylistArgs, PlaylistConfig, PlaylistTitle
from sqlite import DatabaseModel, Relationship, RowId, RowIdColumn, create_db, db_transaction
from utils import CliTuple, Crc, DEFAULT_DAT_CONCURRENCY, EmptyStringToNone, FrozenDict, IndexArgs, Md5, OnlyFirst, PoolArgs, Sha1, VerboseArgs

type DatValidationMode = Literal['dat'] | None
type DatPair = tuple[str, DatValue]
type DatRecord = tuple[DatPair, ...]
type DatValue = str | DatRecord
type DatTopLevelRecord = tuple[str, DatRecord]
type DatFile = tuple[DatTopLevelRecord, ...]

class DatModel(DatabaseModel, ABC, frozen=True, extra="allow", str_strip_whitespace=True, validate_by_name=True):
    __dattype__: ClassVar[LiteralString]

    @computed_field(
        return_type=Annotated[FrozenDict[str, Any] | None, Column(JSON(none_as_null=True), nullable=True)],
        repr=False,
    )
    @property
    def extra(self) -> frozendict[str, Any] | None:
        """
        A computed field that gathers any extra fields not defined in the model
        into a dictionary. This allows us to preserve unrecognized fields from the DAT file
        without losing them during validation.
        """
        return frozendict(self.model_extra) if self.model_extra else None

    @classmethod
    def from_dat(cls, value: DatRecord | DatTopLevelRecord) -> Self:
        return cls.model_validate(value, context="dat")

    def to_dat(self) -> DatRecord:
        """
        Returns this record as DAT pairs; the inverse of `from_dat`.

        Declared fields come first, under their serialization aliases, followed by extra fields.
        Nested records come after both, so that e.g. a `game` ends with its `rom`s.
        Fields that are None are left out.
        """
        declared = ((key, getattr(self, name)) for name, key in self._dat_keys())
        fields = chain(declared, (self.model_extra or {}).items())
        pairs = [pair for key, value in fields if value is not None for pair in _dat_pairs(key, value)]
        return tuple(sorted(pairs, key=_is_record))

    @classmethod
    @cache
    def _dat_keys(cls) -> tuple[tuple[str, str], ...]:
        """Returns each declared field's name, and the key that `to_dat` writes it under."""
        return tuple((name, info.serialization_alias or name) for name, info in cls.model_fields.items())

    @model_validator(mode="wrap")
    @classmethod
    def validate_dat(cls, data: Any, handler: ModelWrapValidatorHandler[Self], info: ValidationInfo) -> Self:
        """
        If the validation context is 'dat', construct the object from a DAT record.
        """
        if info.context != 'dat':
            return handler(data)

        match data:
            case str(type) | (str(type), [*_]) if type != cls.__dattype__:
                # A DAT key or keyed DatRecord with an unexpected type
                raise ValueError(f"Expected a DAT type of {cls.__dattype__}, got {type}")
            case str(), str():
                # A DatPair with a string value
                return handler(data)
            case (str(), [*pairs]) | [*pairs]:
                # A DatRecord with multiple DatPairs, possibly as a top-level record
                datdict: dict[str, tuple[DatValue, ...]] = map_reduce(
                    (p for p in pairs if isinstance(p, tuple) and len(p) == 2),
                    lambda pair: str(pair[0]), # the DAT pair type
                    lambda pair: pair[1], # the DAT pair value
                    lambda vals: vals[0] if len(vals) == 1 and not isinstance(vals[0], tuple) else tuple(v for v in vals),
                )
                return handler(datdict)
            case _:
                # Handle other cases normally
                return handler(data)

def _dat_pairs(key: str, value: Any) -> Iterator[DatPair]:
    """
    Encodes one field of a `DatModel` as DAT pairs.

    A sequence becomes one pair per item, the way a `game` lists each of its `rom`s.
    """
    match value:
        case str():
            yield key, value
        case bool():
            yield key, "1" if value else "0"
        case DatModel():
            yield key, value.to_dat()
        case None:
            return
        case [(str(), _), *_]:
            # A nested record that `from_dat` kept as-is among the extra fields
            yield key, value
        case [*items]:
            for item in items:
                yield from _dat_pairs(key, item)
        case _:
            yield key, str(value)

def _is_record(pair: DatPair) -> bool:
    return isinstance(pair[1], tuple)

def _split_for_retroarch_validator(value: str) -> tuple[str, ...]:
    """
    Split the string by commas, pipes, or slashes, matching RetroArch's logic.

    Rules:
    - Strip whitespace before and after each segment
    - Don't treat corporate suffixes (e.g. ", Inc." or ", Ltd." or ", The") as separators

    Matches logic from:
    https://github.com/libretro/RetroArch/blob/master/menu/menu_explore.c#L272
    """
    import re

    if not value or not value.strip():
        return ()

    # Split on delimiters that are NOT preceded by a corporate suffix.
    # The pattern uses a negative lookbehind to exclude commas that follow suffixes.
    # For slashes and pipes, we always split (they're not used with company names).
    pattern = r'\s*(?:(?<=\.)(?=\s*[,/|])|(?<!\s(?:Inc|Ltd|The)\.?))\s*[,/|]\s*'

    # Split and filter out empty strings
    segments = [seg.strip() for seg in re.split(pattern, value, re.IGNORECASE) if seg.strip()]

    return tuple(segments)

RetroArchStringTuple = Annotated[tuple[str, ...], AfterValidator(_split_for_retroarch_validator)]

class ClrMamePro(DatModel, frozen=True):
    __tablename__ = "DatClrMamePro"
    __dattype__ = "clrmamepro"

    rowid: RowIdColumn
    name: str
    description: str | None = None
    category: str | None = None
    date: str | None = None
    author: str | None = None
    email: str | None = None
    url: str | None = None
    version: str | None = None
    comment: str | None = None
    homepage: str | None = None

class RomId(TypedDict, total=False):
    crc: Crc | None
    serial: str | None
    md5: Md5 | None
    sha1: Sha1 | None

class Rom(DatModel, frozen=True):
    __tablename__ = "DatRom"
    __dattype__ = "rom"
    __tableargs__ = (
        CheckConstraint("crc NOT NULL OR serial NOT NULL", name="ix_DatRom_has_retroarch_id"),
        Index("ix_DatRom", "crc", "serial", "md5", "sha1", unique=True),
        Index("ix_DatRom_name_where_not_null", "name", sqlite_where=column("name").is_not(None)),
        Index("ix_DatRom_crc_where_not_null", "crc", sqlite_where=column("crc").is_not(None), unique=True),
        Index("ix_DatRom_serial_where_not_null", "serial", sqlite_where=column("serial").is_not(None)),
    )

    rowid: RowIdColumn
    name: Annotated[str | None, Field(validation_alias=AliasChoices("name", "image"))] = None
    crc: Annotated[Crc | None, Column(CheckConstraint("crc IS NULL OR length(crc) = 8"), unique=True)] = None
    serial: str | None = None
    md5: Annotated[Md5 | None, Column(CheckConstraint("md5 IS NULL OR length(md5) = 32"), unique=True, index=True)] = None
    sha1: Annotated[Sha1 | None, Column(CheckConstraint("sha1 IS NULL OR length(sha1) = 40"), unique=True, index=True), Field(validation_alias=AliasChoices("sha1", "sha1sum"))] = None
    size: ByteSize | None = None

class Game(DatModel, frozen=True):
    """
    A parsed and unmarshalled game record from a DAT file.

    Unrecognized fields are kept as extra fields, and written back out by `to_dat`.
    Add a field to this class to give it a type and a database column.

    At least one of `name`, `description`, `comment`, or `id` should be present.
    """
    __tablename__ = "DatGame"
    __dattype__ = "game"
    __tableconstraints__ = (
        CheckConstraint("name IS NOT NULL OR description IS NOT NULL OR comment IS NOT NULL OR id IS NOT NULL", name="chk_game_at_least_one_identifier"),
    )

    rowid: RowIdColumn

    # Declared first so that `to_dat` writes it first;
    # not semantically important, but easier to read.
    name: str | None = None

    analog: bool | None = None
    comment: OnlyFirst[str] | None = None
    description: str | None = None
    developer: str | None = None
    """May include multiple developers separated by commas, slashes, or pipes"""

    franchise: str | None = None

    genre: str | None = None
    """May include multiple genres separated by commas, slashes, or pipes."""

    id: str | None = None

    manufacturer: str | None = None
    """May include multiple media types separated by commas, slashes, or pipes."""

    publisher: str | None = None
    """May include multiple publishers separated by commas, slashes, or pipes."""

    region: str | None = None
    releaseday: int | None = None
    releasemonth: int | None = None
    releaseyear: EmptyStringToNone[int] = None
    rumble: bool | None = None
    tags: str | None = None
    users: int | None = None

    roms: Annotated[tuple[Rom, ...], Field(alias="rom"), Relationship(
        self_columns={"rowid": Column("game", ForeignKey("DatGame.rowid"), primary_key=True)},
        related_columns=({
            # The field names don't map 1:1 with column names,
            # so we specify the field names explicitly as keys
            "crc": Column(
                "crc",
                ForeignKey("DatRom.crc"),
                CheckConstraint("crc IS NULL OR length(crc) = 8"),
                nullable=True,
                unique=True,
                primary_key=True,
            ),
            "serial": Column("serial", ForeignKey("DatRom.serial"), nullable=True, primary_key=True),
            "md5": Column(
                "md5",
                ForeignKey("DatRom.md5"),
                CheckConstraint("md5 IS NULL OR length(md5) = 32"),
                nullable=True,
                unique=True,
                index=True,
                primary_key=True,
            ),
            "sha1": Column(
                "sha1",
                ForeignKey("DatRom.sha1"),
                CheckConstraint("sha1 IS NULL OR length(sha1) = 40"),
                nullable=True,
                unique=True,
                index=True,
                primary_key=True,
            ),
        }),
        tableargs=(
            CheckConstraint("crc NOT NULL OR serial NOT NULL", name="chk_game_rom_mapping_retroarch_id"),
            Index("ix_DatGame_roms", "crc", "serial", "md5", "sha1"),
            Index("ix_DatGame_crc_where_not_null", "crc", sqlite_where=column("crc").is_not(None), unique=True),
            Index("ix_DatGame_serial_where_not_null", "serial", sqlite_where=column("serial").is_not(None)),
            Index("ix_DatGame_md5_where_not_null", "md5", sqlite_where=column("md5").is_not(None), unique=True),
            Index("ix_DatGame_sha1_where_not_null", "sha1", sqlite_where=column("sha1").is_not(None), unique=True)
        ),
        tablekwargs=None,
        # Unlike most other relationship tables in this project,
        # this one isn't WITHOUT ROWID because some columns of the primary key are nullable.
    )] = ()

    @computed_field(return_type=Annotated[tuple[RomId, ...], Column(JSON, nullable=False)])
    @property
    def romids(self):
        """Rom IDs"""
        return tuple(RomId(**r.model_dump(include={"crc", "serial", "md5", "sha1"})) for r in self.roms)


class PlaylistGameMapping(DatabaseModel, frozen=True):
    __tablename__ = "DatPlaylistGameMapping"
    __tablekwargs__ = frozendict({"sqlite_with_rowid": False})

    playlist: Annotated[PlaylistTitle, Column(primary_key=True, index=True)]
    game: Annotated[RowId, Column(ForeignKey("DatGame.rowid"), primary_key=True, index=True)]

# PEG grammar for DAT file format
DAT_GRAMMAR = r'''
# Main entry points
DatFile < DatTopLevelRecord* EndOfFile

# Record structure
DatTopLevelRecord < type:DatString Open DatRecord Close
DatRecord < DatPair*
DatPair < key:DatString value:DatValue
DatValue < Open DatRecord Close / DatString

# Tokens
DatString <- !Open !Close (QuotedString / UnquotedString)
QuotedString <- ["] ~((![\r\n"] .)*) ["]?
UnquotedString <- ~((![ \t\r\n"] .)+)

# Parentheses only count as such when they're whole tokens, quoted or not
Open <- "(" &TokenEnd / ["] "(" (["] / &EndOfLine / EndOfFile)
Close <- ")" &TokenEnd / ["] ")" (["] / &EndOfLine / EndOfFile)
TokenEnd <- [ \t\r\n"] / EndOfFile

# Whitespace
EndOfLine <- [\r\n]
EndOfFile <- !.
'''
"""
There's no formal spec for DAT files,
so this grammar reads them the way RetroArch's `c_converter` does,
since that's the program that compiles them into `.rdb` files.
See `dat_converter_lexer` and `dat_parser_table` in
https://github.com/libretro/RetroArch/blob/master/libretro-db/c_converter.c

These are the semantics:

- A DatValue is either a string or a DatRecord.
- A DatPair is a key (any string) followed by a DatValue.
- A DatRecord is an ordered sequence of zero or more DatPairs.
- A DatRecord may have multiple pairs with the same key.
  The application may interpret this as a list of values for that key,
  though `c_converter` merges them instead (see `compile_dats`).
- A DatFile is a DatRecord where all DatValues are DatRecords.

This is the syntax:

- Tokens are separated by spaces, tabs, and line breaks.
- A double quote also ends a token, and starts or ends a quoted string.
- Quoted strings end at the next double quote or line break, whichever comes first.
  There are no escape sequences, so `\"` is a backslash that ends the string.
- A parenthesis only opens or closes a DatRecord if it's a whole token by itself.
  A quoted `"("` or `")"` counts too, since `c_converter` compares tokens without regard to quotes.
  Otherwise, parentheses are ordinary characters (e.g. `(abc` is a single token).
- DatFiles are not wrapped in parentheses.
- DatRecords are wrapped in parentheses.

We don't try to interpret the meaning of any keys or values while parsing;
this means we just treat everything as a string,
and let the unmarshalling step figure out what to do with it.
Run `python scripts/dats.py check` to find DAT files that don't parse.
"""

def build_top_level_record(pairs: tuple[DatPair, ...], type: str) -> DatTopLevelRecord:
    return (type, pairs)

def build_pair(key: str, value: DatValue) -> DatPair:
    return (key, value)

# Actions for semantic processing
ACTIONS = {
    'DatTopLevelRecord': build_top_level_record,
    'DatRecord': Pack(tuple), # Wrap all DatPairs into a tuple
    'DatPair': build_pair, # Wrap the parsed values (bound to "key" and "value") into a DatPair
    'DatFile': Pack(tuple), # Wrap all DatTopLevelRecords into a tuple
}

dat_parser = pe.compile(DAT_GRAMMAR, actions=ACTIONS, ignore=Star(Class(" \t\r\n")), flags=pe.OPTIMIZE | pe.MEMOIZE | pe.STRICT)

def encode_dat_string(value: str) -> str:
    """
    Quotes a string so that `c_converter` (and `dat_parser`) read it back unchanged.

    DAT files have no escape sequences,
    and a quoted string ends at the next double quote or line break,
    so neither can be represented;
    double quotes become single quotes, and line breaks become spaces.
    """
    return '"' + re.sub(r'[\r\n]+', ' ', value).replace('"', "'") + '"'

def encode_dat(dat: DatFile, output: IO | None = None):
    if not output:
        output = StringIO()

    def write_pair(pair: DatPair, indent: int = 0) -> None:
        match pair:
            case (key, str(value)):
                # leaf-level DAT pair (like a ROM name)
                output.write('\t' * indent)
                output.write(key)
                output.write(' ')
                output.write(encode_dat_string(value))
                output.write('\n')
            case (key, [*pairs]) if indent > 0 and all(isinstance(v, str) for _, v in pairs):
                # nested DAT record without records of its own (usually a rom), on one line
                output.write('\t' * indent)
                output.write(key)
                output.write(' ( ')
                for k, v in pairs:
                    output.write(k)
                    output.write(' ')
                    output.write(encode_dat_string(v))
                    output.write(' ')
                output.write(')\n')
            case (key, [*pairs]):
                # nested DAT record (usually a game or clrmamepro)
                output.write('\t' * indent)
                output.write(key)
                output.write(' (\n')
                for p in pairs:
                    write_pair(p, indent + 1) # type: ignore
                    # p is definitely a DatPair but the type checker says otherwise
                output.write('\t' * indent)
                output.write(')\n')
            case _:
                raise TypeError(f"Cannot encode {pair} of type {type(pair)}")

    for pair in dat:
        write_pair(pair)
        output.write('\n')


def to_dat(value: DatFile) -> str:
    output = StringIO()
    encode_dat(value, output)
    return output.getvalue()

class ParsedDatFile(RootModel, frozen=True):
    """
    A DAT file, as a tuple starting with a ClrMamePro record followed by zero or more Game records.
    """
    root: Annotated[
        tuple[ClrMamePro, *tuple[Game, ...]],
        GetPydanticSchema(
            lambda tp, handler: core_schema.tuple_schema(
                items_schema=[
                    handler.generate_schema(ClrMamePro),  # first item
                    handler.generate_schema(OnErrorOmit[Game]),        # repeated item
                ],
                variadic_item_index=1,  # repeat schema at index 1
                min_length=1,           # must have at least the first item
            )
        )
    ]
    """
    Pydantic doesn't seem to generate schemae for unpacked tuples,
    so we have to define it ourselves.

    See https://github.com/pydantic/pydantic/issues/5952 for the issue,
    and https://stackoverflow.com/a/79877584/1089957 for the workaround's details.

    Once Unpack is supported properly, we can omit the GetPydanticSchema handler above.
    """

    @property
    def clrmamepro(self) -> ClrMamePro:
        """The ClrMamePro record of this DAT file, which contains metadata about the DAT."""
        return self.root[0]

    @property
    def games(self) -> tuple[Game, ...]:
        """The Game records of this DAT file, which contain the actual game data."""
        return self.root[1:] if len(self.root) > 1 else ()

    def to_dat(self) -> DatFile:
        """Returns this DAT file's records, ready for `encode_dat`."""
        return tuple((record.__dattype__, record.to_dat()) for record in self.root)

    @classmethod
    async def from_dat_file_async(cls, dat: PathLike) -> Self:
        """
        Load and parse a DAT file asynchronously from the given path.
        Raises or returns errors based on the `errors` parameter.
        """
        async with aiofiles.open(dat, 'r', encoding='utf-8') as dat_file:
            dat_content = await dat_file.read()

        raw_dat = load_dat(dat_content)

        return cls.model_validate(raw_dat, context="dat")

    @classmethod
    async def from_dat_file_async_or_error(cls, dat: PathLike) -> Self | Exception:
        try:
            return await cls.from_dat_file_async(dat)
        except Exception as e:
            return e

DAT_OBJECT_TYPES = (
    Game,
    Rom,
    ClrMamePro,
    PlaylistGameMapping,
)

def load_dat(dat: str | bytes | PathLike | TextIO | BinaryIO) -> DatRecord:
    """
    Loads a DAT file from disk, memory, or a file-like object and parses it into a DatRecord.
    """
    match dat:
        case str():
            dat_content = dat
        case bytes():
            dat_content = dat.decode('utf-8')
        case PathLike() as p:
            with open(p, 'r', encoding='utf-8') as dat_file:
                dat_content = dat_file.read()
        case TextIO() as f:
            dat_content = f.read()
        case BinaryIO() as f:
            dat_content = f.read().decode('utf-8')
        case _:
            raise TypeError(f"Expect a str, bytes, PathLike, TextIO, or BinaryIO, got {type(dat)}")

    match_result = dat_parser.match(dat_content, flags=pe.MEMOIZE | pe.OPTIMIZE | pe.STRICT | pe.INLINE)
    if match_result is None:
        raise ValueError("Failed to parse DAT string")

    result = match_result.value()
    assert result is not None
    return result

type DatTable = dict[str, "str | DatTable"]
"""
A DatRecord whose repeated keys were merged the way `c_converter` merges them.

A key that appears more than once doesn't become a list.
Instead, if both values are records, the later one is merged into the earlier one;
otherwise the later value replaces the earlier one,
unless the earlier value is a record and the later one is a string,
in which case the string is dropped.
This is why a game with several `rom` records ends up with the hashes of its last ROM.
"""

class CompiledEntry(NamedTuple):
    """One entry of an `.rdb` file, as `c_converter` would compile it."""

    game: DatTable
    """The entry after merging every game record that shares its key, across all source files."""

    roms: tuple[DatTable, ...]
    """Every `rom` record listed under this entry's key, before they were merged."""

def _merge_dat_value(table: DatTable, key: str, value: "str | DatTable") -> None:
    existing = table.get(key)

    if isinstance(existing, dict):
        if isinstance(value, dict):
            for k, v in value.items():
                _merge_dat_value(existing, k, v)
        # A string never replaces a record
    else:
        table[key] = value

def _to_dat_table(record: DatRecord, roms: list[DatTable] | None = None) -> DatTable:
    """
    :param roms: If given, every `rom` record is also appended here,
      before it's merged with its siblings.
    """
    table: DatTable = {}
    for key, value in record:
        if isinstance(value, tuple):
            value = _to_dat_table(value)
            if roms is not None and key == "rom":
                roms.append(dict(value))

        _merge_dat_value(table, key, value)

    return table

def get_dat_match(table: DatTable, match_key: str) -> str | None:
    """
    Looks up a dotted key like `rom.crc` the way `c_converter` does.
    """
    value: str | DatTable | None = table
    for part in match_key.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)

    return value if isinstance(value, str) else None

def compile_dats(paths: Iterable[PathLike], match_key: str) -> dict[str, CompiledEntry]:
    """
    Parses and merges DAT files the way `c_converter` does when it compiles them into one `.rdb`.

    Only `game` records become entries.
    Each is identified by its value of `match_key`,
    and games that share one are merged into a single entry (see `DatTable`),
    with later files taking precedence over earlier ones.

    `c_converter` has one more quirk that this reproduces:
    the first time a file has a game without the match key,
    the loop that prints the warning also advances the match key to its last component.
    So for the rest of that file, games are matched by e.g. a game-level `serial`
    instead of `rom.serial`.
    The match key is reset for the next file.

    :param match_key: The field that identifies each entry, like `rom.crc` or `rom.serial`.
      Games without it are dropped, as `c_converter` drops them.
    :return: Each entry in the resulting `.rdb`, keyed by its value of `match_key`
      exactly as written in the DAT file (i.e. case-sensitively).
    """
    games: dict[str, DatTable] = {}
    roms: dict[str, list[DatTable]] = {}

    for path in paths:
        # c_converter reads bytes, so don't fail on the odd DAT file that isn't valid UTF-8
        dat = load_dat(Path(path).read_bytes().decode("utf-8", errors="surrogateescape"))
        file_match_key = match_key

        for type, record in dat:
            if type != "game":
                continue

            game_roms: list[DatTable] = []
            table = _to_dat_table(record, game_roms)

            if (key := get_dat_match(table, file_match_key)) is None:
                file_match_key = file_match_key.rsplit(".", 1)[-1]
                continue

            _merge_dat_value(games, key, table)
            roms.setdefault(key, []).extend(game_roms)

    return {key: CompiledEntry(game, tuple(roms[key])) for key, game in games.items() if isinstance(game, dict)}

async def compile_dats_async(paths: Iterable[PathLike], match_key: str) -> dict[str, CompiledEntry]:
    """`compile_dats` as a coroutine, for running in an `aiomultiprocess.Pool`."""
    return compile_dats(paths, match_key)

class CheckSubCommand(BaseModel, VerboseArgs):
    """Check DAT files for valid syntax."""

    dat_paths: CliPositionalArg[list[FilePath | DirectoryPath]] = Field(
        default=(Path(__file__).parent.parent / 'dat', Path(__file__).parent.parent / 'metadat'),
        description="Paths to directories containing DAT files to check.",
        validate_default=True,
    )

    check_models: bool = Field(
        default=False,
        description="If set, check that all DATs can be validated as Pydantic models. Otherwise just check syntax.",
        validation_alias=AliasChoices('m', 'models'),
    )

    @staticmethod
    async def check_dat_async(dat_path: Path, check_models: bool, verbose: bool) -> Exception | None:
        try:
            async with aiofiles.open(dat_path, 'r', encoding='utf-8') as dat_file:
                dat_content = await dat_file.read()

            match_result = dat_parser.match(dat_content, flags=pe.MEMOIZE | pe.OPTIMIZE | pe.STRICT | pe.INLINE)
            if not match_result:
                raise ValueError("Failed to parse DAT file")

            parsed_value = match_result.value()
            if not check_models:
                if verbose and parsed_value is not None:
                    print(f"Valid DAT file: {dat_path}")
                return None

            if not isinstance(parsed_value, Sequence):
                raise TypeError(f"Unexpected parsed DAT value: {type(parsed_value)}")

            if len(parsed_value) == 0:
                raise ValueError("DAT file is empty")

            parsed_datfile = await ParsedDatFile.from_dat_file_async(dat_path)

            # Validate as Pydantic models
            if verbose:
                print(f"Valid DAT file with models: {dat_path} ({len(parsed_datfile.root) - 1} games)")
        except Exception as e:
            print(f"Failed to load DAT file {dat_path}: {e}", file=sys.stderr)
            return e

    async def cli_cmd(self) -> None:
        files, dirs = partition(Path.is_dir, self.dat_paths)
        child_files = filter(Path.is_file, chain.from_iterable(p.rglob('*.dat') for p in dirs))
        paths = {p for p in chain(files, child_files) if 'xml' not in p.name.lower()}
        async with Pool() as pool:
            jobs = zip(paths, repeat(self.check_models), repeat(self.verbose))
            result = await pool.starmap(CheckSubCommand.check_dat_async, tuple(jobs))
            if errors := tuple(e for e in result if e is not None):
                raise ExceptionGroup(f"{len(errors)} DAT files failed to load or validate.", errors)

class ToJsonSubCommand(BaseModel):
    """
    Convert a DAT file to equivalent JSON.
    """

    infile: CliPositionalArg[Path | None] = Field(
        default=None,
        description="Path to the input DAT file, or stdin if not provided."
    )

    async def cli_cmd(self) -> None:
        import json

        if self.infile:
            async with aiofiles.open(self.infile, 'rb') as infile:
                dat_contents = await infile.read()
        else:
            dat_contents = await aiofiles.stdin_bytes.read()

        dat = load_dat(dat_contents)
        json.dump(dat, sys.stdout, indent=2, ensure_ascii=False)

class FromJsonSubCommand(BaseModel):
    infile: CliPositionalArg[Path | None] = Field(
        default=None,
        description="Path to the input JSON file, or stdin if not provided."
    )

    encoding: str = Field(
        default='utf-8',
        description="Encoding of the input JSON file."
    )

    async def cli_cmd(self) -> None:
        if self.infile:
            async with aiofiles.open(self.infile, 'r', encoding=self.encoding) as infile:
                json_contents = await infile.read()
        else:
            json_contents = await aiofiles.stdin.read()

        dat = from_json(json_contents)
        encode_dat(dat, sys.stdout)

PARENT_DIR = Path(__file__).parent.parent

class LoadedDat(NamedTuple):
    """
    One DAT file expanded into database rows.

    The rows are built in a worker process, since turning models into rows
    costs much more than handing the finished rows to SQLite.
    """

    games: tuple[dict[str, Any], ...]
    """Rows for `DatGame`, in the order their ROM lists are returned."""

    roms: tuple[dict[str, Any], ...]
    """Rows for `DatRom`, deduplicated within this DAT file."""


async def load_dat_file(path: Path) -> LoadedDat:
    """Loads one DAT file and expands it into database rows."""
    datfile = await ParsedDatFile.from_dat_file_async(path)
    games = datfile.games

    # The same ROM is often listed by several games in one DAT file,
    # and DatRom's hashes are unique, so collapse them before they reach the database.
    roms: dict[tuple[Any, ...], dict[str, Any]] = {}
    for rom in chain.from_iterable(g.roms for g in games):
        roms.setdefault((rom.crc, rom.serial, rom.md5, rom.sha1), rom.as_row)

    return LoadedDat(
        games=tuple(g.as_row for g in games),
        roms=tuple(roms.values()),
    )


class LoadJobResult(NamedTuple):
    playlist: Playlist
    path: Path
    loaded: LoadedDat

    @property
    def games(self) -> tuple[dict[str, Any], ...]:
        return self.loaded.games


_dats_index_log = logging.getLogger('dats.index')



class GameRomMapping(RomId):
    game: RowId

async def _insert_dat_file(db: AsyncEngine, metadata: MetaData, db_lock: asyncio.Lock, dat: LoadJobResult) -> None:
    """Insert a parsed DAT file's rows into the database."""
    log = _dats_index_log
    loaded = dat.loaded

    game_table = metadata.tables[Game.__tablename__]
    rom_table = metadata.tables[Rom.__tablename__]
    mapping_table = metadata.tables[f"{Game.__tablename__}_roms"]
    playlist_table = metadata.tables[PlaylistGameMapping.__tablename__]

    insert_roms = insert(rom_table)
    insert_mapping = insert(mapping_table)

    # One transaction for the whole DAT file.
    # The games have to go in first so that their rowids can be used
    # to link each game to the ROMs it lists.
    async with db_transaction(db, db_lock) as tx:
        inserted_games = await tx.execute(
            insert(game_table).returning(game_table.c.rowid, game_table.c.romids),
            loaded.games
        )
        game_rows = inserted_games.mappings().all()
        log.debug("Inserted %d games", len(game_rows))

        game_rom_mappings = [
            GameRomMapping(game=game.rowid, **rom)
            for game in game_rows
            for rom in game.romids
        ]

        if game_rom_mappings:
            # See Rom.__tableargs__ for the table definition
            await tx.execute(
                insert_mapping.on_conflict_do_update(set_={
                    "crc": coalesce(mapping_table.columns.crc, insert_mapping.excluded.crc),
                    "md5": coalesce(mapping_table.columns.md5, insert_mapping.excluded.md5),
                    "serial": coalesce(mapping_table.columns.serial, insert_mapping.excluded.serial),
                    "sha1": coalesce(mapping_table.columns.sha1, insert_mapping.excluded.sha1),
                }),
                game_rom_mappings
            )
            log.debug("Inserted %d game-ROM mappings", len(game_rom_mappings))
        else:
            log.warning("No game-ROM mappings to insert")

        if game_playlist_mappings := [{"playlist": dat.playlist.title, "game": game.rowid} for game in game_rows]:
            await tx.execute(
                insert(playlist_table).on_conflict_do_nothing(),
                game_playlist_mappings
            )
            log.debug("Inserted %d game-playlist mappings", len(game_playlist_mappings))
        else:
            log.warning("No game-playlist mappings to insert")

        if loaded.roms:
            # The same ROM is often represented in multiple DAT files,
            # so we merge ROM records on conflict instead of skipping or replacing them.
            # The first non-null value for each field is preserved
            await tx.execute(
                insert_roms.on_conflict_do_update(set_={
                    "crc": coalesce(rom_table.columns.crc, insert_roms.excluded.crc),
                    "md5": coalesce(rom_table.columns.md5, insert_roms.excluded.md5),
                    "name": coalesce(rom_table.columns.name, insert_roms.excluded.name),
                    "serial": coalesce(rom_table.columns.serial, insert_roms.excluded.serial),
                    "sha1": coalesce(rom_table.columns.sha1, insert_roms.excluded.sha1),
                    "size": coalesce(rom_table.columns.size, insert_roms.excluded.size),
                }),
                loaded.roms
            )
            log.debug("Inserted %d ROMs", len(loaded.roms))
        else:
            log.warning("No ROMs to insert")

        await tx.commit()

    log.info("Inserted %d games from %s", len(game_rows), dat.path)


DAT_KEY_TABLE = "DatRomKey"
"""The single table in the key index written by `write_dat_key_index`."""


async def write_dat_key_index(db: AsyncEngine, metadata: MetaData, path: Path) -> Path:
    """
    Writes every identifier that the DAT files describe to a small standalone database.

    Other data sources are far larger than the DAT files
    but only matter where they overlap with them,
    so they use this to discard entries that no DAT file could ever refer to.
    It's a separate file rather than a table in the index
    because the worker processes read it while the index itself is still being written.

    All four identifier kinds share one column.
    A serial that happens to look like a CRC would keep one extra row, which is harmless;
    what matters is that nothing a DAT file mentions is ever missing.

    :param path: Where to write the key index. Overwritten if it already exists.
    :return: `path`, for convenience.
    """
    log = _dats_index_log
    datrom = metadata.tables[Rom.__tablename__]

    path.unlink(missing_ok=True)
    keys = create_async_engine(f"sqlite+aiosqlite:///{path}")

    async with keys.begin() as tx:
        await tx.execute(text(f'CREATE TABLE "{DAT_KEY_TABLE}" (value TEXT PRIMARY KEY) WITHOUT ROWID'))
        await tx.commit()

    async with db.connect() as source:
        # Read every identifier out of the index in one pass per column.
        values = set()
        for column in (datrom.c.crc, datrom.c.md5, datrom.c.sha1, datrom.c.serial):
            result = await source.stream(select(column).where(column.is_not(None)).distinct())
            async for (value,) in result:
                values.add(value)

    async with keys.begin() as tx:
        await tx.execute(
            text(f'INSERT OR IGNORE INTO "{DAT_KEY_TABLE}" (value) VALUES (:value)'),
            [{"value": v} for v in values]
        )
        await tx.commit()

    await keys.dispose()
    log.info("Wrote %d DAT identifiers to %s", len(values), path)
    return path


async def index_dats(
    *,
    db: AsyncEngine,
    metadata: MetaData,
    db_lock: asyncio.Lock,
    playlists: Collection[Playlist],
    dat_dirs: tuple[DirectoryPath, ...],
    pool: Pool,
    concurrency: int = DEFAULT_DAT_CONCURRENCY,
) -> None:
    """Load and index DAT files into the database."""
    log = _dats_index_log

    # Recursively find all subdirectories of the requested DAT directories
    nested_dat_paths = chain.from_iterable(p.rglob("*") for p in dat_dirs)
    dat_subdirs = await aiobuiltins.tuple(p for p in nested_dat_paths if await aiopath.isdir(p))
    all_dat_dirs = tuple(chain(dat_dirs, dat_subdirs))

    async def get_dat_paths(playlist: Playlist) -> tuple[Path, ...]:
        # Use the name of the playlist and the alt names to find existing DAT files
        dat_names = prepend(str(playlist.title), playlist.alts)

        # Check for playlists of these names in all requested DAT directories
        dat_paths = (d / f'{n}.dat' for d, n in product(all_dat_dirs, dat_names))

        # HACK: Some XML files have a `.dat` extension, filter them out
        dat_paths = filter(lambda p: 'xml' not in p.name.lower(), dat_paths)
        return await aiobuiltins.tuple(p for p in dat_paths if await aiopath.exists(p))

    dat_paths = {p: await get_dat_paths(p) for p in playlists}

    log.debug("Loading games from %d playlists", len(playlists))

    # Loading a DAT file is much faster than inserting it,
    # so without a limit every file would be loaded and held in memory
    # long before the database caught up.
    # The limit is released only once a file's rows have been inserted.
    in_flight = asyncio.Semaphore(concurrency)

    async def job(playlist: Playlist, path: Path) -> None:
        async with in_flight:
            log.debug("Loading")
            loaded = await pool.apply(load_dat_file, args=(path,))
            log.info("Loaded with %d games", len(loaded.games))

            if not loaded.games:
                log.warning("DAT file %s has no games, skipping database insertion", path)
                return

            await _insert_dat_file(db, metadata, db_lock, LoadJobResult(playlist, path, loaded))

    async with asyncio.TaskGroup() as group:
        for playlist in playlists:
            for path in dat_paths[playlist]:
                group.create_task(job(playlist, path), name=f"{path}")

    log.info("Finished inserting data")


class IndexSubCommand(BaseModel, VerboseArgs, PlaylistArgs, IndexArgs, PoolArgs):
    dat_dirs: CliTuple[DirectoryPath] = Field(
        default=(PARENT_DIR / 'dat', PARENT_DIR / 'metadat',),
        description="Paths to the directories containing existing DAT files to scan for games to process.",
        validation_alias=AliasChoices('d', 'dat'),
        validate_default=True,
    )

    output: Path = Field(
        default=PARENT_DIR / 'tmp' / 'dats.db',
        description="Path to the output SQLite database file.",
        validation_alias=AliasChoices('o', 'output'),
        validate_default=True,
    )

    _db_lock = asyncio.Lock()
    _log = logging.getLogger('dats.index')

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
        db, metadata = await create_db(self.output, DAT_OBJECT_TYPES)
        sqlalchemy_engine_log.setLevel(logging.WARNING)


        async with self.create_pool() as pool:
            await index_dats(db=db, metadata=metadata, db_lock=self._db_lock, playlists=playlists, dat_dirs=self.dat_dirs, pool=pool)

        async with db.connect() as connection:
            # Run the SQLite optimizer to improve performance on all tables (0x10000),
            # but don't take too long (0x00010)
            await connection.execute(text("PRAGMA optimize = 0x10012"))

        # Close the engine
        await db.dispose()

        end = time.perf_counter()
        elapsed = timedelta(seconds=end - start)
        self._log.info(f"Elapsed time: %s", elapsed)


class DatCommand(BaseSettings):
    tojson: CliSubCommand[ToJsonSubCommand]
    fromjson: CliSubCommand[FromJsonSubCommand]
    check: CliSubCommand[CheckSubCommand]
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


__all__ = (
    "ClrMamePro",
    "CompiledEntry",
    "compile_dats",
    "compile_dats_async",
    "DatTable",
    "encode_dat",
    "encode_dat_string",
    "Game",
    "get_dat_match",
    "index_dats",
    "load_dat",
    "Rom",
    "DAT_KEY_TABLE",
    "DAT_OBJECT_TYPES",
    "write_dat_key_index",
    "ParsedDatFile",
)

if __name__ == "__main__":
    CliApp.run(DatCommand)