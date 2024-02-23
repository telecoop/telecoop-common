from requests_oauth2client import OAuth2Client, ApiClient
from requests_oauth2client.auth import OAuth2ClientCredentialsAuth


class Connector:
    def __init__(self, config, logger):
        self.logger = logger
        self._config = config

        self.oauth2client = OAuth2Client(
            token_endpoint=f"{config['keycloak_token_url']}/realms/{config['keycloak_realm']}/protocol/openid-connect/token",
            auth=(config["keycloak_client_id"], config["keycloak_client_secret"]),
        )
        self.connector = ApiClient(
            config["host"],
            auth=OAuth2ClientCredentialsAuth(self.oauth2client),
            raise_for_status=False,
        )
        # self.token = oauth2client.client_credentials()

    def getToken(self):
        return self.oauth2client.client_credentials()

    def createCode(self, value=None, type="generic", amount="1"):
        data = {
            "code_type": type,
            "amount": amount,
        }
        if value is not None:
            data["value"] = value
        return self.connector.post(
            "/promo_codes/codes/", json=data, allow_redirects=True
        )

    def getCode(self, code):
        return self.connector.get(f"/promo_codes/codes/{code}", allow_redirects=True)

    def getCodes(self, codeType=None):
        url = "/promo_codes/codes"
        if codeType is not None:
            url += f"?code_type={codeType}"
        return self.connector.get(url, allow_redirects=True)

    def useCode(self, code, client):
        return self.connector.post(
            f"/promo_codes/code/{code}/used-by/{client}", allow_redirects=True
        )

    def getSponsorshipCode(self, referer):
        return self.connector.get(
            f"/promo_codes/sponsorships/{referer}", allow_redirects=True
        )

    def linkToReferee(self, referer, referee):
        return self.connector.post(
            f"/promo_codes/sponsorships/{referer}/linkedTo/{referee}",
            allow_redirects=True,
        )

    def appliedToReferee(self, referer, referee):
        return self.connector.post(
            f"/promo_codes/sponsorships/{referer}/applied/{referee}",
            allow_redirects=True,
        )
