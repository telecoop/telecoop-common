from datetime import datetime

import pytest
import responses

from telecoopcommon.telecommown import TeleCommownConnector


@pytest.fixture(scope="class")
def test_connector(test_config, test_logger):
    return TeleCommownConnector(
        "https://fake_host.fr",
        "test_user",
        "test_password",
        "testsalt",
        test_logger,
    )


class TestTeleCommown:
    @responses.activate
    def test_optin(self, test_connector):
        mobile = "0600000000"
        optoutDate = datetime.now()

        # mock the opt-in route
        responses.add(
            responses.POST,
            f"{test_connector._host}/campaigns/TeleCommown2021/opt-in",
            json={},
            status=200,
        )

        # check
        test_connector.optin(mobile, optoutDate)

    @responses.activate
    def test_optout(self, test_connector):
        mobile = "0600000000"
        optoutDate = datetime.now()

        # mock the opt-out route
        responses.add(
            responses.POST,
            f"{test_connector._host}/campaigns/TeleCommown2021/opt-out",
            json={},
            status=200,
        )

        # check
        test_connector.optout(mobile, optoutDate)

    def test_getKey(self, test_connector):
        """Simple test to ensure we don't break key hashing in the future"""
        test_connector._salt = "testsalt"  # override salt
        assert (
            test_connector.getKey("0600000000")
            == "38037ff8bab6f9c1dbe8403321614d39be2cd7a6f2bdc598891e935d453f66d8"
        )

    @responses.activate
    def test_getImportantEvents(self, test_connector):
        startDate = datetime.now()
        endDate = datetime.now()

        # mock the important-events route
        responses.add(
            responses.GET,
            f"{test_connector._host}/campaigns/TeleCommown2021/subscriptions/important-events",
            json={},
            status=200,
        )

        # check
        test_connector.getImportantEvents(startDate, endDate)

    @responses.activate
    def test_notifyNewClients(self, test_connector):

        class Client:
            msisdn = "0600000000"
            startDate = datetime.now()

        # mock the opt-in route
        responses.add(
            responses.POST,
            f"{test_connector._host}/campaigns/TeleCommown2021/opt-in",
            json={},
            status=200,
        )

        # check
        test_connector.notifyNewClients([Client()])
