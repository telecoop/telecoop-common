import json
from typing import Tuple

from requests_oauth2client import ApiClient, OAuth2Client
from requests_oauth2client.auth import OAuth2ClientCredentialsAuth

from .sellsyConnectorBase import TcSellsyConnectorBase
from .sellsyError import SellsyApiError

TOKEN_URL = "https://login.sellsy.com/oauth2/access-tokens"
SMART_TAGS_ID = {""}


class TcSellsyConnectorV2(TcSellsyConnectorBase):
    def __init__(self, conf: dict, logger, emailTemplates=None):
        self._client_id = conf["v2_client_id"]
        self._client_secret = conf["v2_client_secret"]
        self.url = "https://api.sellsy.com/v2/"
        super().__init__(conf, logger, emailTemplates)

    def _getConnector(self) -> None:
        if self._connector is None:
            self._oauth2client = OAuth2Client(
                token_endpoint=TOKEN_URL,
                auth=(self._client_id, self._client_secret),
            )
            self._connector = ApiClient(
                "https://api.sellsy.com/v2/",
                auth=OAuth2ClientCredentialsAuth(self._oauth2client),
                raise_for_status=False,
            )

    def _getToken(self):
        return self._oauth2client.client_credentials()

    def _get(self, endpoint: str) -> dict:
        self.logger.debug(f"Calling Sellsy API v2 GET {endpoint}")
        response = self._connector.get(endpoint)
        return response.json()

    def _post(self, endpoint: str, json: str | None = None, files: dict | None = None):
        headers = {"cache-control": "no-cache"}

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
        response = self._connector.post(
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

    def _delete(self, endpoint: str) -> None:
        url = f"{self.url}{endpoint}"
        self.logger.debug(f"Calling Sellsy API v2 DELETE {url}")
        self._connector.delete(endpoint)

    # === Opportunities

    def getOpportunity(self, opportunityId: str):
        """{
            "id": 11122521,
            "number": "OPP-00141",
            "name": "test pg",
            "probability": 0,
            "amount": {"currency": "EUR", "value": "0.00"},
            "source": {"id": 119864, "name": "Site web"},
            "due_date": "2026-04-04",
            "created": "2026-03-05T10:51:00+01:00",
            "updated_status": "2026-04-05T04:04:10+02:00",
            "status": "late",
            "pipeline": {"id": 62579, "name": "Vie du contrat"},
            "step": {"id": 694761, "name": "Relance en cours"},
            "note": "",
            "owner": {"id": 170761, "type": "staff"},
            "company_id": 57864003,
            "individual_id": None,
            "main_doc_id": None,
            "contact_ids": [57798736],
            "assigned_staff_ids": [170761],
            "related": [
                {"type": "company", "id": 57864003},
                {"type": "contact", "id": 57798736},
            ],
        }"""
        raise NotImplementedError

    # === Files

    def fileUpload(
        self,
        filePath: str,
        fileName: str,
        fileMimetype: str,
        resource: str,
        resourceId: str,
    ) -> Tuple[bool, dict]:
        # build file object
        files = {
            "file": (fileName, open(filePath, "rb"), fileMimetype, {"Expires": "0"}),
        }

        # upload file
        try:
            response = self._post(f"{resource}/{resourceId}/files", files=files)
        except SellsyApiError as e:
            self.logger.warning(e)
            return False, {}
        else:
            return True, response.json()

    def fileDelete(self, fileId: str) -> bool:
        # delete file
        try:
            self._delete(f"files/{fileId}")
        except SellsyApiError as e:
            self.logger.warning(e)
            return False
        else:
            return True

    def getClientIndividualFiles(self, clientId: str) -> list:
        results = self._get(f"individuals/{clientId}/files")
        return [i["id"] for i in results["data"]]

    def getClientProFiles(self, clientId: str) -> list:
        results = self._get(f"companies/{clientId}/files")
        return [i["id"] for i in results]

    # === SmartTags

    def linkSmartTagToObject(self, objectType: str, objectId: int, smartTagLabel: str):
        """Link a SmartTag to an object (ex: invoices, opportunities)
        We need to fetch the fetch the SmartTag already linked to an Opportunity, as a Post resets all existing opportunities
        """

        # fetch existing smartTags
        response = self._get(
            f"{objectType}/{objectId}/smart-tags",
        )
        if "data" not in response:
            raise SellsyApiError(
                f"Could not get smart-tags for {objectType} with id {objectId}. Response={response}"
            )
        smartTagList = response["data"]

        # add new smart tag to list
        if smartTagLabel not in [i["value"] for i in smartTagList]:
            smartTagList.append({"value": smartTagLabel})

            self._post(
                f"{objectType}/{objectId}/smart-tags",
                json=json.dumps(smartTagList),
            )

    # === Payments

    def createPayment(self, invoiceId, paymentDate, amount, label, doctype):
        raise NotImplementedError

    def deletePayment(self, paymentId, invoiceId, docType):
        raise NotImplementedError
