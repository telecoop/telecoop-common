import requests
from datetime import datetime
from time import sleep
from json import JSONDecodeError

class BazileError(Exception):
  statusCode = None
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
    headers = {'Authorization': 'Bearer ' + self.getToken()}
    url = self.host+service
    self.logger.debug("Calling GET {} with headers {}".format(url, headers))
    retry = 3
    result = None
    while retry >= 0:
      try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
          exc = BazileError(f"Got code {response.status_code} \n{response.text}")
          exc.statusCode = response.status_code
          raise exc
        # We only want to retry when we got a 503 http code
        retry = -1
        result = response.json()
        if ('data' not in result):
          raise BazileError(f"Unknown response from Bazile {result}")
      except BazileError as e:
        if response.status_code in [503, 502] and retry >= 1:
          # When too many calls on Bazile API, we get a 503 error, waiting some time solves the problem
          self.logger.info(f"Retrying {3-retry+1}/3")
          retry -= 1
          sleep(5)
          continue
        self.logger.warning(e)
        self.logger.warning(f"Service called was {service}")
        raise e
      except JSONDecodeError:
        self.logger.warning(f"Calling {service}, got a non json response {response.text}")
        raise BazileError("Non JSON response")
    return result

  def post(self, service, data):
    headers = {'Authorization': 'Bearer {}'.format(self.getToken())}
    url = self.host+service
    self.logger.info("Calling POST {}".format(url))
    response = requests.post(url, json=data, headers=headers)
    return response.json()

  def getMarques(self):
    return self.get('/ext/marques')

  def getPlans(self):
    return self.get('/ext/plans')

  def postOrder(self, params):
    # print(params)
    return self.post('/ext/order', params)

  def getSimInfo(self, nsce):
    url = f"/ext/sim/{nsce.replace(' ', '')}"
    return self.get(url)

  def isSimActive(self, nsce):
    isActive = None
    try:
      response = self.getSimInfo(nsce)
      isActive = (response['data']['Sim_information']['Statut'] == 'Active')
    except BazileError:
      isActive = False

    return isActive

  def getNumFromSim(self, nsce):
    num = None
    try:
      response = self.getSimInfo(nsce)
      num = response['data']['Sim_information']['Numero']
    except BazileError:
      num = None

    return num

  def getConso(self, accountId, month):
    return self.get(f"/ext/consommation/{accountId}/{month}")

  def getSimPortaHistory(self, nsce):
    url = f"/ext/sim/portability/history/{nsce}"
    return self.get(url)

  def postChangePlan(self, accountId, plan, startDate):
    data = {
      "Fidelisation": {
        "Account_id": accountId,
        "Marque_id": "14",
        "Plan_identifiant": plan,
        "Date_mise_en_place": startDate,
        "Paiement_id": "9"
      }
    }
    url = "/ext/fidelisation"
    return self.post(url, data)

  def getSimplePortaHistory(self, nsce):
    url = f"/ext/sim/portability/history/{nsce}"
    response = self.get(url)
    history = {}
    if response['returnCode'] == 200:
      h = response['data']['Historique']
      h.sort(key=lambda e: e['date'])
      for event in h:
        if event['statut'] == 'PORTING DONE':
          if 'activated' not in history:
            history['activated'] = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
        else:
          history[event['statut']] = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))

    return history
