from dataclasses import InitVar, dataclass, field, fields

import inflection
from psycopg import Cursor, sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class NotInDBError(RuntimeError):
    pass


class NamingError(TypeError):
    pass


@dataclass
class TcDataClass:
    id: int | None
    schema: InitVar[str | None] = None
    tableName: InitVar[str | None] = None
    cursor: InitVar[Cursor | None] = None
    allData: InitVar[bool] = field()
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
        self.schema, self.tableName = self.__class__.__get_schema_and_table__()
        self.cursor = cursor
        self.allData = allData

    def save(self):
        if not hasattr(self, "id"):
            raise RuntimeError("Can't handle save without id column")

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
        if self.allData:
            query += onConflict
        else:
            # Updates that does nothing so that RETURNING * returns something
            query += "ON CONFLICT({{naturalKey}}) DO UPDATE SET {updateNkValues}"
            updateNkValues = ",".join(
                [f"{{{f}}} = EXCLUDED.{{{f}}}" for f in self.NATURAL_KEY]
            )

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
            schema=sql.Identifier(self.schema),
            tableName=sql.Identifier(self.tableName),
            naturalKey=sql.SQL(",").join([sql.Identifier(f) for f in self.NATURAL_KEY]),
            fields=sql.SQL(",").join([sql.Identifier(f.name) for f in columns]),
            **({f.name: sql.Identifier(f.name) for f in columns}),
        )
        rowStyle = self.cursor.row_factory
        self.cursor.row_factory = dict_row
        self.cursor.execute(
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
            result = self.cursor.fetchone()
            for k, v in result.items():
                setattr(self, k, v)
            self.allData = True
        self.cursor.row_factory = rowStyle

    def load(self, **kwargs):
        if len(kwargs) == 0:
            if hasattr(self, "id") and self.id is not None:
                kwargs = {"id": self.id}
            else:
                kwargs = {}
                for f in self.NATURAL_KEY:
                    assert getattr(self, f) is not None, f"{f} is None"
                    kwargs[f] = getattr(self, f)
        values = self.__class__.__get_values__(
            self.schema, self.tableName, self.cursor, **kwargs
        )
        if values is None:
            if hasattr(self, "id") and self.id is not None:
                raise NotInDBError(f"{self.id} not found")
            else:
                key = ",".join(map(str, [getattr(self, f) for f in self.NATURAL_KEY]))
                raise NotInDBError(f"{key} not found")
        for f in fields(self):
            setattr(self, f.name, values[f.name])
        self.allData = True

    @classmethod
    def _getFields(cls):
        return sql.SQL(",").join([sql.Identifier(f.name) for f in fields(cls)])

    @classmethod
    def __get_values__(cls, schema, tableName, cursor, **kwargs):
        if (
            "id" not in kwargs
            and len(kwargs) != len(cls.NATURAL_KEY)
            and set(kwargs) != set(cls.NATURAL_KEY)
        ):
            raise RuntimeError(
                f"Expected either id or those params : {cls.NATURAL_KEY}, got {kwargs}"
            )
        query = """
          SELECT {fields}
            FROM {schema}.{tableName}
           WHERE
        """
        if "id" in kwargs:
            query += "id = %(id)s"
        else:
            query += " AND ".join([f"{{{k}}} = %({k})s" for k in cls.NATURAL_KEY])
        rowStyle = cursor.row_factory
        cursor.row_factory = dict_row
        cursor.execute(
            sql.SQL(query).format(
                schema=sql.Identifier(schema),
                tableName=sql.Identifier(tableName),
                fields=cls._getFields(),
                **({k: sql.Identifier(k) for k in cls.NATURAL_KEY}),
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
    def __getMany__(cls, cursor, query):
        schema, tableName = cls.__get_schema_and_table__()

        rowStyle = cursor.row_factory
        cursor.row_factory = dict_row
        cursor.execute(
            sql.SQL(query).format(
                fields=cls._getFields(),
                schema=sql.Identifier(schema),
                tableName=sql.Identifier(tableName),
            )
        )
        results = cursor.fetchall()
        cursor.row_factory = rowStyle
        return [cls(cursor=cursor, allData=True, **row) for row in results]
