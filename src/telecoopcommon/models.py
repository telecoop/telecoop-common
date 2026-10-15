from dataclasses import InitVar, dataclass, fields
from datetime import date, datetime

import inflection
from psycopg import Cursor, sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from telecoopcommon.cursor import TcCursor


class NotInDBError(RuntimeError):
    pass


class NamingError(TypeError):
    pass


@dataclass
class TcDataClassBase:
    schema: InitVar[str | None] = None
    tableName: InitVar[str | None] = None
    cursor: InitVar[Cursor | None] = None
    allData: InitVar[bool] = False
    NATURAL_KEY = []

    @classmethod
    def __get_schema_and_table__(cls):
        splits = [s for s in cls.__name__.split("_")]
        if len(splits) != 2:
            raise NamingError("Expecting name to be Schema_Tablename")
        schemaName = splits[0].lower()
        tableName = inflection.underscore(splits[1])
        return (schemaName, tableName)

    def __post_init__(self, schema, tableName, cursor, allData):
        self._schema, self._tableName = self.__class__.__get_schema_and_table__()
        self._cursor = cursor
        self._allData = allData

    @classmethod
    def _getFields(cls):
        return sql.SQL(",").join([sql.Identifier(f.name) for f in fields(cls)])

    @classmethod
    def _hasIdentifier(cls, **kwargs):
        return len(kwargs) == len(cls.NATURAL_KEY) and set(kwargs) == set(
            cls.NATURAL_KEY
        )

    @classmethod
    def _getIdentifierFilter(cls, **kwargs):
        if not cls._hasIdentifier(**kwargs):
            raise RuntimeError(
                f"Expected either id or those params : {cls.NATURAL_KEY}, got {kwargs}"
            )
        # Don't use f"{}" form to keep query type as LiteralString
        return " AND ".join(["{" + k + "} = %(" + k + ")s" for k in cls.NATURAL_KEY])

    @classmethod
    def __get_values__(cls, schema, tableName, cursor, **kwargs):
        query = """
          SELECT {fields}
            FROM {schema}.{tableName}
           WHERE
        """
        query += cls._getIdentifierFilter(**kwargs)
        rowStyle = cursor.row_factory
        cursor.row_factory = dict_row
        identifierFields = {k: sql.Identifier(k) for k in cls.NATURAL_KEY}
        cursor.execute(
            sql.SQL(query).format(
                schema=sql.Identifier(schema),
                tableName=sql.Identifier(tableName),
                fields=cls._getFields(),
                **identifierFields,
            ),
            kwargs,
        )
        result = cursor.fetchone()
        cursor.row_factory = rowStyle
        return result

    @classmethod
    def fromDb(cls, cursor, **kwargs):
        schema, tableName = cls.__get_schema_and_table__()
        values = cls.__get_values__(cursor, schema, tableName, **kwargs)
        return cls(cursor=cursor, allData=True, **values)

    @classmethod
    def __getMany__(cls, cursor, query, params=None):
        schema, tableName = cls.__get_schema_and_table__()

        rowStyle = cursor.row_factory
        cursor.row_factory = dict_row
        cursor.execute(
            sql.SQL(query).format(
                fields=cls._getFields(),
                schema=sql.Identifier(schema),
                tableName=sql.Identifier(tableName),
            ),
            params,
        )
        results = cursor.fetchall()
        cursor.row_factory = rowStyle
        return [cls(cursor=cursor, allData=True, **row) for row in results]

    def load(self, **kwargs):
        if len(kwargs) == 0:
            kwargs = {}
            for f in self.NATURAL_KEY:
                assert getattr(self, f) is not None, f"{f} is None"
                kwargs[f] = getattr(self, f)
        values = self.__class__.__get_values__(
            self._schema, self._tableName, self._cursor, **kwargs
        )
        if values is None:
            key = ",".join(map(str, [getattr(self, f) for f in self.NATURAL_KEY]))
            raise NotInDBError(f"{key} not found")
        for f in fields(self):
            setattr(self, f.name, values[f.name])
        self._allData = True


@dataclass
class TcDataClassView(TcDataClassBase):
    def save(self):
        raise RuntimeError("It's a view, no saving ;-)")


@dataclass
class TcDataClass(TcDataClassBase):
    id: int | None = None

    @classmethod
    def _hasIdentifier(cls, **kwargs):
        return "id" in kwargs or super()._hasIdentifier(**kwargs)

    @classmethod
    def _getIdentifierFilter(cls, **kwargs):
        result = ""
        if "id" in kwargs:
            result = "id = %(id)s"
        else:
            result = super()._getIdentifierFilter(**kwargs)
        return result

    def save(self):
        query = """
          INSERT INTO {{schema}}.{{tableName}} ({{fields}}) VALUES ({insertValues})
        """
        onConflict = """
          ON CONFLICT (id) DO UPDATE
          SET {updateValues}
        """
        if self.id is None:
            onConflict = """
              ON CONFLICT ({{naturalKey}}) DO UPDATE
              SET {updateValues}
            """
        # If all data are loaded we can upsert
        updateNkValues = ""
        if self._allData:
            query += onConflict
        else:
            # Updates that does nothing so that RETURNING * returns something
            query += "ON CONFLICT({{naturalKey}}) DO UPDATE SET {updateNkValues}"
            updateNkValues = ",".join(
                [f"{{{f}}} = EXCLUDED.{{{f}}}" for f in self.NATURAL_KEY]
            )

        for upperBound in ["date_end", "date_terminated"]:
            if (
                hasattr(self, upperBound)
                and not self._allData
                and getattr(self, upperBound) is None
            ):
                setattr(self, upperBound, "infinity")

        if self.id is None:
            query += " RETURNING *"

        # Create date has always a default value of now()
        columns = [
            f for f in fields(self) if f.name not in ["date_created", "date_updated"]
        ]
        # If column id is present and is not NULL, we'll be doing
        # 1. an insert during which we'll use the primary key default value
        # 2. OR an update and we don't want to update this column
        if self.id is None:
            columns = [c for c in columns if c.name != "id"]

        query = query.format(
            insertValues=",".join([f"%({f.name})s" for f in columns]),
            updateValues=",".join(
                [
                    f"{{{f.name}}} = EXCLUDED.{{{f.name}}}"
                    for f in columns
                    if f.name != "id"
                ]
                + ["date_updated = DEFAULT"]
            ),
            updateNkValues=updateNkValues,
        )
        query = sql.SQL(query).format(
            schema=sql.Identifier(self._schema),
            tableName=sql.Identifier(self._tableName),
            naturalKey=sql.SQL(",").join([sql.Identifier(f) for f in self.NATURAL_KEY]),
            fields=sql.SQL(",").join([sql.Identifier(f.name) for f in columns]),
            **({f.name: sql.Identifier(f.name) for f in columns}),
        )
        rowStyle = self._cursor.row_factory
        self._cursor.row_factory = dict_row
        self._cursor.execute(
            query,
            {
                f.name: (
                    Jsonb(getattr(self, f.name))
                    if str(f.type)[0:4] == "dict"
                    else getattr(self, f.name)
                )
                for f in columns
            },
        )
        if self.id is None:
            result = self._cursor.fetchone()
            for k, v in result.items():
                setattr(self, k, v)
            self._allData = True
        self._cursor.row_factory = rowStyle

    def load(self, **kwargs):
        if len(kwargs) == 0:
            if self.id is not None:
                kwargs = {"id": self.id}
            else:
                kwargs = {}
                for f in self.NATURAL_KEY:
                    assert getattr(self, f) is not None, f"{f} is None"
                    kwargs[f] = getattr(self, f)
        values = self.__class__.__get_values__(
            self._schema, self._tableName, self._cursor, **kwargs
        )
        if values is None:
            if self.id is not None:
                raise NotInDBError(f"{self.id} not found")
            else:
                key = ",".join(map(str, [getattr(self, f) for f in self.NATURAL_KEY]))
                raise NotInDBError(f"{key} not found")
        for f in fields(self):
            setattr(self, f.name, values[f.name])
        self._allData = True


@dataclass
class Crm_Client(TcDataClass):
    id: int | None = None
    reference: str | None = None
    name: str | None = None
    firstname: str | None = None
    email: str | None = None
    create_date: datetime | None = None
    sellsy_id: int | None = None
    phone_number: str | None = None
    sellsy_status: str | None = None
    client_type: str | None = None
    company_name: str | None = None
    is_pro: bool | None = None
    automatic_validation: bool | None = None
    birthdate: date | None = None
    referee_code: str = ""
    sponsor_code: str = ""
    promo_code: str = ""
    discounts: int | None = None
    preferred_payment_method: str | None = None
    slimpay_mandate_status: str | None = None
    NATURAL_KEY = ["reference"]

    @classmethod
    def fromSellsyId(cls, sellsyId: int, cursor: TcCursor):
        query = """
          SELECT {fields}
            FROM {schema}.{tableName}
           WHERE sellsy_id = %s
        """
        result = cls.__getMany__(cursor, query, params=[sellsyId])
        if len(result) == 0:
            raise NotInDBError()
        return result.pop(0)

    @classmethod
    def fromReference(cls, reference: str, cursor: TcCursor):
        query = """
          SELECT {fields}
            FROM {schema}.{tableName}
           WHERE reference = %s
        """
        result = cls.__getMany__(cursor, query, params=[reference])
        if len(result) == 0:
            raise NotInDBError()
        return result.pop(0)
