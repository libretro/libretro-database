#!/usr/bin/env python3

"""
Provides base classes and utilities for defining database models using Pydantic and SQLAlchemy.
"""

import asyncio
import sys

from abc import ABC
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import asynccontextmanager
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from functools import cache, cached_property
from itertools import chain
from pathlib import Path
from typing import Annotated, Any, ClassVar, ForwardRef, Literal, LiteralString, NamedTuple, NewType, TypeGuard, get_origin, overload, get_args

import sqlalchemy

from aiomultiprocess import Pool
from frozendict import frozendict
from more_itertools import always_iterable, only
from pydantic import AfterValidator, AliasChoices, BaseModel, BeforeValidator, Field, FilePath, GetCoreSchemaHandler, GetPydanticSchema, HttpUrl, JsonValue, NonNegativeInt, PlainSerializer, PositiveInt, StringConstraints, ValidatorFunctionWrapHandler, WrapSerializer, WrapValidator
from pydantic_core import CoreSchema, core_schema
from pydantic_settings import NoDecode
from pydantic.fields import ComputedFieldInfo, FieldInfo
from pydantic_extra_types.country import CountryNumericCode
from sqlalchemy import DDL, Column, Constraint, ForeignKey, MetaData, Table, Index, text
from sqlalchemy import event
from sqlalchemy.dialects.sqlite import insert, Insert
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.schema import SchemaConst
from sqlalchemy.types import NullType, TypeEngine
from sqlalchemy.util import is_non_string_iterable
from sqlalchemy.util.typing import (GenericProtocol, TypeAliasType,
                                    de_optionalize_union_types,
                                    eval_expression, flatten_newtype,
                                    includes_none, is_fwd_ref, is_generic,
                                    is_literal, is_newtype, is_pep593, is_pep695, is_union, make_union_type)

type AnnotationScanType = type[Any] | str | ForwardRef | NewType | TypeAliasType | GenericProtocol[Any]

def is_non_string_sequence_type(t: Any) -> TypeGuard[type[Sequence[Any]]]:
    """
    Determines whether a type annotation represents a non-string iterable type.
    """
    if isinstance(t, type) and issubclass(t, Sequence) and not issubclass(t, (str, bytes, bytearray)):
        return True

    return False

def flatten_newtype(type_: NewType) -> type[Any]:
    super_type = type_.__supertype__
    while is_newtype(super_type):
        super_type = super_type.__supertype__
    return super_type  # type: ignore[return-value]

type CopyableSchemaItem = Column | ForeignKey | Constraint | Index

@overload
def copy_schema_item(item: Column) -> Column: ...
@overload
def copy_schema_item(item: ForeignKey) -> ForeignKey: ...
@overload
def copy_schema_item(item: Constraint) -> Constraint: ...
@overload
def copy_schema_item(item: Index) -> Index: ...

def copy_schema_item(item: CopyableSchemaItem) -> CopyableSchemaItem:
    """
    Creates a copy of a SQLAlchemy schema item (Column, ForeignKey, or Constraint).
    This is necessary because SQLAlchemy schema items have internal state that can cause issues if shared between multiple tables.
    """
    match item:
        case Column() | ForeignKey() | Constraint():
            return item._copy()
        case Index():
            return Index(item.name, *item.expressions, unique=item.unique, info=item.info, **item.dialect_kwargs)
        case _:
            raise TypeError(f"Unsupported schema item type: {type(item)}")


type RelationshipTableArg = Mapping[str, Column] | Iterable[Column] | Column | ForeignKey
RowId = NewType("RowId", int)
RowIdColumn = Annotated[RowId | None, Column(primary_key=True, index=True, unique=True, nullable=False), Field(default=None)]
EMPTY_DICT = frozendict()

DEFAULT_RELATIONSHIP_TABLE_KWARGS = frozendict({"sqlite_with_rowid": False})

@asynccontextmanager
async def db_transaction(db: AsyncEngine, db_lock: asyncio.Lock):
    async with db_lock:
        async with db.begin() as tx:
            yield tx

@dataclass(eq=True, unsafe_hash=True)
class Relationship:

    tablename: str | None
    """
    The name of the relationship table that will be created
    to represent this relationship.

    If None, a default name will be generated based on the parent model's table name
    and the Pydantic field name that this Relationship is associated with.
    """

    self_columns: frozendict[str, Column]
    """
    One or more `Column`s that identify the "parent" object.
    Each key is a field name on the parent object's model,
    and each value is a corresponding column in the generated relationship table.
    """

    related_columns: frozendict[str, Column]
    """
    One or more `Column`s that define the related object.

    Can be references to another `DatabaseModel`'s primary key columns,
    or primitive values.
    """

    tableargs: tuple[CopyableSchemaItem, ...]
    """
    Positional arguments to pass as-is to the Table constructor
    after the table name, metadata, and explicit constraints.
    Useful for table-level constraints.
    """

    tablekwargs: frozendict[str, Any]
    """
    Keyword arguments to pass as-is to the Table constructor.
    """

    def __init__(
        self,
        tablename: str | None = None,
        self_columns: RelationshipTableArg = EMPTY_DICT,
        related_columns: RelationshipTableArg = EMPTY_DICT,
        tableargs: Iterable[CopyableSchemaItem] = (),
        tablekwargs: Mapping[str, Any] | None = DEFAULT_RELATIONSHIP_TABLE_KWARGS
    ):
        self.tablename = tablename

        match self_columns:
            case Column() as column:
                self.self_columns = frozendict({column.name: column})
            case ForeignKey() as fk:
                name = fk.target_fullname.split(".")[-1]
                column_name = fk.target_fullname.replace(".", "_")
                self.self_columns = frozendict({name: Column(column_name, fk._copy(), nullable=False)})
            case { **items }:
                self.self_columns = frozendict(items)
            case [*columns]:
                self.self_columns = frozendict({c.name: c for c in columns})
            case _:
                raise TypeError(f"Unsupported self_columns type: {type(self_columns)}")

        match related_columns:
            case Column() as column:
                self.related_columns = frozendict({column.name: column})
            case ForeignKey() as fk:
                name = fk.target_fullname.split(".")[-1]
                column_name = fk.target_fullname.replace(".", "_")
                self.related_columns = frozendict({name: Column(column_name, fk._copy(), nullable=False)})
            case { **items }:
                self.related_columns = frozendict(items)
            case [*columns]:
                self.related_columns = frozendict({c.name: c for c in columns})
            case _:
                raise TypeError(f"Unsupported related_columns type: {type(related_columns)}")

        self.tableargs = tuple(tableargs)
        self.tablekwargs = frozendict(tablekwargs) if tablekwargs is not None else EMPTY_DICT


    def __deepcopy__(self, memo: dict[int, Any]) -> "Relationship":
        return Relationship(
            tablename=self.tablename,
            self_columns=frozendict({k: copy_schema_item(v) for k, v in self.self_columns.items()}),
            related_columns=frozendict({k: copy_schema_item(c) for k, c in self.related_columns.items()}),
            tableargs=tuple(copy_schema_item(i) for i in self.tableargs),
            tablekwargs=frozendict(self.tablekwargs),
        )

SchemaDef = Column | Relationship

class DatabaseModel(BaseModel, ABC, frozen=True):
    __tablename__: ClassVar[LiteralString]
    __tableargs__: ClassVar[tuple[CopyableSchemaItem, ...]] = ()
    __tablekwargs__: ClassVar[Mapping[str, Any]] = EMPTY_DICT
    __tableddl__: ClassVar[LiteralString | tuple[LiteralString, ...] | None] = None
    """
    Extra DDL statements to execute after creating this class's table.
    Intended for database-specific features that SQLAlchemy doesn't natively support.
    """

    @classmethod
    def get_default_column_type(cls, annotation: AnnotationScanType | ComputedFieldInfo | FieldInfo) -> type[TypeEngine]:
        """
        Maps a Pydantic type annotation to a SQLAlchemy column type.

        :param annotation: A type declaration, or a FieldInfo or ComputedFieldInfo instance.
        :return: A SQLAlchemy TypeEngine subclass representing the column type.
        """

        if isinstance(annotation, FieldInfo):
            if annotation.annotation is None:
                raise TypeError("Field has no type annotation")

            return cls.get_default_column_type(annotation.annotation)

        if isinstance(annotation, ComputedFieldInfo):
            if annotation.return_type is None:
                raise TypeError("Computed field has no return type annotation")

            return cls.get_default_column_type(annotation.return_type)

        field_type = cls.unwrap_type(annotation)

        if field_type == bool:
            return sqlalchemy.Boolean

        if issubclass(field_type, (int, CountryNumericCode)):
            return sqlalchemy.Integer

        if issubclass(field_type, (str, HttpUrl)):
            return sqlalchemy.String

        if field_type == datetime:
            return sqlalchemy.DateTime

        if field_type == date:
            return sqlalchemy.Date

        if field_type == float:
            return sqlalchemy.Float

        if field_type == JsonValue:
            return sqlalchemy.JSON

        raise NotImplementedError(f"Unsupported field type: {field_type}")

    @classmethod
    @cache
    def get_default_foreign_keys(cls) -> tuple[ForeignKey, ...]:
        """
        Returns foreign keys referencing this model's primary key columns.
        The returned keys can be used to uniquely identify an instance of this model.

        :return: A tuple of `ForeignKey` instances, one for each primary key column.
        Usually just one, but can be more for composite primary keys.
        """

        fk_items: list[ForeignKey] = []
        pk_cols = cls.pk_columns()
        for pk_field_name, pk_coldef in pk_cols.items():
            fk_items.append(
                ForeignKey(f"{cls.__tablename__}.{pk_coldef.name or pk_field_name}")
            )

        return tuple(fk_items)

    @classmethod
    @cache
    def unwrap_type(
        cls,
        t: AnnotationScanType
    ) -> type:
        """
        Strips away literals, optionals, newtypes, generics, and forward references.

        :param t: The type annotation to unwrap
        """
        unwrapped = t
        while not isinstance(unwrapped, type):
            match unwrapped:
                case type():
                    break
                case newtype if is_newtype(newtype):
                    # If this is a newtype, unwrap to get the underlying type
                    unwrapped = flatten_newtype(newtype)
                case literal if is_literal(literal):
                    # If this is a Literal[A, B, C, ...], unwrap to get the types of A, B, C, ...
                    # (but if there's just one unique type, resolve to it)
                    args = get_args(literal)
                    literal_types = set(map(type, args))
                    unwrapped = type(args[0]) if len(literal_types) == 1 else make_union_type(*literal_types)
                case annotation if is_pep593(annotation):
                    # If this is Annotated[T, ...], unwrap to get T
                    args = get_args(annotation)
                    assert len(args) >= 2
                    unwrapped = args[0]
                case ref if is_fwd_ref(ref, check_generic=True, check_for_plain_string=True):
                    # If this is a ForwardRef...
                    unwrapped = eval_expression(ref.__forward_arg__, cls.__module__, locals_=sys.modules[cls.__module__].__dict__)
                case str() as type_expression:
                    unwrapped = eval_expression(type_expression, cls.__module__, locals_=sys.modules[cls.__module__].__dict__)
                case alias if is_pep695(alias) and not alias.__type_params__:
                    # If this is a type alias without parameters...
                    unwrapped = alias.__value__
                case alias if is_pep695(alias) and (args := get_args(alias)):
                    # If this is a parameterized type alias...
                    unwrapped = alias.__value__[args]
                case generic if is_generic(generic) and not is_union(generic): # and is_non_string_sequence_type(get_origin(generic)):
                    # If this is parameterized type like list[T]...
                    unwrapped = get_origin(generic)
                    assert unwrapped is not None
                case optional if includes_none(unwrapped):
                    # If this type can have a value of None...
                    # (For most purposes you can treat it as Optional[T],
                    # but Python has several equivalent constructs.)
                    unwrapped = de_optionalize_union_types(unwrapped)
                case _:
                    raise TypeError(f"Unexpected type annotation: {t} ({type(t)})")

        assert isinstance(unwrapped, type)
        return unwrapped

    @classmethod
    def get_field_type(cls, field: FieldInfo | ComputedFieldInfo | str) -> type:
        field_annotation = cls.get_field_annotation(field)
        if field_annotation is None:
            raise TypeError(f"Model field {cls.__name__}.{field} has no type annotation")

        return cls.unwrap_type(field_annotation)

    @classmethod
    def get_field_annotation(cls, field: FieldInfo | ComputedFieldInfo | str) -> AnnotationScanType | None:
        """
        Returns the type annotation of a model field.

        :param field: A `FieldInfo`, `ComputedFieldInfo`, or field name.
        """
        match field:
            case str(field_name):
                info = cls.model_fields.get(field_name) or cls.model_computed_fields.get(field_name)
                if info is None:
                    raise KeyError(f"{cls.__name__} has no real or computed Pydantic field named {field_name!r}")
                return cls.get_field_annotation(info)
            case FieldInfo(annotation=annotation):
                return annotation
            case ComputedFieldInfo(return_type=annotation):
                return annotation
            case _:
                raise TypeError(f"Expected FieldInfo, ComputedFieldInfo, or str; got {type(field)}")

    @classmethod
    def get_collection_element_type(cls, field: FieldInfo | ComputedFieldInfo | str) -> type:
        """
        Returns the element type of a collection-typed model field.

        :param field: A `FieldInfo`, `ComputedFieldInfo`, or field name.
        :return: The element type of the collection.
        :raises TypeError: if the field is not a collection type.
        """

        field_type = cls.get_field_type(field)
        if not is_non_string_sequence_type(field_type):
            raise TypeError(f"Field {cls.__name__}.{field} is not a non-string sequence type; got {field_type}")

        element_type = cls.unwrap_type(get_args(field_type)[0])
        return element_type

    @classmethod
    def get_column_metadata(cls, field: FieldInfo | ComputedFieldInfo | str) -> Column | None:
        """
        Retrieves a copy of the `Column` explicitly defined on a model field's `Annotated` metadata, if any.

        :param field: A `FieldInfo`, `ComputedFieldInfo`, or field name.
        :return: The `Column` defined on the field, or `None` if there isn't one.
        :raises KeyError: if the field name does not exist on this model.
        :raises TypeError: if the field is not one of the expected types.
        :raises ValueError: if multiple `Column` instances are defined on the field.
        """

        match field:
            case str(field_name):
                info = cls.model_fields.get(field_name) or cls.model_computed_fields.get(field_name)
                if info is None:
                    raise KeyError(f"Model {cls.__name__} has no real or computed field named {field_name!r}")
                return cls.get_column_metadata(info)
            case FieldInfo(metadata=metadata):
                return only((m._copy() for m in metadata if isinstance(m, Column)), default=None)
            case ComputedFieldInfo(return_type=None):
                return None
            case ComputedFieldInfo(return_type=annotation) if is_pep593(annotation):
                args = get_args(annotation)
                return only((m._copy() for m in args if isinstance(m, Column)), default=None)
            case ComputedFieldInfo(return_type=annotation):
                return None
            case _:
                raise TypeError(f"Expected FieldInfo, ComputedFieldInfo, or str; got {type(field)}")

    @classmethod
    def get_relationship_table_def(cls, field: FieldInfo | ComputedFieldInfo | str) -> Relationship | None:
        """
        Retrieves a copy of the `RelationshipTableDef` explicitly defined on a model field's `Annotated` metadata, if any.

        :param field: A `FieldInfo`, `ComputedFieldInfo`, or field name.
        :return: The `RelationshipTableDef` defined on the field, or `None` if there isn't one.
        :raises KeyError: if the field name does not exist on this model.
        :raises TypeError: if the field is not one of the expected types.
        """
        match field:
            case str(field_name):
                info = cls.model_fields.get(field_name) or cls.model_computed_fields.get(field_name)
                if info is None:
                    raise KeyError(f"Model {cls.__name__} has no real or computed field named {field_name!r}")
                return cls.get_relationship_table_def(info)
            case FieldInfo(metadata=metadata):
                return only((m for m in metadata if isinstance(m, Relationship)), default=None)
            case ComputedFieldInfo(return_type=None):
                return None
            case ComputedFieldInfo(return_type=annotation) if is_pep593(annotation):
                args = get_args(annotation)
                return only((m for m in args if isinstance(m, Relationship)), default=None)
            case ComputedFieldInfo(return_type=annotation):
                return None
            case _:
                raise TypeError(f"Expected FieldInfo or ComputedFieldInfo, got {type(field)}")

    @classmethod
    @cache
    def pk_columns(cls) -> frozendict[str, Column]:
        """
        Returns a dictionary of primary key columns for the model.

        :return: A dictionary mapping field names to Column instances that are primary keys.
        """

        return frozendict({k:v for k, v in cls.columns().items() if v.primary_key})

    @classmethod
    @cache
    def columns(cls) -> frozendict[str, Column]:
        """
        Gets all Column instances from this model type's fields
        as defined in their Annotated metadata.
        Absent values will be filled in with defaults.

        Returns a map of field names to Column instances,
        empty if none are found.

        :returns: A map of field names to `Column` instances,
        where each `Column` is populated by the field's explicit annotation
        with additional defaults.
        """

        result: dict[str, Column] = {}

        all_fields = chain(cls.model_fields.items(), cls.model_computed_fields.items())
        for field_name, field in all_fields:
            # For each field (real or computed)...
            if cls.get_relationship_table_def(field):
                # Don't create Columns for known relationship tables
                continue

            field_annotation = cls.get_field_annotation(field)
            unwrapped_field_type = cls.unwrap_type(field_annotation)
            field_origin = get_origin(field_annotation)
            column = cls.get_column_metadata(field)

            if column is None and (is_non_string_sequence_type(field_origin) or is_non_string_sequence_type(unwrapped_field_type)):
                # Skip automatic FK generation for collection types
                # that don't explicitly define a column
                # otherwise we run the risk of infinite recursion
                # (they should use RelationshipTableDef instead)
                continue


            if isinstance(field, FieldInfo) and field.exclude:
                # Don't create Columns for excluded fields, except for primary keys
                # (this is so we can have rowids, which aren't interesting outside of the DB)
                if column is None or not column.primary_key:
                    continue

            column = column._copy() if column is not None else Column()
            # Create a copy of the Column to avoid mutating the one in the Annotated metadata

            if __debug__:
                # Wrapped in a __debug__ even though asserts are stripped with -O
                # so that mypy doesn't treat Column as a Never
                assert column.table is None, f"{column} unexpectedly linked to {column.table}, did something mutate it?"

            if not column.name:
                # Use the field name as the column name if not given
                column.name = field_name

            if column._user_defined_nullable == SchemaConst.NULL_UNSPECIFIED:
                # TODO: Raise a warning if _user_defined_nullable doesn't exist,
                # as it means SQLAlchemy's internals have changed
                # If nullability isn't specified, infer it from the field annotation
                column.nullable = includes_none(field_annotation)

            field_type = cls.get_field_type(field)
            if issubclass(field_type, DatabaseModel):
                # If this field refers to another model...
                if field_type != cls and not column.foreign_keys:
                    # If this column doesn't already define any foreign keys,
                    # get the default foreign keys that the target type uses
                    for fk in field_type.get_default_foreign_keys():
                        assert fk.parent is None, f"Default ForeignKey to {field_type.__name__} has an unexpected parent {fk.parent}; did something mutate it?"
                        column.append_foreign_key(fk._copy())

                # Otherwise, this column already has foreign keys, so use them;
                # the type doesn't matter, SQLAlchemy will infer it when building the Tables
            elif isinstance(column.type, (NullType, type(None))):
                # If there isn't a type already, infer it from the field annotation
                column.type = cls.get_default_column_type(field)()

            result[field_name] = column

        return frozendict(result)

    @classmethod
    @cache
    def relationship_table_defs(cls) -> frozendict[str, Relationship]:
        """
        Gets all RelationshipTableDef instances from this model type's fields,
        as defined in their Annotated metadata.
        Absent values will be filled in with defaults.

        :returns: A dict of field names to RelationshipTableDef instances.
        The key will always be a field in this class,
        regardless of what the table or its columns are named.

        :raises ValueError: if multiple RelationshipTableDefs are found on a single field.
        """

        result: dict[str, Relationship] = {}
        all_fields = chain(cls.model_fields.items(), cls.model_computed_fields.items())
        for field_name, field in all_fields:
            if isinstance(field, FieldInfo) and field.exclude:
                # Don't create relationship tables that represent excluded fields
                continue

            field_annotation = cls.get_field_annotation(field)
            field_origin = get_origin(field_annotation)
            field_type = cls.get_field_type(field)

            defn = cls.get_relationship_table_def(field)
            if not is_non_string_sequence_type(field_origin):
                # Relationship tables only make sense for collection types;
                # raise an error if one is inappropriately defined, otherwise just move on
                if not defn:
                    # No RelationshipTableDef is explicitly defined, and there shouldn't be one; good!
                    continue
                else:
                    raise TypeError(f"Cannot create relationship table for non-collection field {cls.__name__}.{field_name} of type {field_type}")

            defn = deepcopy(defn) if defn else Relationship()
            # If no RelationshipTableDef is defined, create a default one;
            # otherwise create a deep copy of the existing one to avoid mutating it
            # (since SQLAlchemy Table/Column/etc. instances have internal state)

            if not defn.tablename:
                # If the RelationshipTableDef doesn't specify a table name,
                # generate a default one based on the parent table and field name
                defn.tablename = f"{cls.__tablename__}_{field_name}"

            if not defn.self_columns:
                # If the RelationshipTableDef doesn't specify columns that reference this object,
                # generate defaults with this class's primary key columns
                pk_cols = cls.pk_columns()
                if not pk_cols:
                    raise ValueError(
                        f"Cannot create default relationship table for {cls.__name__}.{field_name} "
                        f"because {cls.__name__}'s generated table has no primary key columns; "
                        "try defining one explicitly by passing a Column to one of its Annotated fields "
                        "and setting primary_key=True"
                    )


                # By default, generate a column for each component of this class's primary key
                # and make it part of the relationship table row's composite primary key.
                # (Whew! What a mouthful.)
                defn.self_columns = frozendict({
                    pkcol_name: Column(
                        f"{defn.tablename}_{pkcol.name}",
                        ForeignKey(f"{cls.__tablename__}.{pkcol.name}"),
                        primary_key=True,
                        index=True,
                    ) for pkcol_name, pkcol in pk_cols.items()
                })

            if not defn.related_columns:
                # If the RelationshipTableDef doesn't specify columns that reference the related object,
                # generate defaults based on the related type
                field_type_args = get_args(field_annotation)
                related_type = cls.unwrap_type(field_type_args[0])
                # TODO: Is this the right way to get the related type?

                if issubclass(related_type, DatabaseModel):
                    # If this field is a collection of other database models...
                    related_pk_cols = related_type.pk_columns()
                    if not related_pk_cols:
                        raise ValueError(
                            f"Cannot create default relationship table for {cls.__name__}.{field_name} "
                            f"because related model {related_type.__name__} has no primary key columns; "
                            "try defining one explicitly"
                        )

                    # ...add a column for each part of the related type's primary key
                    defn.related_columns = frozendict({
                        pkcol_name: Column(
                            f"{related_type.__tablename__}_{pkcol.name}",
                            ForeignKey(f"{related_type.__tablename__}.{pkcol.name}"),
                            primary_key=True,
                            index=True
                        )
                        for pkcol_name, pkcol in related_pk_cols.items()
                    })
                else:
                    # This field is a collection of primitive values
                    defn.related_columns = frozendict({
                        field_name: Column(
                            f"{cls.__tablename__}_{field_name}",
                            cls.get_default_column_type(related_type),
                            primary_key=True
                        ),
                    })

            result[field_name] = defn

        return frozendict(result)

    @classmethod
    def create_tables(cls, metadata: MetaData) -> tuple[Table, *tuple[Table, ...]]:
        """
        Creates a SQLAlchemy Table object for this model type,
        and any associated relationship tables.

        :param metadata: The `MetaData` to associate the tables with.
        :return: A tuple of `Table`s, where the first item is the main table
                    and any subsequent items are relationship tables.
        """

        relationship_tables: list[Table] = []
        main_table_columns: list[Column] = []

        columns = cls.columns()
        relationship_table_defs = cls.relationship_table_defs()
        all_fields = chain(cls.model_fields.items(), cls.model_computed_fields.items())
        for field_name, field in all_fields:
            match field:
                case FieldInfo(exclude=True):
                    # Excluded fields won't have columns
                    pass
                case (FieldInfo() | ComputedFieldInfo()) if field_name in columns:
                    # Columns contain internal state, so we need to copy them;
                    # otherwise SQLAlchemy will think we're adding the same Column to multiple tables
                    main_table_columns.append(columns[field_name]._copy())
                case (FieldInfo() | ComputedFieldInfo()) if field_name in relationship_table_defs:
                    reldef = relationship_table_defs[field_name]
                    if __debug__:
                        for colname, col in reldef.self_columns.items():
                            assert col.table is None, f"{col} representing {colname} unexpectedly linked to {col.table}, did something mutate it?"

                        for colname, col in reldef.related_columns.items():
                            assert col.table is None, f"{col} representing {colname} unexpectedly linked to {col.table}, did something mutate it?"

                    reltable = Table(
                        reldef.tablename or f"{cls.__tablename__ or cls.__name__}_{field_name}",
                        metadata,
                        *(copy_schema_item(c) for c in reldef.self_columns.values()),
                        *(copy_schema_item(c) for c in reldef.related_columns.values()),
                        *(copy_schema_item(i) for i in reldef.tableargs),
                        **reldef.tablekwargs,
                    )
                    relationship_tables.append(reltable)

        main_table = Table(
            cls.__tablename__,
            metadata,
            *main_table_columns,
            *cls.__tableargs__,
            **cls.__tablekwargs__,
        )

        # If we want to execute any extra data definition language statements (e.g. CREATE, ALTER, etc.),
        # register an event listener to do so after creating the table
        match cls.__tableddl__:
            case str() as ddl:
                event.listen(main_table, "after_create", DDL(ddl))
            case [*ddls]:
                for ddl in ddls:
                    event.listen(main_table, "after_create", DDL(ddl))

        return (main_table, *relationship_tables)

    @cached_property
    def nested_models(self) -> frozenset["DatabaseModel"]:
        """
        Returns a set of all nested DatabaseModel instances referenced by this model's fields,
        excluding itself.

        Checks immediate attributes,
        but only recurses into attributes that are also DatabaseModel instances or lists of them.
        You can subclass this behavior if you need more complex recursion.
        """
        models: set[DatabaseModel] = set()
        for field_name in chain(type(self).model_fields, type(self).model_computed_fields):
            match getattr(self, field_name):
                case obj if isinstance(obj, DatabaseModel):
                    models.add(obj)
                    models.update(obj.nested_models)
                case [*items]:
                    objects = (i for i in items if isinstance(i, DatabaseModel))
                    for obj in objects:
                        models.add(obj)
                        models.update(obj.nested_models)

        return frozenset(models)

    def get_relationship(self, field_name: str) -> tuple[frozendict[str, Any], ...]:
        cls = type(self)
        reldefs = cls.relationship_table_defs()
        reldef = reldefs.get(field_name)

        if not reldef:
            return ()

        field = cls.model_fields.get(field_name) or cls.model_computed_fields.get(field_name)
        if not field:
            return ()

        field_annotation = cls.get_field_annotation(field)
        field_origin = get_origin(field_annotation)
        if not is_non_string_sequence_type(field_origin):
            # If the field isn't a non-string sequence type, we don't handle it here
            return ()

        self_cols = dict()
        for col_fieldname, col in reldef.self_columns.items():
            # For each column that defines this relationship table...
            # Get the value from this object that corresponds to the column
            self_cols[col.name] = getattr(self, col_fieldname)

        rows: list[frozendict[str, Any]] = []
        field_value = getattr(self, field_name)
        for v in field_value:
            # For each item in this collection...
            row: dict[str, Any] = dict(self_cols)
            for col_fieldname, col in reldef.related_columns.items():
                # For each column that defines this relationship table...
                if isinstance(v, DatabaseModel):
                    # Try the field name first, fall back to the column name
                    row[col.name] = getattr(v, col_fieldname, getattr(v, col.name, None))
                else:
                    # Or it's just a primitive value
                    row[col.name] = v

            rows.append(frozendict(row))

        return tuple(rows)

    @cached_property
    def relationships(self) -> frozendict[str, tuple[frozendict[str, Any], ...]]:
        """
        Returns a dictionary whose keys are field names representing relationships,
        and whose values are sets of dicts suitable for relationship tables.
        These dicts include the foreign key mappings for this object and the related objects.

        This property is not recursive, i.e. it does not include relationships from nested models.
        """
        results: dict[str, tuple[frozendict[str, Any], ...]] = {}
        cls = type(self)

        for field_name in chain(cls.model_fields, cls.model_computed_fields):
            rows = self.get_relationship(field_name)
            if rows:
                results[field_name] = tuple(rows)

        return frozendict(results)

    @property
    def as_row(self) -> dict[str, Any]:
        return self.model_dump(context='row')

    @classmethod
    def table(cls, metadata: MetaData) -> Table:
        """Returns this model's main table in `metadata`."""
        return metadata.tables[cls.__tablename__]

    @classmethod
    def relationship_table(cls, metadata: MetaData, field_name: str) -> Table:
        """Returns the table in `metadata` that holds one of this model's relationship fields."""
        tablename = cls.relationship_table_defs()[field_name].tablename
        assert tablename is not None, "relationship_table_defs() names every table"
        return metadata.tables[tablename]

    @classmethod
    def relationship_columns(cls, metadata: MetaData, field_name: str) -> tuple[Column, Column]:
        """
        Returns the columns of a relationship table
        that refer to this model and to each related value, in that order.

        Only for relationships with a single column on each side.
        """
        definition = cls.relationship_table_defs()[field_name]
        table = cls.relationship_table(metadata, field_name)
        (owner,) = definition.self_columns.values()
        (related,) = definition.related_columns.values()
        return table.c[owner.name], table.c[related.name]

    @classmethod
    def insert(cls, metadata: MetaData) -> Insert:
        """
        Returns an `Insert` object for this model's main table.
        """
        assert cls.__tablename__ in metadata.tables, f"Table {cls.__tablename__} not found in metadata; did you forget to call create_tables()?"
        return insert(metadata.tables[cls.__tablename__])


class ExtractedRows(NamedTuple):
    """
    The database rows that a batch of models expands to,
    grouped by the table each row belongs in.

    Extracting rows is by far the most expensive part of indexing a data source,
    so it's done in the worker process that loaded the models
    rather than in the process that owns the database.
    Plain dicts of primitives are also much cheaper to send between processes
    than the `DatabaseModel` graphs they come from.
    """

    objects: tuple[tuple[str, tuple[dict[str, Any], ...]], ...]
    """
    Rows for the models themselves, as `(table name, rows)` pairs.
    """

    relationships: tuple[tuple[str, tuple[dict[str, Any], ...]], ...]
    """
    Rows for the relationship tables, as `(table name, rows)` pairs.
    """


def _dedupe_key(model: DatabaseModel) -> Any:
    """
    Returns a cheap value that identifies `model` for deduplication.

    Models are deduplicated by primary key where they have one,
    since hashing an entire model graph is much more expensive
    and the database would discard the later duplicate anyway.
    """
    pk_fields = type(model).pk_columns()

    if not pk_fields:
        return model

    return tuple(getattr(model, field_name) for field_name in pk_fields)


class RowAccumulator:
    """
    Collects the rows that models expand to, one model at a time.

    Lets a caller expand a large file incrementally,
    instead of holding every model in it in memory at once.
    Some Hasheous dumps describe hundreds of thousands of games,
    and the models are far bigger than the rows they turn into.
    """

    def __init__(self, relationship_prefix: str) -> None:
        """
        :param relationship_prefix: The table name that relationship tables are named after,
          i.e. the `__tablename__` of the model type that owns the relationship fields.
        """
        self._relationship_prefix = relationship_prefix
        self._objects: dict[str, dict[Any, dict[str, Any]]] = {}
        self._relationships: dict[str, dict[frozendict[str, Any], None]] = {}

    def add(self, model: DatabaseModel, *, keep: Callable[[str, Mapping[str, Any]], bool] | None = None) -> None:
        """
        Expands `model` and everything nested inside it into rows.

        :param keep: Decides whether to accept a row, given the table it belongs in.
          Rejected rows are dropped here rather than after the fact,
          so the ones that aren't wanted never accumulate.
        """
        for nested in chain((model,), model.nested_models):
            tablename = type(nested).__tablename__
            rows = self._objects.setdefault(tablename, {})
            key = _dedupe_key(nested)

            if key in rows:
                continue

            row = nested.as_row
            if keep is None or keep(tablename, row):
                rows[key] = row

        for field_name, field_rows in model.relationships.items():
            tablename = f"{self._relationship_prefix}_{field_name}"
            table_rows = self._relationships.setdefault(tablename, {})

            for row in field_rows:
                if keep is None or keep(tablename, row):
                    table_rows.setdefault(row, None)

    def result(self) -> ExtractedRows:
        """Returns everything accumulated so far, ready to be inserted."""
        return ExtractedRows(
            objects=tuple((name, tuple(rows.values())) for name, rows in self._objects.items() if rows),
            relationships=tuple(
                (name, tuple(dict(row) for row in rows))
                for name, rows in self._relationships.items()
                if rows
            ),
        )


def extract_rows(models: Iterable[DatabaseModel], *, relationship_prefix: str) -> ExtractedRows:
    """
    Expands `models` and everything they contain into rows, ready to be inserted.

    A convenience wrapper around `RowAccumulator`
    for callers that already hold every model in memory.

    :param models: The top-level models to expand.
      Nested models are included, but only the top-level ones contribute relationships.
    :param relationship_prefix: The table name that relationship tables are named after,
      i.e. the `__tablename__` of the model type that owns the relationship fields.
    """
    accumulator = RowAccumulator(relationship_prefix)

    for model in models:
        accumulator.add(model)

    return accumulator.result()


class RowDeduplicator:
    """
    Remembers which rows have already been sent to each table,
    so that rows repeated across files never reach the database twice.

    Most of the objects these data sources describe
    (genres, companies, platforms, age rating boards, and so on)
    appear in nearly every playlist or dump.
    Letting SQLite discard those duplicates still costs a parameter bind
    and an index probe apiece, which adds up to far more
    than the cost of remembering their primary keys here.

    Only valid for a database that this process built from empty,
    since it assumes that nothing else has inserted rows behind its back.
    """

    def __init__(self, metadata: MetaData) -> None:
        self._metadata = metadata
        self._seen: dict[str, set[tuple[Any, ...]]] = {}

    def filter(self, tablename: str, rows: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        """
        Returns the rows of `rows` whose primary keys this deduplicator hasn't seen before,
        and remembers them for next time.

        Tables without a primary key are passed through untouched.
        """
        key_columns = tuple(c.name for c in self._metadata.tables[tablename].primary_key.columns)

        if not key_columns:
            return list(rows)

        seen = self._seen.setdefault(tablename, set())
        unseen: list[Mapping[str, Any]] = []

        for row in rows:
            key = tuple(row.get(c) for c in key_columns)
            if key not in seen:
                seen.add(key)
                unseen.append(row)

        return unseen


def deferred_indexes(metadata: MetaData) -> tuple[Index, ...]:
    """
    Returns the indexes in `metadata` that aren't needed while the database is being filled.

    Unique indexes have to exist from the start,
    because the inserts rely on them to detect conflicts.
    Every other index only matters once the data is queried,
    and SQLite can build one in a single sorted pass at the end
    for much less than it costs to update it on every inserted row.
    """
    return tuple(
        index
        for table in metadata.tables.values()
        for index in table.indexes
        if not index.unique
    )


async def create_deferred_indexes(db: AsyncEngine, metadata: MetaData) -> None:
    """
    Creates the indexes that `create_db` held back.
    Call this once all data has been inserted, but before querying it.
    """
    async with db.begin() as tx:
        for index in deferred_indexes(metadata):
            await tx.run_sync(lambda connection, index=index: index.create(connection, checkfirst=True))

        await tx.commit()


def build_metadata(model_types: Iterable[type[DatabaseModel]]) -> MetaData:
    """Returns the tables that `model_types` are stored in."""
    metadata = MetaData()
    for model_type in model_types:
        model_type.create_tables(metadata)

    return metadata


async def create_db(path: Path, model_types: Iterable[type[DatabaseModel]]) -> tuple[AsyncEngine, MetaData]:
    db = create_async_engine(
        f"sqlite+aiosqlite:///{path}",
        connect_args={
            "check_same_thread": False,
            "autocommit": False,
        },
    )

    metadata = build_metadata(model_types)

    # Hold back the indexes that aren't needed while the database is being filled,
    # so that the bulk inserts don't have to maintain them row by row.
    # `create_deferred_indexes` puts them back once the data is in.
    deferred = deferred_indexes(metadata)
    for index in deferred:
        index.table.indexes.discard(index)

    @event.listens_for(db.sync_engine, "connect")
    def set_common_pragmas(dbapi_connection, connection_record):
        # `synchronous` and `journal_mode` can't be changed inside a transaction,
        # and the engine is configured to keep one open at all times.
        # SQLAlchemy wraps the aiosqlite connection, which in turn wraps the sqlite3 one.
        raw_connection = dbapi_connection.driver_connection._conn
        previous_autocommit = raw_connection.autocommit
        raw_connection.autocommit = True

        # Don't wait for the filesystem to confirm each commit.
        # Every commit would otherwise cost a flush to disk,
        # which dominates the runtime when the index is built
        # out of many small transactions.
        dbapi_connection.execute("PRAGMA synchronous = OFF")

        # Use in-memory journaling for better performance at the expense of durability,
        # but that's okay since the database is just used as a local cache
        # (as opposed to persistent storage of critical data).
        dbapi_connection.execute("PRAGMA journal_mode = MEMORY")

        # Keep a healthy page cache and all temporary tables in RAM;
        # the index is built in one pass and is far bigger than the default 2 MiB cache.
        # Every connection gets its own cache, so this isn't free.
        # (Negative values are in KiB, so this is 256 MiB.)
        dbapi_connection.execute("PRAGMA cache_size = -262144")
        dbapi_connection.execute("PRAGMA temp_store = MEMORY")

        # Explicitly disable foreign key constraints for two reasons:
        # 1. Some data sources may refer to newer games
        #    that we're not interested in tracking in RetroArch,
        #    like current-gen remakes of SNES games.
        #    We want to keep the IDs in the database so we can query exclusivity.
        # 2. Enforcing foreign key constraints would require that
        #    related records be inserted in the same transaction.
        #
        # Foreign key constraints are still useful for visualizing or browsing
        # the raw SQLite database, even if they're not enforced at runtime.
        #
        # SQLite doesn't enforce foreign key constraints by default,
        # but the docs say that could change in the future.
        dbapi_connection.execute("PRAGMA foreign_keys = OFF")

        raw_connection.autocommit = previous_autocommit

    async with db.connect() as connection:
        await connection.run_sync(metadata.create_all)
        await connection.commit()

        await connection.execute(text("PRAGMA optimize"))

    for index in deferred:
        index.table.indexes.add(index)

    return (db, metadata)

type CoercedHttpUrl = Annotated[HttpUrl, WrapValidator(lambda v, h: h(v) if v else None), PlainSerializer(str, str)]
type InsertInRowContext = Literal['row'] | None

def validate_frozendict(v: Any, handler: ValidatorFunctionWrapHandler) -> frozendict[Any, Any]:
    if isinstance(v, frozendict):
        return v

    if isinstance(v, Mapping):
        return frozendict(handler(v))

    raise TypeError(f"Expected frozendict or Mapping, got {type(v)}")

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

def ZeroPad(min_length: int):
    return BeforeValidator(lambda s: s.zfill(min_length))

type FrozenDict[K, V] = Annotated[frozendict[K, V], GetPydanticSchema(_frozen_dict_schema)]
type TypedFrozenDict[T] = Annotated[T, AfterValidator(lambda v: frozendict(v))]
# NOTE: The pattern is in Rust syntax, not Python syntax! (Pydantic-core is implemented in Rust.)
Crc = Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True, pattern=r"^[a-fA-F0-9]{8}$")]
Md5 = Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True, pattern=r"^[a-fA-F0-9]{32}$")]
Sha1 = Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True, pattern=r"^[a-fA-F0-9]{40}$")]
Sha256 = Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True, pattern=r"^[a-fA-F0-9]{64}$")]

type FrozenJsonValue = tuple[FrozenJsonValue, ...] | FrozenDict[str, FrozenJsonValue] | str | bool | int | float | None

type WrapInTuple[T] = Annotated[tuple[T, ...], BeforeValidator(lambda v: always_iterable(v))]
type OnlyFirst[T] = Annotated[T, BeforeValidator(lambda v: v[0] if is_non_string_iterable(v) and isinstance(v, Sequence) else v)]

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

type CliTuple[T] = Annotated[tuple[T, ...], NoDecode, BeforeValidator(_split_cli_csv)]
"""
A tuple field that can be given on the command line
as one comma-separated argument or as a repeated argument.
"""

PARENT_DIR = Path(__file__).parent.parent

class PoolArgs:
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
    "DatabaseModel",
    "build_metadata",
    "create_deferred_indexes",
    "deferred_indexes",
    "DEFAULT_DAT_CONCURRENCY",
    "DEFAULT_IGDB_CONCURRENCY",
    "DEFAULT_HASHEOUS_CONCURRENCY",
    "RowDeduplicator",
    "ExtractedRows",
    "RowAccumulator",
    "extract_rows",
    "CliTuple",
    "Relationship",
    "Sha256",
    "Sha1",
    "Md5",
    "Crc",
    "EmptyStringToNone",
    "is_non_string_sequence_type",
    "CoercedHttpUrl",
    "InsertInRowContext",
    "WrapInTuple",
    "FrozenDict",
)