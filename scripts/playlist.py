"""
The playlists that `playlists.toml` defines, and the arguments that select them.
"""

import tomllib

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Annotated, Literal, NewType, Self

from frozendict import frozendict
from pydantic import AliasChoices, BaseModel, Field, FilePath, computed_field

from utils import CliTuple, FrozenDict, FrozenJsonValue

PlaylistTitle = NewType('PlaylistTitle', str)

type DumpIdType = Literal['crc', 'serial']

@dataclass(frozen=True)
class Playlist:
    """
    A playlist defines criteria for a set of games
    that will be aggregated into a single `.rdb` file.

    Conceptually similar to playlists in RetroArch,
    but this object doesn't list specific games;
    just criteria for aggregating their data.
    """

    title: PlaylistTitle
    '''
    The canonical title of the playlist, usually (but not necessarily)
    the name of a hardware manufacturer and platform.
    Used as the name of a generated `.dat` file and `.rdb` database.
    '''

    igdb_query: Annotated[
        FrozenDict[str, FrozenJsonValue] | str,
        Field(validation_alias='igdb')
    ]
    '''
    The IGDB query to use to fetch games for this playlist, as `playlists.toml` gives it.
    Left unparsed because `igdb` imports this module; see `igdb.playlist_query`.
    '''

    alts: tuple[str, ...] = ()
    '''
    Other names that may be used to address this playlist.

    Primarily used to identify `.dat` files from this repo
    that don't share the same name as the playlist title.
    '''

    hasheous_dirs: Annotated[tuple[str, ...], Field(validation_alias='hasheous')] = ()
    '''
    The names of zero or more Hasheous dump files, excluding the zip suffix.
    Passed to "https://hasheous.org/api/v1/Dumps/platforms/{name}".
    '''

    id_type: DumpIdType = 'crc'
    """
    Used to determine which ID is most useful for a platform.

    Some platforms (mostly CD-based) can have a given dump
    encoded or compressed in many different ways,
    making CRCs useless for reliably identifying them.
    For these platforms, we use the serial number
    that's usually embedded in the ROM data.

    The values in playlists.toml are taken from
    https://github.com/libretro/RetroArch/blob/master/tasks/task_database_cue.c
    """

class PlaylistConfig(BaseModel, frozen=True):
    """The `[[playlists]]` of `playlists.toml`. Other sections are ignored."""

    playlists: tuple[Playlist, ...]

    @classmethod
    def load(cls, path: Path) -> Self:
        return cls.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))

    def playlists_titled(self, titles: Collection[str]) -> tuple[Playlist, ...]:
        """Returns the playlists with the given titles, or all of them if `titles` is empty."""
        return tuple(p for p in self.playlists if p.title in titles) if titles else self.playlists

    @computed_field
    @cached_property
    def by_title(self) -> Mapping[PlaylistTitle, Playlist]:
        return frozendict({pl.title: pl for pl in self.playlists})

PARENT_DIR = Path(__file__).parent.parent

class PlaylistArgs:
    config: FilePath = Field(
        default=PARENT_DIR / 'playlists.toml',
        title="Playlist Config File",
        description="Path to the config file that defines available playlists.",
        validation_alias=AliasChoices('c', 'config'),
        validate_default=True,
    )

    playlists: CliTuple[str] = Field(
        default=(),
        description="""
            Restrict processing to these playlists.
            Pass as -p '<playlist1>,<playlist2>,...' or as repeated -p '<playlist>' arguments.
            If omitted, every playlist in the config is processed.
        """,
        validation_alias=AliasChoices('playlists', 'p'),
        examples=[("Coleco - ColecoVision", "Dinothawr")]
    )

__all__ = (
    "DumpIdType",
    "Playlist",
    "PlaylistArgs",
    "PlaylistConfig",
    "PlaylistTitle",
)
