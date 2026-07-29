import asyncio

import pytest

from telecoopcommon import runner
from tests import mock


def test_execWithLogsSync(test_config, test_logger):
    def mockfunction():
        print("dumb")

    def mockfunctionRaise():
        raise Exception("dumb")

    def getMockCursor(db: str = "main"):
        cursor = mock.MockCursor()
        cursor.result = [1]
        return cursor

    # create runner
    testRunner = runner.TcRunner("DEV", test_config, test_logger, "", "test")

    # mock getCursor
    testRunner.getCursor = getMockCursor  # pyright: ignore[reportAttributeAccessIssue]

    # run
    testRunner.execWithLogs("fake-command", mockfunction, noLog=False)

    # run with raise
    with pytest.raises(Exception):
        testRunner.execWithLogs("fake-command", mockfunctionRaise, noLog=False)


def test_execWithLogsAsync(test_config, test_logger):
    cursor = mock.MockCursor()
    COUNT = 0
    cursor.result = [COUNT]  # fake result returning count() = 0
    EXCEP = "fake-test-exception"

    async def mockfunction():
        print("dumb")

    async def mockfunctionRaise():
        raise Exception(EXCEP)

    def getMockCursor(db: str = "main"):
        return cursor

    # create runner
    testRunner = runner.TcRunner("DEV", test_config, test_logger, "", "test")

    # mock getCursor
    testRunner.getCursor = getMockCursor  # pyright: ignore[reportAttributeAccessIssue]

    # run
    asyncio.run(testRunner.execWithLogsAsync("fake-command", mockfunction, noLog=False))

    # run with raise
    with pytest.raises(Exception):
        asyncio.run(
            testRunner.execWithLogsAsync("fake-command", mockfunctionRaise, noLog=False)
        )

    assert EXCEP in cursor.lastParams[0]  # pyright: ignore[reportOptionalSubscript]
    assert cursor.lastParams[1] == COUNT  # pyright: ignore[reportOptionalSubscript]


def test_getArg(test_config, test_logger):
    class ArgMock:
        arguments = ["abc", "a,b,c", "3"]

    # create runner
    testRunner = runner.TcRunner("DEV", test_config, test_logger, ArgMock(), "test")

    # # mock getCursor
    # testRunner.getCursor = getMockCursor  # pyright: ignore[reportAttributeAccessIssue]

    assert testRunner.getArg("test") == "abc"
    assert testRunner.getArg("test2", "list") == ["a", "b", "c"]
    assert testRunner.getArg("test3", "int") == 3
