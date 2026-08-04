import hashlib
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth


class TeleCommownConnector:
    """A connector for the TeleCommown API"""

    TIMEOUT = 10
    CAMPAIN_REF = "TeleCommown2021"

    def __init__(self, host: str, user: str, password: str, salt: str, logger):
        self.logger = logger
        self._host = host
        self._auth = HTTPBasicAuth(user, password)
        self._salt = salt

    # ==== private

    def _get(self, endpoint: str, params: dict) -> dict:
        url = f"{self._host}/{endpoint}"
        self.logger.debug(
            f"[TeleCommown] Sending GET with params={params} to URL={url}"
        )
        response = requests.get(
            url, params=params, auth=self._auth, timeout=self.TIMEOUT
        )
        response.raise_for_status()
        self.logger.debug(response.json)
        return response.json()

    def _post(self, endpoint: str, data: dict) -> dict:
        url = f"{self._host}/{endpoint}"
        self.logger.debug(f"[TeleCommown] Sending POST with data={data} to URL={url}")
        response = requests.post(url, json=data, auth=self._auth, timeout=self.TIMEOUT)
        response.raise_for_status()
        self.logger.debug(response.json)
        return response.json()

    # ==== public

    def optin(self, mobile: str, optinDate: datetime) -> dict:
        key = self.getKey(mobile)
        endpoint = f"campaigns/{self.CAMPAIN_REF}/opt-in"
        data = {"customer_key": key, "optin_ts": optinDate.isoformat()}
        response = self._post(endpoint, data)
        return response

    def optout(self, mobile: str, optoutDate: datetime) -> dict:
        key = self.getKey(mobile)
        endpoint = f"campaigns/{self.CAMPAIN_REF}/opt-out"
        data = {"customer_key": key, "optout_ts": optoutDate.isoformat()}
        response = self._post(endpoint, data)
        return response

    def getKey(self, mobile: str) -> str:
        """Return a hash given a mobile phone"""
        hash = hashlib.sha256()
        hash.update((mobile + self._salt).encode("utf-8"))
        return hash.hexdigest()

    def notifyNewClients(self, newClients: list) -> None:
        """Create opt-in for each new client"""
        for client in newClients:
            self.logger.info(
                f"Notifying telecommown {client.msisdn} has optin on {client.startDate}"
            )
            self.optin(client.msisdn, client.startDate)

    def getImportantEvents(self, startDate: datetime, endDate: datetime) -> dict:
        """Get opt-ins and opt-outs from API"""
        endpoint = f"campaigns/{self.CAMPAIN_REF}/subscriptions/important-events"
        params = {"since": startDate.isoformat(), "until": endDate.isoformat()}
        response = self._get(endpoint, params=params)
        return response
