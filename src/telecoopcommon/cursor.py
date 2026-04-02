class TcCursor:
    def __init__(self, cursor, logger):
        self._cursor = cursor
        self.logger = logger
        self.rowcount = None

    def execute(self, query, params=None):
        text = self._cursor.mogrify(query, params)
        if "decode" in dir(text):
            text = text.decode()
        self.logger.debug(text)
        self._cursor.execute(query, params)
        self.rowcount = self._cursor.rowcount

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchone(self):
        return self._cursor.fetchone()

    def copy_expert(self, query, file):
        result = None
        if hasattr(self._cursor, "copy_expert"):
            result = self._cursor.copy_expert(query, file)
        else:
            with self._cursor.copy(query) as copy:
                if "TO STDOUT" in query or "to stdout" in query:
                    file.write(copy.read())
                elif "FROM STDIN" in query or "from stdin" in query:
                    copy.write(file.read())
        return result

    def copy(self, query):
        return self._cursor.copy(query)

    def __iter__(self):
        return iter(self._cursor)

    # Use only if self._cursor is from psycopg 3
    @property
    def row_factory(self):
        return self._cursor.row_factory

    @row_factory.setter
    def row_factory(self, rowStyle):
        self._cursor.row_factory = rowStyle
