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
    self.customFieldBazileNb = conf['custom_field_bazile_nb']
    self.customFieldTelecomNum = conf['custom_field_telecom_num']
    self.cfIdTeleCommownOffre = conf['cfid_telecommown_offre']
    self.cfIdTeleCommownOrigine = conf['cfid_telecommown_origine']
    self.cfIdTeleCommownDateDebut = conf['cfid_telecommown_date_debut']
    self.cfIdTeleCommownDateFin = conf['cfid_telecommown_date_fin']
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

  def getTeleCommownOptinDate(self, clientId):
    response = sellsyConnector.api(method="Client.getOne", params={ 'clientid': clientId })
    optinDate = None
    for l in response['customFields']:
      if (l['name'] == 'Z-Offre TeleCommown'):
        for f in l['list']:
          if (f['code'] == 'offre-telecommown' and 'formatted_ymd' in f and f['formatted_ymd'] != ""):
            optinDate = pytz.timezone('Europe/Paris').localize(datetime.datetime.strptime(f['formatted_ymd'], '%Y-%m-%d'))
            break
        break
    return optinDate

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

class SellsyOpportunity:
  def __init__(self, id):
    self.id = id

  def loadWithValues(self, opp):
    self.clientId = opp['linkedid']
    self.funnelId = opp['funnelid']
    self.creationDate = opp['created']
    self.steps = { opp['stepid']: opp['stepEnterDate'] }
    self.nsce = None
    self.msisdn = None
    self.rio = None
    self.plan = None
    self.achatSimPhysique = False
    self.dateActivationSimAsked = None

    for fieldId, field in opp['customfields'].items():
      if ('code' in field):
        if (field['code'] == 'rio'):
          self.rio = field['textval']
        if (field['code'] == 'forfait'):
          self.plan = field['textval']
        if (field['code'] == 'nsce'):
          self.nsce = field['textval']
        if (field['code'] == 'numerotelecoop'):
          self.msisdn = field['textval']
        if (field['code'] == 'refbazile'):
          self.bazileNum = field['textval']
        if (field['code'] == 'achatsimphysique'):
          self.achatSimPhysique = (field["boolval"] == "Y")
        if (field['code'] == 'date-activation-sim-souhaitee' and field['timestampval'] is not None and field['timestampval'] > 0):
          timestamp = field['timestampval']
          if (timestamp is not None):
            self.dateActivationSimAsked = pytz.timezone('Europe/Paris').localize(datetime.fromtimestamp(timestamp))

  def updateStep(self, stepId, connector):
    connector.api(method="Opportunities.updateStep", params = { 'oid': self.id, 'stepid': stepId})

  def updateStatus(self, status, connector):
    connector.api(method='Opportunities.updateStatus', params = { 'id': self.id, 'status': status })

  def isPorta(self):
    return (self.rio is not None and self.rio != 'N/A')

  def isOldBazileLine(self):
    return (self.rio is not None and self.rio[0:2] == '56')
