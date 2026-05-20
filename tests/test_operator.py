from datetime import datetime, timedelta

import pytest
import requests
import responses
from freezegun import freeze_time

from telecoopcommon import operator

TEST_HOST = "https://phenix-test.telecoop.fr"


@pytest.fixture(scope="function")
def phenixConnector(test_logger):
    config = {
        "host": TEST_HOST,
        "login": "",
        "password": "",
        "partnerId": "",
        "purchaseCostCode": "",
    }
    return operator.PhenixConnector(config, test_logger)


class TestOperator:
    @responses.activate
    def test_phenixToken(self, phenixConnector):
        # Init
        now = datetime.now()
        PHENIX_TOKEN_EXPIRY_HOURS = 4

        # Mock http requests
        # First response
        responses.add(
            responses.POST,
            f"{TEST_HOST}/Auth/authenticate",
            json={
                "access_token": "supertesttoken",
                "expires_in": PHENIX_TOKEN_EXPIRY_HOURS * 3600,
            },
            status=200,
        )
        # Second response
        responses.add(
            responses.POST,
            f"{TEST_HOST}/Auth/authenticate",
            json={
                "access_token": "supertesttoken2",
                "expires_in": PHENIX_TOKEN_EXPIRY_HOURS * 3600,
            },
            status=200,
        )

        # get a first token from Phenix
        token = phenixConnector.getToken()

        # get a second token and make sure it is the same one
        token2 = phenixConnector.getToken()
        assert token == token2

        # get a third token in the future a make sure its a new one
        with freeze_time(now + timedelta(hours=PHENIX_TOKEN_EXPIRY_HOURS, seconds=10)):
            token3 = phenixConnector.getToken()
            assert token != token3
