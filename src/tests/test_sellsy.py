import configparser
import pytest
import pytz
from datetime import datetime
from telecoopcommon import sellsy

confFile = "/etc/telecoop-common/conf.cfg"
config = configparser.ConfigParser()
config.read(confFile)

parisTZ = pytz.timezone("Europe/Paris")

clientIdPG = 34246953
opportunityIdPG = 5366993
clientIdNoOpportunity = 33309487


class Logger:
    def critical(self, message):
        return None

    def warning(self, message):
        return None

    def info(self, message):
        print(message)

    def debug(self, message):
        print(message)


@pytest.fixture(scope="module")
def test_connector():
    return sellsy.TcSellsyConnector(config["SellsyDev"], Logger())


def test_get_opportunity(test_connector):
    id = opportunityIdPG
    cf = sellsy.sellsyValues["DEV"]["custom_fields"]
    d = datetime.now()
    now = parisTZ.localize(datetime(year=d.year, month=d.month, day=d.day))
    timestamp = now.timestamp()
    test_connector.updateCustomField("opportunity", id, cf["nsce"], "1234")
    test_connector.updateCustomField(
        "opportunity", id, cf["numerotelecoop"], "0610658239"
    )
    test_connector.updateCustomField("opportunity", id, cf["rio"], "1111")
    test_connector.updateCustomField("opportunity", id, cf["forfait"], "Sobriété")
    test_connector.updateCustomField("opportunity", id, cf["refbazile"], "2222")
    test_connector.updateCustomField("opportunity", id, cf["achatsimphysique"], True)
    test_connector.updateCustomField(
        "opportunity", id, cf["date-activation-sim-souhaitee"], timestamp
    )
    test_connector.updateCustomField(
        "opportunity", id, cf["offre-telecommown"], timestamp
    )
    test_connector.updateCustomField(
        "opportunity", id, cf["telecommown-date-debut"], timestamp
    )
    test_connector.updateCustomField(
        "opportunity", id, cf["telecommown-date-fin"], timestamp
    )
    test_connector.updateCustomField(
        "opportunity", id, cf["telecommown-origine"], "TeleCoop"
    )
    test_connector.updateCustomField("opportunity", id, cf["abo-telecommown"], "Y")
    test_connector.updateCustomField("opportunity", id, cf["code-promo"], "TESTCODE")
    test_connector.updateCustomField(
        "opportunity", id, cf["parrainage-code-parrain"], "CODEPAR"
    )
    test_connector.updateCustomField("opportunity", id, cf["pack-depannage"], 1)

    o = sellsy.SellsyOpportunity(id)
    o.load(test_connector)
    assert o.clientId == str(clientIdPG), "Check client id"
    assert o.nsce == "1234", "Check nsce"
    assert o.msisdn == "0610658239", "Check msisdn"
    assert o.rio == "1111", "Check RIO"
    assert o.plan == "Sobriété", "Check forfait"
    assert o.operatorRef == "2222", "Check Bazile number"
    assert o.achatSimPhysique is True, "Check achat sim physique"
    assert o.dateActivationSimAsked == now, "Check date activation SIM souhaitée"
    assert o.optinTeleCommown == now, "Check optin telecommown"
    assert o.telecommownStart == now, "Check telecommown start"
    assert o.telecommownEnd == now, "Check telecommown end"
    assert o.telecommownOrigin == "TeleCoop", "Check telecommown origine"
    assert o.telecommownAbo is True, "Check telecommown abo"
    assert o.promoCode == "TESTCODE", "Check promo code"
    assert o.refereeCode == "CODEPAR", "Check referee code"
    assert o.packDepannage == 1, "Check pack dépannage"

    test_connector.updateCustomField("opportunity", id, cf["nsce"], "4321")
    test_connector.updateCustomField(
        "opportunity", id, cf["numerotelecoop"], "0610658238"
    )
    test_connector.updateCustomField("opportunity", id, cf["rio"], "2222")
    test_connector.updateCustomField("opportunity", id, cf["forfait"], "Transition")
    test_connector.updateCustomField("opportunity", id, cf["refbazile"], "1111")
    test_connector.updateCustomField("opportunity", id, cf["achatsimphysique"], "N")
    # test_connector.updateCustomField('opportunity', id, cf['date-activation-sim-souhaitee'], None)
    test_connector.updateCustomField("opportunity", id, cf["code-promo"], "TESTCODE2")
    test_connector.updateCustomField(
        "opportunity", id, cf["parrainage-code-parrain"], "CODEPAR2"
    )
    test_connector.updateCustomField("opportunity", id, cf["pack-depannage"], 2)

    o = sellsy.SellsyOpportunity(id)
    o.load(test_connector)
    assert o.nsce == "4321", "Check nsce"
    assert o.msisdn == "0610658238", "Check msisdn"
    assert o.rio == "2222", "Check RIO"
    assert o.plan == "Transition", "Check forfait"
    assert o.operatorRef == "1111", "Check Bazile number"
    assert o.achatSimPhysique is False, "Check achat sim physique"
    # assert o.dateActivationSimAsked is None, "Check date activation SIM souhaitée"
    assert o.promoCode == "TESTCODE2"
    assert o.refereeCode == "CODEPAR2", "Check referee code"
    assert o.packDepannage == 2, "Check pack dépannage"


def test_get_client(test_connector):
    id = clientIdPG
    cf = sellsy.sellsyValues["DEV"]["custom_fields"]
    d = datetime.now()
    now = parisTZ.localize(datetime(year=d.year, month=d.month, day=d.day))
    timestamp = now.timestamp()
    test_connector.updateClientProperty(id, "mobile", "0610658239")
    test_connector.updateClientProperty(id, "email", "pierre@afeu.fr")
    test_connector.updateCustomField("client", id, cf["refbazile"], "1234")
    test_connector.updateCustomField(
        "client", id, cf["facturationmanuelle"], "automatique"
    )
    test_connector.updateCustomField("client", id, cf["facture-unique"], "Y")
    test_connector.updateCustomField(
        "client", id, cf["statut-client-abo-mobile"], "Actif"
    )
    test_connector.updateCustomField("client", id, cf["parrainage-code"], "BBBB")
    test_connector.updateCustomField("client", id, cf["parrainage-lien"], "LLLL")
    test_connector.updateCustomField("client", id, cf["parrainage-code-nb-use"], 2)
    test_connector.updateCustomField("client", id, cf["parrainage-nb-discount"], 1)
    test_connector.updateCustomField(
        "client", id, cf["parrainage-code-parrain"], "CCCC"
    )
    test_connector.updateCustomField("client", id, cf["parrainage-nb-code-donated"], 1)
    test_connector.updateCustomField("client", id, cf["offre-telecommown"], timestamp)
    test_connector.updateCustomField(
        "client", id, cf["telecommown-date-debut"], timestamp
    )
    test_connector.updateCustomField(
        "client", id, cf["telecommown-date-fin"], timestamp
    )
    test_connector.updateCustomField(
        "client", id, cf["telecommown-origine"], "TeleCoop"
    )
    test_connector.updateCustomField("client", id, cf["abo-telecommown"], "Y")
    test_connector.updateCustomField("client", id, cf["code-promo"], "TESTCODE")

    c = sellsy.SellsyClient(id)
    c.load(test_connector)
    assert c.msisdn == "+33610658239", "Check mobile"
    assert c.email == "pierre@afeu.fr", "Check email"
    assert c.lines[0]["operatorRef"] == "1234", "Check bazile num"
    assert c.autoValidation is True, "Check autovalidation"
    assert c.oneInvoicePerLine is False, "Check facture unique"
    assert c.status == "Actif", "Check status"
    assert c.sponsorCode == "BBBB", "Check sponsor code"
    assert c.sponsorLink == "LLLL", "Check sponsor link"
    assert c.sponsorNbUse == 2, "Check sponsor nb code"
    assert c.sponsorNbDiscount == 1, "Check sponsor nb discount"
    assert c.refereeCode == "CCCC", "Check referee code"
    assert c.sponsorNbCodeDonated == 1, "Check sponsor nb code donated"
    assert c.optinTeleCommown == now, "Check optin telecommown"
    assert c.telecommownStart == now, "Check telecommown start"
    assert c.telecommownEnd == now, "Check telecommown end"
    assert c.telecommownOrigin == "TeleCoop", "Check telecommown origine"
    assert c.telecommownAbo is True, "Check telecommown abo"
    assert c.promoCode == "TESTCODE", "Check promo code"

    test_connector.updateClientProperty(id, "mobile", "0610658238")
    test_connector.updateClientProperty(id, "email", "pierre2@afeu.fr")
    test_connector.updateCustomField("client", id, cf["refbazile"], "4321")
    test_connector.updateCustomField(
        "client", id, cf["facturationmanuelle"], "manuelle"
    )
    test_connector.updateCustomField("client", id, cf["facture-unique"], "N")
    test_connector.updateCustomField(
        "client", id, cf["statut-client-abo-mobile"], "Non actif"
    )
    test_connector.updateCustomField("client", id, cf["parrainage-code"], "AAAA")
    test_connector.updateCustomField("client", id, cf["parrainage-lien"], "MMMM")
    test_connector.updateCustomField("client", id, cf["parrainage-code-nb-use"], 4)
    test_connector.updateCustomField("client", id, cf["parrainage-nb-discount"], 2)
    test_connector.updateCustomField(
        "client", id, cf["parrainage-code-parrain"], "DDDD"
    )
    test_connector.updateCustomField("client", id, cf["parrainage-nb-code-donated"], 2)
    # test_connector.updateCustomField('client', id, cf['offre-telecommown'], timestamp)
    # test_connector.updateCustomField('client', id, cf['telecommown-date-debut'], timestamp)
    # test_connector.updateCustomField('client', id, cf['telecommown-date-fin'], timestamp)
    test_connector.updateCustomField("client", id, cf["telecommown-origine"], "Commown")
    test_connector.updateCustomField("client", id, cf["abo-telecommown"], "N")
    test_connector.updateCustomField("client", id, cf["code-promo"], "TESTCODE2")

    c = sellsy.SellsyClient(id)
    c.load(test_connector)
    assert c.msisdn == "+33610658238", "Check mobile"
    assert c.email == "pierre2@afeu.fr", "Check email"
    assert c.lines[0]["operatorRef"] == "4321", "Check bazile num"
    assert c.autoValidation is False, "Check autovalidation"
    assert c.oneInvoicePerLine is True, "Check facture unique"
    assert c.status == "Non actif", "Check status"
    assert c.sponsorCode == "AAAA", "Check sponsor code"
    assert c.sponsorLink == "MMMM", "Check sponsor link"
    assert c.sponsorNbUse == 4, "Check sponsor nb code"
    assert c.sponsorNbDiscount == 2, "Check sponsor nb discount"
    assert c.refereeCode == "DDDD", "Check referee code"
    assert c.sponsorNbCodeDonated == 2, "Check sponsor nb code donated"
    # assert c.optinTeleCommown == now, "Check optin telecommown"
    # assert c.telecommownStart == now, "Check telecommown start"
    # assert c.telecommownEnd == now, "Check telecommown end"
    assert c.telecommownAbo is False, "Check telecommown abo"
    assert c.promoCode == "TESTCODE2", "Check promo code"


def test_get_client_opportunities(test_connector):
    c = sellsy.SellsyClient(clientIdPG)
    opps = c.getOpportunities(test_connector)
    assert opps[0].id == str(opportunityIdPG)

    c = sellsy.SellsyClient(clientIdNoOpportunity)
    opps = c.getOpportunities(test_connector)
    assert len(opps) == 0


def test_get_opportunity_client(test_connector):
    o = sellsy.SellsyOpportunity(opportunityIdPG)
    o.load(test_connector)
    c = o.getClient(test_connector)
    assert c.id == str(clientIdPG), "First access, check client id"
    # Shouldn't use the connector, so passing an empty object shouldn't be a problem
    c = o.getClient(object())
    assert c.id == str(clientIdPG), "Second access, check client id"
