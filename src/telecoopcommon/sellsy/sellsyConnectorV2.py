from requests_oauth2client import ApiClient, OAuth2Client
from requests_oauth2client.auth import OAuth2ClientCredentialsAuth

from .sellsyError import SellsyApiError

DEFAULT_URL = "https://apifeed.sellsy.com/0/"
TOKEN_URL = "https://login.sellsy.com/oauth2/access-tokens"


class TcSellsyConnectorV2:
    def __init__(self, conf, logger, emailTemplates=None):
        self.conf = conf
        self.logger = logger
        self._connector = None
        self._getConnector()

    def _getConnector(self):
        if self._connector is None:
            self._oauth2client = OAuth2Client(
                token_endpoint=TOKEN_URL,
                auth=(self.conf["v2_client_id"], self.conf["v2_client_secret"]),
            )
            self._connector = ApiClient(
                self.conf["v2_host"],
                auth=OAuth2ClientCredentialsAuth(self._oauth2client),
                raise_for_status=False,
            )
        return self._connector

    def _getToken(self):
        return self._oauth2client.client_credentials()

    def _get(self, endpoint):
        connector = self._getConnector()
        self.logger.debug(f"Calling Sellsy API v2 GET {endpoint}")
        return connector.get(endpoint)

    def _post(self, endpoint, json=None, files: dict | None = None):
        connector = self._getConnector()
        if files:
            self.logger.debug(
                f"Calling Sellsy API v2 POST {endpoint} with files={files}"
            )
        else:
            self.logger.debug(f"Calling Sellsy API v2 POST {endpoint} with json={json}")

        response = connector.post(endpoint, json=json, files=files)
        # the json parameter is ignored if either data or files is passed.
        # see https://requests.reafdthedocs.io/en/latest/user/quickstart/#post-a-multipart-encoded-file

        if response.status_code not in [200, 201]:
            exc = SellsyApiError(f"Got code {response.status_code} \n{response.text}")
            exc.statusCode = response.status_code
            exc.textError = response.text
            raise exc

        return response
