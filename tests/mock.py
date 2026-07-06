import re
from contextlib import contextmanager


class MockResource:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def write(self, query):
        pass


class MockCursor:
    def __init__(self):
        self.result = []
        self.rowcount = 0
        self.lastQuery = ""
        self.lastParams = []

    def mogrify(self, query, params=None):
        return None

    def execute(self, query, params=None):
        if query == "":
            self.result = []
            self.rowcount = 0
        self.lastQuery = re.sub(r"\s+", " ", query).strip()
        self.lastParams = params

    def fetchone(self) -> list:
        return self.result

    def fetchall(self) -> list:
        return self.result

    def __iter__(self):
        return iter(self.result)

    @contextmanager
    def copy(self, *args, **kwds):
        with MockResource() as copy:
            yield copy
