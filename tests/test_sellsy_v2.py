import pytest

from telecoopcommon import sellsy


@pytest.fixture(scope="module")
def test_connector_v2(test_config, test_logger):
    return sellsy.TcSellsyConnectorV2(test_config["Sellsy"], test_logger)


@pytest.mark.skip(reason="Can only be run manualy on live Sellsy Dev environment")
class TestSellyV2:
    def test_get_opportunity(self, test_connector_v2):
        token = test_connector_v2._getToken()
        assert token.access_token

    def test_linkSmartTagToOpportunity(self, test_connector_v2):
        test_connector_v2.linkSmartTagToOpportunity(11122521, "test")
        test_connector_v2.linkSmartTagToOpportunity(11122521, "test2")

    def test_linkSmartTagToInvoice(self, test_connector_v2):
        test_connector_v2.linkSmartTagToInvoice(52697614, "test")
        test_connector_v2.linkSmartTagToInvoice(52697614, "test2")
