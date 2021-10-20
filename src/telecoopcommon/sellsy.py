import sellsy_api, time, pytz
from json import JSONDecodeError
from datetime import datetime

class TcSellsyConnector:
  def __init__(self, conf, logger):
    self.logger = logger
    self._client = sellsy_api.Client(
      conf['consumer_token'],
      conf['consumer_secret'],
      conf['user_token'],
      conf['user_secret'])
    self.ownerId = conf['owner_id']
    self.sellsyNewClientMailTemplateId = conf['new_client_mail_template_id']
    self.customFieldBazileNb = conf['custom_field_bazile_nb']
    self.customFieldTelecomNum = conf['custom_field_telecom_num']
    self.cfIdTeleCommownOffre = conf['cfid_telecommown_offre']
    self.cfIdTeleCommownOrigine = conf['cfid_telecommown_origine']
    self.cfIdTeleCommownDateDebut = conf['cfid_telecommown_date_debut']
    self.cfIdTeleCommownDateFin = conf['cfid_telecommown_date_fin']
    self.cfidSponsorCode = conf['cfid_sponsor_code']
    self.cfidSponsorLink = conf['cfid_sponsor_link']
    self.cfidSponsorNbUse = conf['cfid_sponsor_nb_use']
    self.cfidSponsorNbDiscount = conf['cfid_sponsor_nb_discount']
    self.cfidSponsorRefereeCode = conf['cfid_sponsor_referee_code']

    self.funnelIdVdc = conf['funnel_id_vie_du_contrat']
    self.stepNew = conf['step_new']
    self.stepSimToSend = conf['step_sim_to_send']
    self.stepSimSent = conf['step_sim_sent']
    self.stepSimReceived = conf['step_sim_received']
    self.stepSimPendingPorta = conf['step_sim_pending_porta']
    self.stepSimPendingNew = conf['step_sim_pending_new']
    self.stepSimActivated = conf['step_sim_activated']
    self.stepSimSuspended = conf['step_sim_suspended']
    self.stepSimTerminated = conf['step_sim_terminated']

  def api(self, method, params=None):
    try:
      self.logger.debug(f"Calling Sellsy {method} with params {params}")
      retry = 3
      result = None
      while retry > 0:
        try:
          result = self._client.api(method, params)
          retry = 0
        except JSONDecodeError as e:
          if (retry < 1):
            self.logger.warning(e)
            raise e
          retry -= 1
          time.sleep(1)
        except sellsy_api.errors.SellsyError as e:
          if (e.sellsy_code_error == 'E_OBJ_NOT_LOADABLE'):
            if (retry < 1):
              raise e
            retry -= 1
            time.sleep(1)
          else:
            raise e
    except sellsy_api.SellsyAuthenticateError as e: # raised if credential keys are not valid
      self.logger.warning('Authentication failed ! Details : {}'.format(e))
    except sellsy_api.SellsyError as e: # raised if an error is returned by Sellsy API
      self.logger.warning(e)
      raise e
    return result

  def updateClient(self, clientId, values):
    params = {
      'clientid': clientId,
      'third': values
    }
    return self.api(method="Client.update", params=params)

  def updateCustomField(self, entity, entityId, cfid, value):
    knownEntities = ['client', 'opportunity']
    if (entity not in knownEntities):
      raise ValueError(f"Unknown entity {entity}, should be in {knownEntities}")
    params = {
      'linkedtype': entity,
      'linkedid': entityId,
      'values': [
        { 'cfid': cfid, 'value': value },
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
      response = sellsyConnector.api(method="Client.getOne", params={ 'clientid': clientId })
    if opportunityId is not None:
      response = sellsyConnector.api(method="opportunities.getOne", params={ 'id': opportunityId })
    optinDate = None
    for l in response['customFields']:
      if (l['name'] == 'Z-Offre TeleCommown'):
        for f in l['list']:
          if (f['code'] == 'offre-telecommown' and 'formatted_ymd' in f and f['formatted_ymd'] != ""):
            optinDate = pytz.timezone('Europe/Paris').localize(datetime.datetime.strptime(f['formatted_ymd'], '%Y-%m-%d'))
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
      'parrainage-link': { 'code': 'parrainage-link', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'parrainage-code-nb-use': { 'code': 'parrainage-code-nb-use', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'parrainage-nb-discount': { 'code': 'parrainage-nb-discount', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'parrainage-code-parrain': { 'code': 'parrainage-code-parrain', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'offre-telecommown': { 'code': 'offre-telecommown', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'telecommown-date-debut': { 'code': 'telecommown-date-debut', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'telecommown-date-fin': { 'code': 'telecommown-date-fin', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
      'telecommown-origine': { 'code': 'telecommown-origine', 'textval': '', 'formatted_value': '', 'boolval': False, 'numericval': 0, 'timestampval': 0 },
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
          if (code in ["refbazile", 'parrainage-code', 'parrainage-link', 'parrainage-code-parrain']):
            customFields[code]['textval'] = f["defaultValue"]
          elif (code in ["facturationmanuelle", 'statut-client-abo-mobile', 'telecommown-origine'] and 'formatted_value' in f):
            customFields[code]['formatted_value'] = f["formatted_value"]
          elif (code == "facture-unique"):
            customFields[code]['boolval'] = (f["defaultValue"] == 'Y')
          elif (code in ['parrainage-nb-discount', 'parrainage-code-nb-use']):
            customFields[code]['numericval'] = int(f['defaultValue'])
          elif (code in ['offre-telecommown', 'telecommown-date-debut', 'telecommown-date-fin'] and 'formatted_ymd' in f):
            customFields[code]['timestampval'] = parisTZ.localize(datetime.strptime(f['formatted_ymd'], '%Y-%m-%d')).timestamp()
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
      logger.info("Processing page {}/{}".format(currentPage, nbPages))
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
        clients = sellsyClient.api(method="Client.getList", params=params)
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
      'linkedid': opp['linkedid'],
      'funnelid': opp['funnelid'],
      'created': opp['created'],
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
      }
    }

    for l in opp['customFields']:
      fields = l['list'].values() if isinstance(l['list'], dict) else l['list']
      for field in fields:
        if ('code' in field):
          code = field['code']
          if (code in ['rio', 'forfait', 'nsce', 'numerotelecoop', 'refbazile']):
            result['customfields'][code]['textval'] = field['defaultValue']
          if (code == 'achatsimphysique'):
            result['customfields'][code]['boolval'] = (field["defaultValue"] == "Y")
          if (code == 'date-activation-sim-souhaitee' and 'formatted_ymd' in field):
            result['customfields'][code]['timestampval'] = parisTZ.localize(datetime.strptime(field['formatted_ymd'], '%Y-%m-%d')).timestamp()

    return result

  def getOpportunitiesInStep(self, funnelId, stepId):
    result = []
    params = {
      'pagination': {
        'nbperpage': 1000,
        'pagenum': 1
      },
      'search': {
        'funnelid': funnelId,
        'stepid': stepId
      }
    }
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

      currentPage += 1
      if (infos["pagenum"] <= nbPages):
        params['pagination']['pagenum'] = currentPage
        opportunities = self.api(method="Opportunities.getList", params=params)
        infos = opportunities["infos"]

    return result

  def getClientOpportunities(self, clientId):
    result = []
    params = { 'search': { 'thirds': [clientId] } }
    opportunities = sellsyClient.api(method="Opportunities.getList", params=params)
    for opp in opportunities.values():
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

class SellsyClient:
  def __init__(self, id):
    self.id = id
    self.reference = None
    self.type = None
    self.label = None
    self.name = None
    self.firstname = None
    self.email = None
    self.oneInvoicePerLine = None
    self.autoValidation = None
    self.status = None

  def __str__(self):
    return f"#{self.id} {self.reference} {self.label} {self.email} {self.status}"

  def load(self, connector):
    self.loadWithValues(connector.getClientValues)

  def loadWithValues(self, cli):
    parisTZ = pytz.timezone('Europe/Paris')
    email = cli['email']
    # recherche du contact principal
    mainContactId = cli['maincontactid']
    for contactId, contact in cli["contacts"].items():
      if (contactId == mainContactId):
        email = contact['email']

    self.reference = cli['ident']
    self.type = cli['type']
    self.label = cli['name']
    self.name =  cli['people_name']
    self.firstname = cli['people_forename']
    self.email = email
    self.msisdn = cli['mobile']
    self.oneInvoicePerLine = False
    self.autoValidation = True
    self.status = None
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
        self.oneInvoicePerLine = (f["boolval"] == 'N')
      elif (code == 'statut-client-abo-mobile' and 'formatted_value' in f):
        self.status = f["formatted_value"]

      elif (code == 'parrainage-code'):
        self.sponsorCode = f['textval']
      elif (code == 'parrainage-link'):
        self.sponsorLink = f['textval']
      elif (code == 'parrainage-code-nb-use'):
        self.sponsorCodeNb = f['numericval']
      elif (code == 'parrainage-nb-discount'):
        self.sponsorNbDiscount = f['numericval']
      elif (code == 'parrainage-code-parrain'):
        self.refereeCode = f['textval']

      elif (code == 'offre-telecommown'):
        self.optinTeleCommown = parisTZ.localize(datetime.fromtimestamp(int(f['timestampval'])))
      elif (code == 'telecommown-date-debut'):
        self.telecommownStart = parisTZ.localize(datetime.fromtimestamp(int(f['timestampval'])))
      elif (code == 'telecommown-date-fin'):
        self.telecommownEnd = parisTZ.localize(datetime.fromtimestamp(int(f['timestampval'])))
      elif (code == 'telecommown-origine'):
        self.telecommownOrigin = f['formatted_value']

class SellsyOpportunity:
  def __init__(self, id):
    self.id = id
    self.clientId = None
    self.funnelId = None
    self.creationDate = None
    self.steps = None
    self.nsce = None
    self.msisdn = None
    self.rio = None
    self.plan = None
    self.achatSimPhysique = None
    self.dateActivationSimAsked = None

  def __str__(self):
    return f"#{self.id} {self.creationDate} {self.msisdn} client #{self.clientId}"

  def load(self, connector):
    values = connector.getOpportunityValues(self.id)
    self.loadWithValues(values)

  def loadWithValues(self, opp):
    parisTZ = pytz.timezone('Europe/Paris')
    print(opp)
    self.clientId = opp['linkedid']
    self.funnelId = opp['funnelid']
    self.creationDate = opp['created']
    self.steps = { opp['stepid']: parisTZ.localize(datetime.fromisoformat(opp['stepEnterDate'])) }

    for fieldId, field in opp['customfields'].items():
      if ('code' in field):
        code = field['code']
        if (code == 'rio'):
          self.rio = field['textval']
        if (code == 'forfait'):
          self.plan = field['textval']
        if (code == 'nsce'):
          self.nsce = field['textval']
        if (code == 'numerotelecoop'):
          self.msisdn = field['textval']
        if (code == 'refbazile'):
          self.bazileNum = field['textval']
        if (code == 'achatsimphysique'):
          self.achatSimPhysique = (field["boolval"] == "Y")
        if (code == 'date-activation-sim-souhaitee' and field['timestampval'] is not None and field['timestampval'] > 0):
          timestamp = field['timestampval']
          if (timestamp is not None):
            self.dateActivationSimAsked = parisTZ.localize(datetime.fromtimestamp(timestamp))

  def updateStep(self, stepId, connector):
    connector.api(method="Opportunities.updateStep", params = { 'oid': self.id, 'stepid': stepId})

  def updateStatus(self, status, connector):
    connector.api(method='Opportunities.updateStatus', params = { 'id': self.id, 'status': status })

  def isPorta(self):
    return (self.rio is not None and self.rio != 'N/A')

  def isOldBazileLine(self):
    return (self.rio is not None and self.rio[0:2] == '56')
