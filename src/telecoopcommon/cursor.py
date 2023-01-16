class TcCursor:
    def __init__(self, cursor, logger):
        self._cursor = cursor
        self.logger = logger
        self.rowcount = None

    def execute(self, query, params=None):
        self.logger.debug(self._cursor.mogrify(query, params).decode())
        self._cursor.execute(query, params)
        self.rowcount = self._cursor.rowcount

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchone(self):
        return self._cursor.fetchone()

    def copy_expert(self, query, file):
        return self._cursor.copy_expert(query, file)

    def __iter__(self):
        return iter(self._cursor)
