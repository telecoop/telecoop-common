import requests
from requests_oauth2client import OAuth2Client, ApiClient
from requests_oauth2client.auth import BearerAuth, OAuth2ClientCredentialsAuth
from datetime import datetime

class Connector:
  def __init__(self, config, logger):
    self.logger = logger
    self._config = config

    self.oauth2client = OAuth2Client(
      token_endpoint=f"{config['keycloak_token_url']}/realms/{config['keycloak_realm']}/protocol/openid-connect/token",
      auth=(config['keycloak_client_id'], config['keycloak_client_secret']),
    )
    self.connector = ApiClient(
      config['host'],
      auth=OAuth2ClientCredentialsAuth(self.oauth2client),
    )
    #self.token = oauth2client.client_credentials()

  def getToken(self):
    return self.oauth2client.client_credentials()

  def getCode(self, code):
    return self.connector.get(f"/promo_codes/codes/{code}")

  def getSponsorshipCode(self, referee):
    return self.connector.get(f"/promo_codes/sponsorships/{referee}")

  def linkToReferee(self, referee, client):
    return self.connector.post(f"/promo_codes/sponsorships/{referee}/linkedTo/{client}")

  def appliedToReferee(self, referee, client):
    return self.connector.post(f"/promo_codes/sponsorships/{referee}/applied/{client}")
