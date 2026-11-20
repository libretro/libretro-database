#!/usr/bin/env python3

"""
Pydantic types and command-line helpers shared by the scripts.
"""

from collections.abc import Sequence
from typing import Annotated, Any, get_args

from aiomultiprocess import Pool
from frozendict import frozendict
from pydantic import AfterValidator, AliasChoices, BeforeValidator, Field, GetCoreSchemaHandler, GetPydanticSchema, HttpUrl, NonNegativeInt, PlainSerializer, PositiveInt, StringConstraints, WrapSerializer, WrapValidator
from pydantic_core import CoreSchema, core_schema
from pydantic_settings import NoDecode
from sqlalchemy.util import is_non_string_iterable

type CoercedHttpUrl = Annotated[HttpUrl, WrapValidator(lambda v, h: h(v) if v else None), PlainSerializer(str, str)]

@GetPydanticSchema
def _frozen_dict_schema(tp: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
    args = get_args(tp)
    key_type = args[0] if len(args) >= 1 else Any
    value_type = args[1] if len(args) >= 2 else Any

    return core_schema.no_info_after_validator_function(
        frozendict,
        core_schema.dict_schema(
            keys_schema=handler.generate_schema(key_type),
            values_schema=handler.generate_schema(value_type)
        )
    )

type FrozenDict[K, V] = Annotated[frozendict[K, V], _frozen_dict_schema]
"""Type definition for an immutable dict."""

type FrozenTypedDict[T] = Annotated[T, AfterValidator(lambda v: frozendict(v))]
# NOTE: The pattern is in Rust syntax, not Python syntax! (Pydantic-core is implemented in Rust.)
Crc = Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True, pattern=r"^[a-fA-F0-9]{8}$")]
"""A str that coerces to a lowercase CRC32 when used as a Pydantic field."""

Md5 = Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True, pattern=r"^[a-fA-F0-9]{32}$")]
"""A str that coerces to a lowercase MD5 when used as a Pydantic field."""

Sha1 = Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True, pattern=r"^[a-fA-F0-9]{40}$")]
"""A str that coerces to a loewrcase SHA1 when used as a Pydantic field."""

Sha256 = Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True, pattern=r"^[a-fA-F0-9]{64}$")]
"""A str that coerces to a lowercase SHA256 when used as a Pydantic field."""

type FrozenJsonValue = tuple[FrozenJsonValue, ...] | FrozenDict[str, FrozenJsonValue] | str | bool | int | float | None
"""An immutable equivalent to JsonValue."""

type OnlyFirst[T] = Annotated[T, BeforeValidator(lambda v: v[0] if is_non_string_iterable(v) and isinstance(v, Sequence) else v)]
"""A type that extracts the first element of a non-string iterable (or accepts anything else as-is)"""

type EmptyStringToNone[T] = Annotated[
    T | None,
    BeforeValidator(lambda v: v if v != "" else None),
    WrapSerializer(lambda v, h: h(v) if v != "" else None, return_type=(T | None))
]
"""
A type that serializes and validates empty strings as None.
"""

type EmptyToNone[T] = Annotated[
    T | None,
    BeforeValidator(lambda v: v if v else None),
    WrapSerializer(lambda v, h: h(v) if v else None, return_type=(T | None))
]
"""Serializes falsy values as None."""

@BeforeValidator
def _split_cli_csv(value: Any) -> Any:
    """
    Splits a comma-separated CLI argument into a tuple of strings.

    `pydantic-settings` normally decodes collection-typed settings as JSON,
    which fails for plain values like `-p 'Nintendo - Game Boy'`.
    Fields using this validator are marked with `NoDecode`
    so that they receive the raw string instead.
    """
    if isinstance(value, str):
        return tuple(filter(None, (item.strip() for item in value.split(","))))

    return value

type CliTuple[T] = Annotated[tuple[T, ...], NoDecode, _split_cli_csv]
"""
A tuple field that can be given on the command line
as one comma-separated argument or as a repeated argument.
"""

class PoolArgs:
    """Common CLI arguments for scripts that need to run multiple parallel tasks."""
    processes: int | None = Field(
        default=None,
        description="Number of processes to use for loading data. Defaults to the number of CPU cores.",
        # TODO: If this is set to 1, just do everything on the main process
    )

    maxtasksperchild: NonNegativeInt = 0
    childconcurrency: PositiveInt = 16
    queuecount: PositiveInt = 1

    def create_pool(self) -> Pool:
        return Pool(
            processes=self.processes,
            maxtasksperchild=self.maxtasksperchild,
            childconcurrency=self.childconcurrency,
            queuecount=self.queuecount,
        )

# How many files each data source may hold in memory
# between loading them and inserting them.
#
# Loading is parallel and inserting is not,
# so an unbounded pipeline ends up holding every data source in memory at once.
# The right limit depends on how much one unit of work expands to.
# Hasheous dumps are read in chunks of a fixed number of games,
# so a chunk is comparable in size to a DAT file.
DEFAULT_DAT_CONCURRENCY = 32
DEFAULT_IGDB_CONCURRENCY = 12
DEFAULT_HASHEOUS_CONCURRENCY = 12

class IndexArgs:
    concurrency: PositiveInt | None = Field(
        default=None,
        description="""
            How many files may be loaded but not yet inserted at any one time.
            Raise it to keep the worker pool busier, lower it to use less memory.
            Applies to every data source; each one picks its own limit by default.
        """,
        validation_alias=AliasChoices('concurrency', 'n'),
    )

    force: bool = Field(
        default=False,
        description="Overwrite existing output database file if it exists.",
        validation_alias=AliasChoices('f', 'force'),
    )

class VerboseArgs:
    verbose: bool = Field(
        default=False,
        description="Enable verbose output.",
        validation_alias=AliasChoices('v', 'verbose'),
    )

__all__ = (
    "DEFAULT_DAT_CONCURRENCY",
    "DEFAULT_HASHEOUS_CONCURRENCY",
    "DEFAULT_IGDB_CONCURRENCY",
    "CliTuple",
    "CoercedHttpUrl",
    "Crc",
    "EmptyStringToNone",
    "FrozenDict",
    "Md5",
    "Sha1",
    "Sha256",
)
