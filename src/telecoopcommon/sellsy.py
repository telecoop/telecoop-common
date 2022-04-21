import sellsy_api, time, pytz, os
from json import JSONDecodeError
from datetime import datetime
from decimal import Decimal

from requests_oauth2client import OAuth2Client, ApiClient
from requests_oauth2client.auth import OAuth2ClientCredentialsAuth

sellsyValues = {
  'DEV': {
    'owner_id': 170714,
    'staff': {
      'support-client': 170761,
      'support-client-2': 170761,
      'support-societaire': 170714,
      'finance': 170714,
      'technique': 170761
    },
    'plans': {
      'Sobriété': 'PL_807',
      'Transition': 'PL_827'
    },
    'new_client_mail_template_id': 62573,
    'custom_fields': {
      'refbazile': 103778,
      'numerotelecoop': 103448,
      'nsce': 103775,
      'rio': 103447,
      'forfait': 154395,
      'achatsimphysique': 125472,
      'facturationmanuelle': 109341,
      'facture-unique': 117454,
      'date-activation-sim-souhaitee': 134623,
      'statut-client-abo-mobile': 141160,
      'offre-telecommown': 139323,
      'telecommown-origine': 139327,
      'telecommown-date-debut': 139329,
      'telecommown-date-fin': 139332,
      'abo-telecommown': 139325,
      'parrainage-code': 139333,
      'parrainage-lien': 139334,
      'parrainage-code-nb-use': 139352,
      'parrainage-nb-discount': 139353,
      'parrainage-code-parrain': 140671,
      'parrainage-nb-code-donated': 146337,
      'code-promo': 143564,
      'pack-depannage': 145684,
      'slimpay-mandate-status': 154395,
    },
    'funnel_id_vie_du_contrat': 62579,
    'step_new': 447893,
    'step_sim_to_send': 447894,
    'step_sim_to_send_transition': 573010,
    'step_sim_sent': 447895,
    'step_sim_received': 447896,
    'step_sim_pending_porta': 447897,
    'step_sim_pending_new': 447898,
    'step_sim_activated': 447899,
    'step_sim_suspended': 447900,
    'step_sim_terminated': 447901,
  },
  'PROD': {
    'owner_id': 170799,
    'staff': {
      'support-client': 170799,
      'support-client-2': 206337,
      'support-societaire': 183494,
      'finance': 174036,
      'technique': 168911
    },
    'plans': {
      'Sobriété': 'PL_750',
      'Transition': 'PL_796'
    },
    'new_client_mail_template_id': 62591,
    'custom_fields': {
      'refbazile': 103227,
      'numerotelecoop': 103670,
      'nsce': 102689,
      'rio': 102688,
      'forfait': 103346,
      'achatsimphysique': 125604,
      'date-activation-sim-souhaitee': 134621,
      'facturationmanuelle': 109534,
      'facture-unique': 119383,
      'statut-client-abo-mobile': 132773,
      'offre-telecommown': 139951,
      'telecommown-origine': 139954,
      'telecommown-date-debut': 139955,
      'telecommown-date-fin': 139956,
      'abo-telecommown': 139952,
      'parrainage-code': 139957,
      'parrainage-lien': 139958,
      'parrainage-code-nb-use': 139959,
      'parrainage-nb-discount': 139961,
      'parrainage-code-parrain': 140672,
      'parrainage-nb-code-donated': 146338,
      'code-promo': 144015,
      'pack-depannage': 145683,
      'slimpay-mandate-status': None,
    },
    'funnel_id_vie_du_contrat': 60663,
    'step_new': 446190,
    'step_sim_to_send': 434062,
    'step_sim_to_send_transition': 566314,
    'step_sim_sent': 444468,
    'step_sim_received': 434063,
    'step_sim_pending_porta': 444469,
    'step_sim_pending_new': 444470,
    'step_sim_activated': 442523,
    'step_sim_suspended': 446191,
    'step_sim_terminated': 446192,
  }
}

class TcSellsyError(Exception):
  pass

class TcSellsyConnector:
  def __init__(self, conf, logger):
    env = os.getenv('ENV', 'LOCAL')
    self.env = 'PROD' if env == 'PROD' else 'DEV'
    self.conf = conf
    self.logger = logger
    self._client = sellsy_api.Client(
      conf['consumer_token'],
      conf['consumer_secret'],
      conf['user_token'],
      conf['user_secret'])
    self._connector = None
    self.ownerId = sellsyValues[self.env]['owner_id']
    self.staff = sellsyValues[self.env]['staff']
    self.plans = sellsyValues[self.env]['plans']
    self.sellsyNewClientMailTemplateId = sellsyValues[self.env]['new_client_mail_template_id']
    customFields = sellsyValues[self.env]['custom_fields']
    self.customFieldBazileNb = customFields['refbazile']
    self.customFieldTelecomNum = customFields['numerotelecoop']
    self.cfidManuelInvoice = customFields['facturationmanuelle']
    self.cfidMergeInvoices = customFields['facture-unique']
    self.cfIdStatusClientMobile = customFields['statut-client-abo-mobile']
    self.cfIdTeleCommownOffre = customFields['offre-telecommown']
    self.cfIdTeleCommownOrigine = customFields['telecommown-origine']
    self.cfIdTeleCommownDateDebut = customFields['telecommown-date-debut']
    self.cfIdTeleCommownDateFin = customFields['telecommown-date-fin']
    self.cfIdTeleCommownBoth = customFields['abo-telecommown']
    self.cfidSponsorCode = customFields['parrainage-code']
    self.cfidSponsorLink = customFields['parrainage-lien']
    self.cfidSponsorNbUse = customFields['parrainage-code-nb-use']
    self.cfidSponsorNbDiscount = customFields['parrainage-nb-discount']
    self.cfidSponsorRefereeCode = customFields['parrainage-code-parrain']
    self.cfidSponsorNbCodeDonated = customFields['parrainage-nb-code-donated']
    self.cfidPromoCode = customFields['code-promo']
    self.cfidPackDepannage = customFields['pack-depannage']
    self.cfidSlimpayMandateStatus = customFields['slimpay-mandate-status']

    self.funnelIdVdc = sellsyValues[self.env]['funnel_id_vie_du_contrat']
    self.stepNew = sellsyValues[self.env]['step_new']
    self.stepSimToSend = sellsyValues[self.env]['step_sim_to_send']
    self.stepSimToSendTransition = sellsyValues[self.env]['step_sim_to_send_transition']
    self.stepSimSent = sellsyValues[self.env]['step_sim_sent']
    self.stepSimReceived = sellsyValues[self.env]['step_sim_received']
    self.stepSimPendingPorta = sellsyValues[self.env]['step_sim_pending_porta']
    self.stepSimPendingNew = sellsyValues[self.env]['step_sim_pending_new']
    self.stepSimActivated = sellsyValues[self.env]['step_sim_activated']
    self.stepSimSuspended = sellsyValues[self.env]['step_sim_suspended']
    self.stepSimTerminated = sellsyValues[self.env]['step_sim_terminated']


  def getConnector(self):
    if self._connector is None:
      self._oauth2client = OAuth2Client(
        token_endpoint="https://login.sellsy.com/oauth2/access-tokens",
        auth=(self.conf['v2_client_id'], self.conf['v2_client_secret']),
      )
      self._connector = ApiClient(
        self.conf['v2_host'],
        auth=OAuth2ClientCredentialsAuth(self._oauth2client),
        raise_for_status=False
      )
    return self._connector

  def getToken(self):
    return self._oauth2client.client_credentials()

  def api2Get(self, endpoint):
    connector = self.getConnector()
    self.logger.debug(f"Calling Sellsy API v2 GET {endpoint}")
    return connector.get(endpoint)

  def api2Post(self, endpoint, data):
    connector = self.getConnector()
    self.logger.debug(f"Calling Sellsy API v2 POST {endpoint} with {data}")
    return connector.post(endpoint, json=data)

  def api(self, method, params={}):
    try:
      self.logger.debug(f"Calling Sellsy {method} with params {params}")
      retry = 3
      result = None
      while retry >= 0:
        if retry < 3:
          self.logger.info(f"Retrying for the {3-retry}th time")
        try:
          result = self._client.api(method, params)
          retry = -1
        except JSONDecodeError as e:
          if (retry < 1):
            self.logger.warning(e)
            raise e
          retry -= 1
          time.sleep(1)
        except sellsy_api.errors.SellsyError as e:
          if (e.sellsy_code_error == 'E_OBJ_NOT_LOADABLE'):
            if (retry < 1):
              self.logger.warning(e)
              raise e
            retry -= 1
            time.sleep(1)
          else:
            raise e
    except sellsy_api.errors.SellsyAuthenticateError as e: # raised if credential keys are not valid
      self.logger.warning('Authentication failed ! Details : {}'.format(e))
      raise e
    except sellsy_api.errors.SellsyError as e: # raised if an error is returned by Sellsy API
      self.logger.warning(e)
      raise e
    # Sellsy API is throttled at 5 requests per second, we take a margin of 0.25s
    time.sleep(0.25)
    return result

  def updateClientProperty(self, clientId, property, value):
    client = self.getClient(clientId)
    params = {
      'clientid': clientId,
      'third': {
        'name': client.label,
      }
    }
    response = None
    if property in ['mobile', 'email']:
      if client.type == 'person':
        params = {
          'clientid': clientId,
          'third': {
            'name': client.name,
            property: value
          },
          'contact': {
            'name': client.name,
            'forename': client.firstname,
            property: value
          }
        }
        response = self.api(method="Client.update", params=params)
      else:
        params = {
          'clientid': clientId,
          'contactid': client.mainContactId,
          'contact': {
            'name': client.name,
            property: value
          }
        }
        response = self.api(method="Client.updateContact", params=params)

    return response

  def updateCustomField(self, entity, entityId, cfid, value):
    knownEntities = ['client', 'opportunity']
    if (entity not in knownEntities):
      raise ValueError(f"Unknown entity {entity}, should be in {knownEntities}")
    params = {
      'linkedtype': entity,
      'linkedid': entityId,
      'values': [
        { 'cfid': cfid, 'value': str(value) if value == 0 else value },
      ]
    }
    return self.api(method='CustomFields.recordValues', params=params)

  def getClientRef(self, clientId):
    response = sellsyConnector.api(method="Client.getOne", params={ 'clientid': clientId })
    return response['ident']

  def getTeleCommownOptinDate(self, clientId=None, opportunityId=None):
    if clientId is None and opportunityId is None:
      raise ValueError("Either clientId or opportunityId should be not None")
    response = None
    if clientId is not None:
      response = self.api(method="Client.getOne", params={ 'clientid': clientId })
    if opportunityId is not None:
      response = self.api(method="opportunities.getOne", params={ 'id': opportunityId })
    optinDate = None
    for l in response['customFields']:
      if (l['name'] == 'Z-Offre TeleCommown'):
        fields = l['list'] if isinstance(l['list'], list) else l['list'].values()
        for f in fields:
          if (f['code'] == 'offre-telecommown' and 'formatted_ymd' in f and f['formatted_ymd'] != ""):
            optinDate = pytz.timezone('Europe/Paris').localize(datetime.strptime(f['formatted_ymd'], '%Y-%m-%d'))
            break
        break
    return optinDate

  def getClient(self, id):
    c = SellsyClient(id)
    c.loadWithValues(self.getClientValues(id))
    return c

  def getClientValues(self, id):
    parisTZ = pytz.timezone('Europe/Paris')
    cli = self.api(method="Client.getOne", params={'clientid': id})

    mainContactId = cli['client']['maincontactid']

    result = {
      'ident': cli['client']['ident'],
      'type': cli['client']['type'],
      'people_name': '',
      'people_forename': '',
      'email': '',
      'mobile': '',
      'maincontactid':  mainContactId,
      'contacts': { },
    }
    customFields = {
      'refbazile': { 'code': 'refbazile', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'facturationmanuelle': { 'code': 'facturationmanuelle', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'facture-unique': { 'code': 'facture-unique', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'statut-client-abo-mobile': { 'code': 'statut-client-abo-mobile', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'parrainage-code': { 'code': 'parrainage-code', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'parrainage-lien': { 'code': 'parrainage-lien', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'parrainage-code-nb-use': { 'code': 'parrainage-code-nb-use', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'parrainage-nb-discount': { 'code': 'parrainage-nb-discount', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'parrainage-code-parrain': { 'code': 'parrainage-code-parrain', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'parrainage-nb-code-donated': { 'code': 'parrainage-nb-code-donated', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'offre-telecommown': { 'code': 'offre-telecommown', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'telecommown-date-debut': { 'code': 'telecommown-date-debut', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'telecommown-date-fin': { 'code': 'telecommown-date-fin', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'telecommown-origine': { 'code': 'telecommown-origine', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'abo-telecommown': { 'code': 'abo-telecommown', 'boolval': False },
      'code-promo': { 'code': 'code-promo', 'textval': '' }
    }
    # Name + person data
    if (cli['client']['type'] == 'person'):
      contact = cli['contact'] if 'contact' in cli else cli['contacts'][mainContactId]
      civility = 'M' if contact['civil'] == 'man' else 'Mme'
      result['name'] = f"{civility} {contact['name']} {contact['forename']}"
      result['email'] = contact['email']
      result['mobile'] = contact['mobile']
      result['people_name'] = contact['name']
      result['people_forename'] = contact['forename']
    elif (cli['client']['type'] == 'corporation'):
      corporation = cli['corporation']
      result['name'] = corporation['name']
      result['email'] = corporation['email']
      result['mobile'] = corporation['mobile']
    # Contacts
    if ('contacts' in cli and mainContactId in cli['contacts']):
      result['contacts'][mainContactId] = cli['contacts'][mainContactId]
    elif ('contact' in cli):
      result['contacts'][mainContactId] = cli['contact']
    # Custom fields
    for l in cli['customFields']:
      fields = l['list'].values() if isinstance(l['list'], dict) else l['list']
      for f in fields:
        if ('code' in f):
          code = f['code']
          if (code in ["refbazile", 'parrainage-code', 'parrainage-lien', 'parrainage-code-parrain', 'code-promo', 'slimpay-mandate-status']):
            customFields[code]['textval'] = f["defaultValue"]
          elif (code in ["facturationmanuelle", 'statut-client-abo-mobile', 'telecommown-origine'] and 'formatted_value' in f):
            customFields[code]['formatted_value'] = f["formatted_value"]
          elif (code in ["facture-unique", 'abo-telecommown']):
            customFields[code]['boolval'] = (f["defaultValue"] == 'Y')
          elif (code in ['parrainage-nb-discount', 'parrainage-code-nb-use', 'parrainage-nb-code-donated']):
            customFields[code]['numericval'] = int(f['defaultValue'])
          elif (code in ['offre-telecommown', 'telecommown-date-debut', 'telecommown-date-fin'] and 'formatted_ymd' in f):
            customFields[code]['formatted_ymd'] = f['formatted_ymd']
    result['customfields'] = customFields.values()

    return result

  def getClientFromRef(self, ref):
    params = {
      'search': {
        'ident': ref
      }
    }
    clients = self.api(method='Client.getList', params=params)
    client = None
    for id, cli in clients['result'].items():
      if (cli['ident'] == 'CLI00001001'):
        # Référence ayant servie de test lors de la mise en prod du parcours souscription
        continue

      client = SellsyClient(id)
      client.loadWithValues(cli)
      break

    return client

  def getClients(self):
    result = {}
    params = {
      'pagination': {
        'nbperpage': 1000,
        'pagenum': 1
      }
    }
    clients = self.api(method='Client.getList', params=params)
    infos = clients["infos"]
    nbPages = infos["nbpages"]
    currentPage = 1
    data = {}
    while (currentPage <= nbPages):
      self.logger.info("Processing page {}/{}".format(currentPage, nbPages))
      for id, client in clients['result'].items():
        if (client['ident'] == 'CLI00001001'):
          # Référence ayant servie de test lors de la mise en prod du parcours souscription
          continue

        if (client['ident'] is not None and client['ident'] not in ['', '-1']):
          c = SellsyClient(id)
          c.loadWithValues(client)
          result[id] = c
        else:
          self.logger.warning(f"Client #{id} has no reference")

      currentPage += 1
      if (infos["pagenum"] <= nbPages):
        params['pagination']['pagenum'] = currentPage
        clients = self.api(method="Client.getList", params=params)
        infos = clients["infos"]

    return result

  def getOpportunity(self, id):
    o = SellsyOpportunity(id)
    o.loadWithValues(self.getOpportunityValues)
    return o

  def getOpportunityValues(self, id):
    parisTZ = pytz.timezone('Europe/Paris')
    opp = self.api(method="Opportunities.getOne", params={'id': id})
    result = {
      'relationType': opp['relationType'],
      'linkedid': opp['linkedid'],
      'funnelid': opp['funnelid'],
      'created': opp['created'],
      'statusLabel': opp['statusLabel'],
      'stepEnterDate': opp['stepEnterDate'],
      'stepid': opp['stepid'],
      'customfields': {
        'nsce': { 'code': 'nsce', 'textval': '' },
        'numerotelecoop': { 'code': 'numerotelecoop', 'textval': '' },
        'rio': { 'code': 'rio', 'textval': '' },
        'refbazile': { 'code': 'refbazile', 'textval': ''},
        'forfait': { 'code': 'forfait', 'textval': '' },
        'achatsimphysique': { 'code': 'achatsimphysique', 'boolval': False },
        'date-activation-sim-souhaitee': { 'code': 'date-activation-sim-souhaitee', 'timestampval': 0 },
        'offre-telecommown': { 'code': 'offre-telecommown', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
        'parrainage-code-parrain': { 'code': 'parrainage-code-parrain', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
        'telecommown-date-debut': { 'code': 'telecommown-date-debut', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
        'telecommown-date-fin': { 'code': 'telecommown-date-fin', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
        'telecommown-origine': { 'code': 'telecommown-origine', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
        'abo-telecommown': { 'code': 'abo-telecommown', 'boolval': False},
        'code-promo': { 'code': 'code-promo', 'textval': '' },
        'pack-depannage': { 'code': 'pack-depannage', 'numericval': 0 }
      }
    }

    for l in opp['customFields']:
      fields = l['list'].values() if isinstance(l['list'], dict) else l['list']
      for field in fields:
        if ('code' in field):
          code = field['code']
          if (code in ['rio', 'nsce', 'numerotelecoop', 'refbazile', 'code-promo', 'parrainage-code-parrain']):
            result['customfields'][code]['textval'] = field['defaultValue']
          if (code in ['telecommown-origine', 'forfait'] and 'formatted_value' in field):
            result['customfields'][code]['formatted_value'] = field["formatted_value"]
          if (code in ['achatsimphysique', 'abo-telecommown']):
            result['customfields'][code]['boolval'] = (field["defaultValue"] == "Y")
          if (code in ['date-activation-sim-souhaitee', 'offre-telecommown', 'telecommown-date-debut', 'telecommown-date-fin'] and 'formatted_ymd' in field):
            result['customfields'][code]['formatted_ymd'] = field['formatted_ymd']
          if (code in ['pack-depannage']):
            result['customfields'][code]['numericval'] = int(field['defaultValue'])

    return result

  def getOpportunitiesInStep(self, funnelId, stepId, limit=None, startDate=None, searchParams=None):
    result = []
    params = {
      'pagination': {
        'nbperpage': 1000,
        'pagenum': 1
      },
      'search': {
        'funnelid': funnelId
      }
    }
    if stepId != 'all':
      params['search']['stepid'] = stepId
    if startDate is not None:
      params['search']['periodecreated_start'] = startDate.timestamp()
    if searchParams is not None:
      for k, v in searchParams.items():
        params['search'][k] = v

    opportunities = self.api(method='Opportunities.getList', params=params)
    infos = opportunities["infos"]
    nbPages = infos["nbpages"]
    currentPage = 1
    while (currentPage <= nbPages):
      self.logger.info("Processing page {}/{}".format(currentPage, nbPages))
      for id, opp in opportunities['result'].items():
        o = SellsyOpportunity(id)
        o.loadWithValues(opp)
        result.append(o)
        if limit is not None and limit <= len(result):
          return result

      currentPage += 1
      if (infos["pagenum"] <= nbPages):
        params['pagination']['pagenum'] = currentPage
        opportunities = self.api(method="Opportunities.getList", params=params)
        infos = opportunities["infos"]

    return result

  def getClientOpportunities(self, clientId):
    result = []
    params = { 'search': { 'thirds': [clientId,] }, 'pagination': { 'nbperpage': 200 } }
    opportunities = self.api(method="Opportunities.getList", params=params)
    if len(opportunities['result']) == 0:
      return result
    for opp in opportunities['result'].values():
      o = SellsyOpportunity(opp['id'])
      o.loadWithValues(opp)
      result.append(o)
    return result

  def getOpportunityFromClientAndMsisdn(self, clientId, msisdn):
    opportunities = self.getClientOpportunities(clientId)
    for opp in opportunities:
      if opp.msisdn == msisdn:
        return opp
    else:
      raise LookupError(f"Could not opportunity with msisdn {msisdn} for client #{clientId}")

  def getServices(self):
    params = {
      'type': 'service',
      'pagination': {
        'nbperpage': 100,
      }
    }
    services = self.api(method='Catalogue.getList', params=params)
    data = {}
    for id, service in services['result'].items():
      if ('name' in service):
        data[service['name']] = {
          'id': service['id'],
          'unitAmount': service['unitAmountTaxesInc'],
          'taxId': service['taxid'],
          'notes': service['notes'],
          'tradename': service['tradename']
        }

    return data

  def getInvoiceValues(self, id):
    parisTZ = pytz.timezone('Europe/Paris')
    invoice = self.api(method="Document.getOne", params={'doctype': 'invoice', 'docid': id})
    result = {
      'ident': invoice['ident'],
      'status': invoice['status'],
      'step_id': invoice['step'],
      'totalAmountTaxesFree': invoice['totalAmountTaxesFree'],
      'taxesAmountSum': invoice['taxesAmountSum'],
      'totalAmount': invoice['totalAmount'],
      'dueAmount': invoice['dueAmount'],
      'payDateCustom': datetime.strptime(invoice['paydate_custom'], "%d/%m/%Y").strftime("%Y-%m-%d"),
      'thirdident': invoice['thirdident'],
      'subject': invoice['subject'],
      'created': invoice['created'],
    }
    return result


class SellsyClient:
  def __init__(self, id):
    self.id = id
    self.reference = None
    self.type = None
    self.label = None
    self.name = None
    self.firstname = None
    self.email = None
    self.mainContactId = None
    self.oneInvoicePerLine = None
    self.autoValidation = None
    self.status = None
    self.optinTeleCommown = None
    self.telecommownStart = None
    self.telecommownEnd = None
    self.telecommownAbo = None
    self.sponsorCode = None
    self.sponsorLink = None
    self.sponsorNbUse = None
    self.sponsorNbDiscount = None
    self.sponsorNbCodeDonated = None
    self.refereeCode = None
    self.promoCode = None
    self.slimpayMandateStatus = None

  def __str__(self):
    return f"#{self.id} {self.reference} {self.label} {self.email} {self.status}"

  def load(self, connector):
    self.loadWithValues(connector.getClientValues(self.id))

  def loadWithValues(self, cli):
    parisTZ = pytz.timezone('Europe/Paris')
    email = cli['email']
    name = cli['people_name']
    firstname = cli['people_forename']
    # recherche du contact principal
    mainContactId = cli['maincontactid']
    for contactId, contact in cli["contacts"].items():
      if (contactId == mainContactId):
        email = contact['email']
        name = contact['name']
        firstname = contact['forename']

    self.reference = cli['ident']
    self.type = cli['type']
    self.label = cli['name']
    self.name =  name
    self.firstname = firstname
    self.email = email
    self.msisdn = cli['mobile']
    self.mainContactId = mainContactId
    self.lines = [{
      'msisdn': cli['mobile'].replace('+33', '0')
    }]
    for f in cli["customfields"]:
      code = f["code"]
      if (code == "refbazile"):
        self.lines[0]['bazileNum'] = f["textval"]
      elif (code == "facturationmanuelle"):
        self.autoValidation = (f["formatted_value"] in ['', 'automatique'])
      elif (code == "facture-unique"):
        if (isinstance(f["boolval"], bool)):
          self.oneInvoicePerLine = (not f["boolval"])
        else:
          self.oneInvoicePerLine = (f['boolval'] == 'N')
      elif (code == 'statut-client-abo-mobile' and 'formatted_value' in f):
        self.status = f["formatted_value"]

      elif (code == 'parrainage-code'):
        self.sponsorCode = f['textval']
      elif (code == 'parrainage-lien'):
        self.sponsorLink = f['textval']
      elif (code == 'parrainage-code-nb-use'):
        self.sponsorNbUse = f['numericval']
      elif (code == 'parrainage-nb-discount'):
        self.sponsorNbDiscount = f['numericval']
      elif (code == 'parrainage-code-parrain'):
        self.refereeCode = f['textval']
      elif (code == 'parrainage-nb-code-donated'):
        self.sponsorNbCodeDonated = f['numericval']

      elif (code == 'offre-telecommown' and 'formatted_ymd' in f and f['formatted_ymd'] != ''):
        self.optinTeleCommown = parisTZ.localize(datetime.strptime(f['formatted_ymd'], '%Y-%m-%d'))
      elif (code == 'telecommown-date-debut' and 'formatted_ymd' in f and f['formatted_ymd'] != ''):
        self.telecommownStart = parisTZ.localize(datetime.strptime(f['formatted_ymd'], '%Y-%m-%d'))
      elif (code == 'telecommown-date-fin' and 'formatted_ymd' in f and f['formatted_ymd'] != ''):
        self.telecommownEnd = parisTZ.localize(datetime.strptime(f['formatted_ymd'], '%Y-%m-%d'))
      elif (code == 'telecommown-origine'):
        self.telecommownOrigin = f['formatted_value']
      elif (code == 'abo-telecommown'):
        if (isinstance(f["boolval"], bool)):
          self.telecommownAbo = f['boolval']
        else:
          self.telecommownAbo = (f['boolval'] == 'Y')

      elif (code == 'code-promo'):
        self.promoCode = f['textval']

      elif code == 'slimpay-mandate-status':
        self.slimpayMandateStatus = f['textval']

  def getOpportunities(self, connector):
    opps = connector.getClientOpportunities(self.id)
    for opp in opps:
      opp.client = self
    return opps

class SellsyOpportunity:
  def __init__(self, id):
    env = os.getenv('ENV', 'LOCAL')
    self.env = 'PROD' if env == 'PROD' else 'DEV'

    self.id = id
    self.clientId = None
    self.client = None
    self.prospectId = None
    self.funnelId = None
    self.creationDate = None
    self.stepIpd = None
    self.steps = None
    self.status = None
    self.nsce = None
    self.msisdn = None
    self.bazileNum = None
    self.rio = None
    self.plan = None
    self.planItem = None
    self.achatSimPhysique = None
    self.dateActivationSimAsked = None
    self.optinTeleCommown = None
    self.telecommownStart = None
    self.telecommownEnd = None
    self.telecommownAbo = None
    self.promoCode = None
    self.refereeCode = None
    self.packDepannage = None

    self.plans = sellsyValues[self.env]['plans']

  def __str__(self):
    return f"#{self.id} {self.creationDate} {self.msisdn} client #{self.clientId}"

  def load(self, connector):
    values = connector.getOpportunityValues(self.id)
    self.loadWithValues(values)

  def getClient(self, connector):
    if self.client is None and self.clientId is not None:
      self.client = SellsyClient(self.clientId)
      self.client.load(connector)
    return self.client

  def loadWithValues(self, opp):
    parisTZ = pytz.timezone('Europe/Paris')
    if opp['relationType'] == 'client':
      self.clientId = opp['linkedid']
    else:
      self.prospectId = opp['linkedid']
    self.funnelId = opp['funnelid']
    self.creationDate = opp['created']
    self.status = opp['statusLabel']
    self.stepId = int(opp['stepid'])
    self.steps = { opp['stepid']: parisTZ.localize(datetime.fromisoformat(opp['stepEnterDate'])) }

    for fieldId, field in opp['customfields'].items():
      if ('code' in field):
        code = field['code']
        if (code == 'rio'):
          self.rio = field['textval']
        if (code == 'forfait'):
          self.plan = field['formatted_value']
        if (code == 'nsce'):
          self.nsce = field['textval']
        if (code == 'numerotelecoop'):
          self.msisdn = field['textval']
        if (code == 'refbazile'):
          self.bazileNum = field['textval']
        if (code == 'achatsimphysique'):
          if (isinstance(field["boolval"], bool)):
            self.achatSimPhysique = field["boolval"]
          else:
            self.achatSimPhysique = (field['boolval'] == 'Y')
        if (code == 'date-activation-sim-souhaitee' and 'formatted_ymd' in field and field['formatted_ymd'] != ''):
          self.dateActivationSimAsked = parisTZ.localize(datetime.strptime(field['formatted_ymd'], '%Y-%m-%d'))
        if (code == 'offre-telecommown' and 'formatted_ymd' in field and field['formatted_ymd'] != ''):
          self.optinTeleCommown = parisTZ.localize(datetime.strptime(field['formatted_ymd'], '%Y-%m-%d'))
        if (code == 'telecommown-date-debut' and 'formatted_ymd' in field and field['formatted_ymd'] != ''):
          self.telecommownStart = parisTZ.localize(datetime.strptime(field['formatted_ymd'], '%Y-%m-%d'))
        if (code == 'telecommown-date-fin' and 'formatted_ymd' in field and field['formatted_ymd'] != ''):
          self.telecommownEnd = parisTZ.localize(datetime.strptime(field['formatted_ymd'], '%Y-%m-%d'))
        if (code == 'telecommown-origine'):
          self.telecommownOrigin = field['formatted_value']
        if (code == 'abo-telecommown'):
          if (isinstance(field["boolval"], bool)):
            self.telecommownAbo = field['boolval']
          else:
            self.telecommownAbo = (field['boolval'] == 'Y')
        if (code == 'code-promo'):
          self.promoCode = field['textval']
        if (code == 'parrainage-code-parrain'):
          self.refereeCode = field['textval']
        if (code == 'pack-depannage'):
          self.packDepannage = field['numericval']

    if self.plan in self.plans:
      self.planItem = self.plans[self.plan]

  def updateStep(self, stepId, connector):
    connector.api(method="Opportunities.updateStep", params = { 'oid': self.id, 'stepid': stepId})

  def updateStatus(self, status, connector):
    connector.api(method='Opportunities.updateStatus', params = { 'id': self.id, 'status': status })

  def isPorta(self):
    return (self.rio is not None and self.rio != 'N/A')

  def isOldBazileLine(self):
    return (self.rio is not None and self.rio[0:2] == '56')

  def getPlanItem(self):
    return self.planItem

  def getSimStateFromStep(self, sellsyConnector):
    sc = sellsyConnector
    state = None
    if self.stepId in [sc.stepNew, sc.stepSimToSend]:
      state = 'new'
    elif self.stepId in [sc.stepSimSent, sc.stepSimReceived]:
      state = 'sent'
    elif self.stepId in [sc.stepSimPendingPorta, sc.stepSimPendingNew]:
      state = 'porta'
    elif self.stepId in [sc.stepSimActivated]:
      state = 'active'
    elif self.stepId in [sc.stepSimSuspended]:
      state = 'suspended'
    elif self.stepId in [sc.stepSimTerminated]:
      state = 'terminated'
    return state

class SellsyInvoice:
  def __init__(self, id):
    env = os.getenv('ENV', 'LOCAL')
    self.env = 'PROD' if env == 'PROD' else 'DEV'

    self.id = id
    self.reference = None
    self.sellsyStatus = None
    self.status = None
    self.amountHT = None
    self.tva = None
    self.amountTTC = None
    self.amountDue = None
    self.paymentDate = None
    self.clientRef = None
    self.subject = None
    self.creationDate = None

  def __str__(self):
    return f"Invoice #{self.id} - {self.reference} {self.sellsyStatus} : {round(self.amountTTC, 2)} € TTC ({round(self.amountHT, 2)} € HT) | {self.subject}"

  def load(self, sellsyConnector):
    values = sellsyConnector.getInvoiceValues(self.id)
    self.loadWithValues(values)

  def loadWithValues(self, values):
    parisTZ = pytz.timezone('Europe/Paris')
    self.reference = values['ident']
    self.sellsyStatus = values['status']
    self.status = values['step_id']
    self.amountHT = Decimal(values['totalAmountTaxesFree'])
    self.tva = Decimal(values['taxesAmountSum'])
    self.amountTTC = Decimal(values['totalAmount'])
    self.amountDue = Decimal(values['dueAmount'])
    self.paymentDate = parisTZ.localize(datetime.fromisoformat(values['payDateCustom']))
    self.clientRef = values['thirdident']
    self.subject = values['subject']

    self.creationDate = parisTZ.localize(datetime.fromisoformat(values['created']))

  @classmethod
  def getInvoices(cls, sellsyConnector, logger, startDate=None, search=None, limit=None, searchParams=None):
    result = []
    params = {
      'doctype': 'invoice',
      'pagination': {
        'nbperpage': 1000,
        'pagenum': 1
      },
      'search': {
      }
    }
    if startDate is not None:
      params['search']['periodecreationDate_start'] = startDate.timestamp()
    if searchParams is not None:
      for k, v in searchParams.items():
        params['search'][k] = v

    invoices = sellsyConnector.api(method='Document.getList', params=params)
    infos = invoices["infos"]
    nbPages = infos["nbpages"]
    currentPage = 1
    while (currentPage <= nbPages):
      logger.info("Processing page {}/{}".format(currentPage, nbPages))
      for id, invoice in invoices['result'].items():
        i = SellsyInvoice(id)
        i.loadWithValues(invoice)
        result.append(i)
        if limit is not None and limit <= len(result):
          return result

      currentPage += 1
      if (infos["pagenum"] <= nbPages):
        params['pagination']['pagenum'] = currentPage
        invoices = sellsyConnector.api(method="Document.getList", params=params)
        infos = invoices["infos"]

    return result
