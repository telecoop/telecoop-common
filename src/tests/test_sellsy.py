import configparser, pytest, pytz
from datetime import datetime
from telecoopcommon import sellsy

confFile = '/etc/telecoop-common/conf.cfg'
config = configparser.ConfigParser()
config.read(confFile)

parisTZ = pytz.timezone('Europe/Paris')

clientIdPG = 34246953
opportunityIdPG = 5107122
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
  return sellsy.TcSellsyConnector(config['SellsyDev'], Logger())

def test_get_opportunity(test_connector):
  id = opportunityIdPG
  cf = sellsy.sellsyValues['DEV']['custom_fields']
  d = datetime.now()
  now = parisTZ.localize(datetime(year=d.year, month=d.month, day=d.day))
  timestamp = now.timestamp()
  test_connector.updateCustomField('opportunity', id, cf['nsce'], '1234')
  test_connector.updateCustomField('opportunity', id, cf['numerotelecoop'], '0610658239')
  test_connector.updateCustomField('opportunity', id, cf['rio'], '1111')
  test_connector.updateCustomField('opportunity', id, cf['forfait'], 'Sobriété')
  test_connector.updateCustomField('opportunity', id, cf['refbazile'], '2222')
  test_connector.updateCustomField('opportunity', id, cf['achatsimphysique'], True)
  test_connector.updateCustomField('opportunity', id, cf['date-activation-sim-souhaitee'], timestamp)
  test_connector.updateCustomField('opportunity', id, cf['offre-telecommown'], timestamp)
  test_connector.updateCustomField('opportunity', id, cf['telecommown-date-debut'], timestamp)
  test_connector.updateCustomField('opportunity', id, cf['telecommown-date-fin'], timestamp)
  test_connector.updateCustomField('opportunity', id, cf['telecommown-origine'], 'TeleCoop')
  test_connector.updateCustomField('opportunity', id, cf['abo-telecommown'], 'Y')

  o = sellsy.SellsyOpportunity(id)
  o.load(test_connector)
  assert o.clientId == str(clientIdPG), "Check client id"
  assert o.nsce == '1234', "Check nsce"
  assert o.msisdn == '0610658239', "Check msisdn"
  assert o.rio == '1111', "Check RIO"
  assert o.plan == 'Sobriété', "Check forfait"
  assert o.bazileNum == '2222', "Check Bazile number"
  assert o.achatSimPhysique == True, "Check achat sim physique"
  assert o.dateActivationSimAsked == now, "Check date activation SIM souhaitée"
  assert o.optinTeleCommown == now, "Check optin telecommown"
  assert o.telecommownStart == now, "Check telecommown start"
  assert o.telecommownEnd == now, "Check telecommown end"
  assert o.telecommownOrigin == 'TeleCoop', "Check telecommown origine"
  assert o.telecommownAbo == True, "Check telecommown abo"

  test_connector.updateCustomField('opportunity', id, cf['nsce'], '4321')
  test_connector.updateCustomField('opportunity', id, cf['numerotelecoop'], '0610658238')
  test_connector.updateCustomField('opportunity', id, cf['rio'], '2222')
  test_connector.updateCustomField('opportunity', id, cf['forfait'], 'Sobriété +')
  test_connector.updateCustomField('opportunity', id, cf['refbazile'], '1111')
  test_connector.updateCustomField('opportunity', id, cf['achatsimphysique'], 'N')
  #test_connector.updateCustomField('opportunity', id, cf['date-activation-sim-souhaitee'], None)

  o = sellsy.SellsyOpportunity(id)
  o.load(test_connector)
  assert o.nsce == '4321', "Check nsce"
  assert o.msisdn == '0610658238', "Check msisdn"
  assert o.rio == '2222', "Check RIO"
  assert o.plan == 'Sobriété +', "Check forfait"
  assert o.bazileNum == '1111', "Check Bazile number"
  assert o.achatSimPhysique == False, "Check achat sim physique"
  #assert o.dateActivationSimAsked is None, "Check date activation SIM souhaitée"

def test_get_client(test_connector):
  id = clientIdPG
  cf = sellsy.sellsyValues['DEV']['custom_fields']
  d = datetime.now()
  now = parisTZ.localize(datetime(year=d.year, month=d.month, day=d.day))
  timestamp = now.timestamp()
  test_connector.updateClientProperty(id, 'mobile', '0610658239')
  test_connector.updateClientProperty(id, 'email', 'pierre@afeu.fr')
  test_connector.updateCustomField('client', id, cf['refbazile'], '1234')
  test_connector.updateCustomField('client', id, cf['facturationmanuelle'], 'automatique')
  test_connector.updateCustomField('client', id, cf['facture-unique'], 'Y')
  test_connector.updateCustomField('client', id, cf['statut-client-abo-mobile'], 'Actif')
  test_connector.updateCustomField('client', id, cf['parrainage-code'], 'BBBB')
  test_connector.updateCustomField('client', id, cf['parrainage-lien'], 'LLLL')
  test_connector.updateCustomField('client', id, cf['parrainage-code-nb-use'], 2)
  test_connector.updateCustomField('client', id, cf['parrainage-nb-discount'], 1)
  test_connector.updateCustomField('client', id, cf['parrainage-code-parrain'], 'CCCC')
  test_connector.updateCustomField('client', id, cf['offre-telecommown'], timestamp)
  test_connector.updateCustomField('client', id, cf['telecommown-date-debut'], timestamp)
  test_connector.updateCustomField('client', id, cf['telecommown-date-fin'], timestamp)
  test_connector.updateCustomField('client', id, cf['telecommown-origine'], 'TeleCoop')
  test_connector.updateCustomField('client', id, cf['abo-telecommown'], 'Y')

  c = sellsy.SellsyClient(id)
  c.load(test_connector)
  assert c.msisdn == '+33610658239', "Check mobile"
  assert c.email == 'pierre@afeu.fr', "Check email"
  assert c.lines[0]['bazileNum'] == '1234', "Check bazile num"
  assert c.autoValidation == True, "Check autovalidation"
  assert c.oneInvoicePerLine == False, "Check facture unique"
  assert c.status == 'Actif', "Check status"
  assert c.sponsorCode == 'BBBB', "Check sponsor code"
  assert c.sponsorLink == 'LLLL', "Check sponsor link"
  assert c.sponsorCodeNb == 2, "Check sponsor nb code"
  assert c.sponsorNbDiscount == 1, "Check sponsor nb discount"
  assert c.refereeCode == 'CCCC', "Check referee code"
  assert c.optinTeleCommown == now, "Check optin telecommown"
  assert c.telecommownStart == now, "Check telecommown start"
  assert c.telecommownEnd == now, "Check telecommown end"
  assert c.telecommownOrigin == 'TeleCoop', "Check telecommown origine"
  assert c.telecommownAbo == True, "Check telecommown abo"

  test_connector.updateClientProperty(id, 'mobile', '0610658238')
  test_connector.updateClientProperty(id, 'email', 'pierre2@afeu.fr')
  test_connector.updateCustomField('client', id, cf['refbazile'], '4321')
  test_connector.updateCustomField('client', id, cf['facturationmanuelle'], 'manuelle')
  test_connector.updateCustomField('client', id, cf['facture-unique'], 'N')
  test_connector.updateCustomField('client', id, cf['statut-client-abo-mobile'], 'Non actif')
  test_connector.updateCustomField('client', id, cf['parrainage-code'], 'AAAA')
  test_connector.updateCustomField('client', id, cf['parrainage-lien'], 'MMMM')
  test_connector.updateCustomField('client', id, cf['parrainage-code-nb-use'], 4)
  test_connector.updateCustomField('client', id, cf['parrainage-nb-discount'], 2)
  test_connector.updateCustomField('client', id, cf['parrainage-code-parrain'], 'DDDD')
  #test_connector.updateCustomField('client', id, cf['offre-telecommown'], timestamp)
  #test_connector.updateCustomField('client', id, cf['telecommown-date-debut'], timestamp)
  #test_connector.updateCustomField('client', id, cf['telecommown-date-fin'], timestamp)
  test_connector.updateCustomField('client', id, cf['telecommown-origine'], 'Commown')
  test_connector.updateCustomField('client', id, cf['abo-telecommown'], 'N')

  c = sellsy.SellsyClient(id)
  c.load(test_connector)
  assert c.msisdn == '+33610658238', "Check mobile"
  assert c.email == 'pierre2@afeu.fr', "Check email"
  assert c.lines[0]['bazileNum'] == '4321', "Check bazile num"
  assert c.autoValidation == False, "Check autovalidation"
  assert c.oneInvoicePerLine == True, "Check facture unique"
  assert c.status == 'Non actif', "Check status"
  assert c.sponsorCode == 'AAAA', "Check sponsor code"
  assert c.sponsorLink == 'MMMM', "Check sponsor link"
  assert c.sponsorCodeNb == 4, "Check sponsor nb code"
  assert c.sponsorNbDiscount == 2, "Check sponsor nb discount"
  assert c.refereeCode == 'DDDD', "Check referee code"
  #assert c.optinTeleCommown == now, "Check optin telecommown"
  #assert c.telecommownStart == now, "Check telecommown start"
  #assert c.telecommownEnd == now, "Check telecommown end"
  assert c.telecommownAbo == False, "Check telecommown abo"

def test_get_client_opportunities(test_connector):
  c = sellsy.SellsyClient(clientIdPG)
  opps = c.getOpportunities(test_connector)
  assert opps[0].id == str(opportunityIdPG)

  c = sellsy.SellsyClient(clientIdNoOpportunity)
  opps = c.getOpportunities(test_connector)
  assert len(opps) == 0


#if (command == 'get-client'):
#  id = self.getArg('Client id')
#  client = self.getSellsyConnector().getClient(id)
#  print(client)
#
#if (command == 'get-client-from-ref'):
#  ref = self.getArg('Client ref')
#  client = self.getSellsyConnector().getClientFromRef(ref)
#  print(client)
#
#if (command == 'get-clients'):
#  clients = self.getSellsyConnector().getClients()
#  print(len(clients))
#  print(next(iter(clients.values())))
#
#if (command == 'get-opportunities-in-step'):
#  step = self.getArg("Step")
#  connector = self.getSellsyConnector()
#  stepId = connector.conf[step]
#  opps = connector.getOpportunitiesInStep(connector.funnelIdVdc, stepId)
#  print(len(opps))
#
#if (command == 'get-client-opportunities'):
#  clientId = self.getArg('Client id')
#  opps = self.getSellsyConnector().getClientOpportunities(clientId)
#  print(opps)
#
#if (command == 'update-client'):
#  id = self.getArg('Client id')
#  prop = self.getArg('Property')
#  value = self.getArg('Property value')
#  response = self.getSellsyConnector().updateClientProperty(id, prop, value)
#  print(response)
#
#if (command == 'update-cf'):
#  env = 'PROD' if self.env == 'PROD' else 'DEV'
#  clientId = self.getArg('Client id')
#  customField = self.getArg('Custom field')
#  cfid = sellsyValues[env]['custom_fields'][customField]
#  value = self.getArg('Value')
#  response = self.getSellsyConnector().updateCustomField('client', clientId, cfid, "Actif")
#  print(response)
#
