import pytest

from telecoopcommon.config import TcConfig
from telecoopcommon.logs import initLogs


@pytest.fixture(scope="module")
def test_config() -> dict:
    return TcConfig()


@pytest.fixture(scope="module")
def test_logger(test_config):
    logger = initLogs("telecoop-common", test_config["Log"], strDesiredLogLevel="DEBUG")
    return logger
