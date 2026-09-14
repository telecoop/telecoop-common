import os

import pytest

from telecoopcommon.config import TcConfig
from telecoopcommon.sellsy.sellsyConnectorV2 import TcSellsyConnectorV2
from telecoopcommon.sellsy.sellsyFile import SellsyFile


@pytest.fixture(scope="module")
def test_connector_v2(test_config, test_logger):
    return TcSellsyConnectorV2(test_config["Sellsy"], test_logger)


@pytest.mark.skipif("Sellsy" not in TcConfig(), reason="Sellsy not in config")
class TestSellyV2:
    @pytest.mark.skip("Not yes implemented")
    def test_get_opportunity(self, test_connector_v2: TcSellsyConnectorV2):
        token = test_connector_v2._getToken()
        assert token.access_token
        assert test_connector_v2.getOpportunity("11122521") == "4"

    def test_linkSmartTagToOpportunity(self, test_connector_v2: TcSellsyConnectorV2):
        test_connector_v2.linkSmartTagToObject("opportunities", 11122521, "test")
        test_connector_v2.linkSmartTagToObject("opportunities", 11122521, "test2")

    def test_linkSmartTagToInvoice(self, test_connector_v2: TcSellsyConnectorV2):
        test_connector_v2.linkSmartTagToObject("invoices", 52697614, "test")
        test_connector_v2.linkSmartTagToObject("invoices", 52697614, "test2")

    def test_fileUploadAndDelete(self, test_connector_v2: TcSellsyConnectorV2):
        # create dummy file
        fileName = "dummy.pdf"
        with open(fileName, "wb") as file:
            file.write(b"Telecoop rocks!\n")

        # upload file
        created, response = SellsyFile(test_connector_v2).upload(
            "testfolder",
            fileName,
            "application/pdf",
            "opportunities",
            "11121827",
        )
        assert created is True
        fileId = response["id"]

        # delete file in Sellsy
        SellsyFile(test_connector_v2).delete(fileId)

        # clean
        os.remove(fileName)
