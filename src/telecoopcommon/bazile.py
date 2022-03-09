import requests
from requests.auth import HTTPBasicAuth
from json import JSONDecodeError

class BazileError(Exception):
  pass

class Connector:
  def __init__(self, conf, logger):
    self.host = conf['host']
    self.login = conf['login']
    self.password = conf['password']
    self.logger = logger

    self.token = None

  def getToken(self):
    if (self.token is None):
      data = {
        'login': self.login,
        'password': self.password
      }
      response = requests.post(self.host+'/ext/authentication', json=data)
      jsonResp = response.json()
      self.token = jsonResp['data']['token']

    self.logger.debug('Token is {}'.format(self.token))
    return self.token

  def get(self, service):
    headers = { 'Authorization': 'Bearer ' + self.getToken() }
    url = self.host+service
    self.logger.debug("Calling GET {} with headers {}".format(url, headers))
    response = requests.get(url, headers=headers)
    try:
      if (response.status_code != 200):
        raise BazileError(f"Got code {response.status_code} \n{response.text}")
      result = response.json()
      if ('data' not in result):
        raise BazileError(f"Unknown response from Bazile {result}")
    except BazileError as e:
      self.logger.warning(e)
      raise e
    except JSONDecodeError:
      self.logger.warning(f"Got a non json response {response.text}")
      raise BazileError("Non JSON response")
    return result

  def post(self, service, data):
    headers = { 'Authorization': 'Bearer {}'.format(self.getToken()) }
    url = self.host+service
    self.logger.info("Calling POST {}".format(url))
    response = requests.post(url, json=data, headers=headers)
    return response.json()

  def getMarques(self):
    return self.get('/ext/marques')

  def getPlans(self):
    return self.get('/ext/plans')

  def postOrder(self, params):
    #print(params)
    return self.post('/ext/order', params)

  def getSimInfo(self, nsce):
    url = f"/ext/sim/{nsce.replace(' ', '')}"
    return self.get(url)

  def isSimActive(self, nsce):
    isActive = None
    try:
      response = self.getSimInfo(nsce)
      isActive = (response['data']['Sim_information']['Statut'] == 'Active')
    except BazileError as e:
      isActive = False

    return isActive

  def getNumFromSim(self, nsce):
    num = None
    try:
      response = self.getSimInfo(nsce)
      num = response['data']['Sim_information']['Numero']
    except BazileError as e:
      isActive = False

    return num

  def getConso(self, accountId, month):
    return self.get(f"/ext/consommation/{accountId}/{month}")

  def getSimPortaHistory(self, nsce):
    url = f"/ext/sim/portability/history/{nsce}"
    return self.get(url)

  def postChangePlan(self, accountId, plan, startDate):
    data = {
      "Fidelisation": {
        "Account_id" : accountId,
        "Marque_id" : "14",
        "Plan_identifiant": plan,
        "Date_mise_en_place": startDate,
        "Paiement_id": "9"
      }
    }
    url = f"/ext/fidelisation"
    return self.post(url, data)
