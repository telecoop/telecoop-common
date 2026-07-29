import json

from requests_oauth2client import ApiClient, OAuth2Client
from requests_oauth2client.auth import OAuth2ClientCredentialsAuth

from .sellsyError import SellsyApiError

TOKEN_URL = "https://login.sellsy.com/oauth2/access-tokens"
SMART_TAGS_ID = {""}


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

    def _get(self, endpoint) -> dict:
        connector = self._getConnector()
        self.logger.debug(f"Calling Sellsy API v2 GET {endpoint}")
        response = connector.get(endpoint, raise_for_status=True)
        return json.loads(response.content)

    def _post(self, endpoint, json: str | None = None, files: dict | None = None):
        headers = {"cache-control": "no-cache"}

        connector = self._getConnector()
        if files:
            self.logger.debug(
                f"Calling Sellsy API v2 POST {endpoint} with files={files}"
            )
        else:
            self.logger.debug(f"Calling Sellsy API v2 POST {endpoint} with json={json}")

        # we have to use data= and set the headers manually, as json= is transforming payload into binary (don't know why)
        if json:
            headers["content-type"] = "application/json"

        # the json parameter is ignored if either data or files is passed.
        # see https://requests.readthedocs.io/en/latest/user/quickstart/#post-a-multipart-encoded-file
        response = connector.post(
            endpoint,
            data=json,
            files=files,
            headers=headers,
        )

        if response.status_code not in [200, 201]:
            exc = SellsyApiError(f"Got code {response.status_code} \n{response.text}")
            exc.statusCode = response.status_code
            exc.textError = response.text
            raise exc

        return response

    # === SmartTags

    def linkSmartTagToObject(self, objectType: str, objectId: int, smartTagLabel: str):
        """Link a SmartTag to an object (ex: invoices, opportunities)
        We need to fetch the fetch the SmartTag already linked to an Opportunity, as a Post resets all existing opportunities
        """

        # fetch existing smartTags
        response = self._get(
            f"{objectType}/{objectId}/smart-tags",
        )
        smartTagList = response["data"]

        # add new smart tag to list
        if smartTagLabel not in [i["value"] for i in smartTagList]:
            smartTagList.append({"value": smartTagLabel})

            self._post(
                f"{objectType}/{objectId}/smart-tags",
                json=json.dumps(smartTagList),
            )
