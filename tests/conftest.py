import configparser
import os

import pytest

from telecoopcommon.logs import initLogs


@pytest.fixture(scope="module")
def test_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config["Log"] = {"folder": "/var/log/common/", "log-level": "INFO", "console": True}  # pyright: ignore[reportArgumentType]
    return config


@pytest.fixture(scope="module")
def test_logger(test_config):
    logger = initLogs("telecoop-common", test_config["Log"], strDesiredLogLevel="DEBUG")
    return logger
