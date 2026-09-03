import json
from datetime import datetime
from enum import Enum
from time import sleep

import requests


class DataStatus(Enum):
    OFF = "N"
    ON_2G = "Compteur_2G"
    ON_4G = "Compteur_4G"


class ForeignStatus(Enum):
    OFF = "N"
    INTERNATIONAL = "I"
    ROAMING = "IR"


class BazileError(Exception):
    statusCode = None
    pass


class BazileAuthError(Exception):
    statusCode = None
    pass


class BazileConnector:
    def __init__(self, conf: dict, logger):
        self.host = conf["host"]
        self.login = conf["login"]
        self.password = conf["password"]
        self.logger = logger
        self.token = None

    def getToken(self):
        if self.token is None:
            data = {"login": self.login, "password": self.password}
            url = self.host + "/ext/authentication"
            response = requests.post(url, json=data)
            if not response.ok:
                raise BazileAuthError("Could not connect to Bazile API.")
            try:
                jsonResp = response.json()
            except (
                requests.exceptions.JSONDecodeError or json.decoder.JSONDecodeError
            ) as excp:
                self.logger.warning(
                    f"POSTed {url} with {data} and got a non json respons {response.text}"
                )
                raise BazileAuthError(f"Non JSON response: {response.text}") from excp
            self.token = jsonResp["data"]["token"]

        self.logger.debug(f"Token starts with {self.token[:6]}")
        return self.token

    def get(self, service: str) -> dict:
        headers = {"Authorization": "Bearer " + self.getToken()}
        url = self.host + service
        self.logger.debug(f"Calling GET {url} with headers {headers}")
        retry = 3
        result = None
        while retry >= 0:
            try:
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    exc = BazileError(
                        f"Got code {response.status_code} \n{response.text}"
                    )
                    exc.statusCode = response.status_code
                    raise exc
                # We only want to retry when we got a 503 http code
                retry = -1
                result = response.json()
                if "data" not in result:
                    error = BazileError(f"Unknown response from Bazile {result}")
                    error.statusCode = 500
                    raise error
            except BazileError as excp:
                if response.status_code in [503, 502] and retry >= 1:
                    # When too many calls on Bazile API, we get a 503 error, waiting some time solves the problem
                    self.logger.info(f"Retrying {3 - retry + 1}/3")
                    retry -= 1
                    sleep(5)
                    continue
                self.logger.warning(excp)
                self.logger.warning(f"Service called was {service}")
                raise excp
            except requests.exceptions.JSONDecodeError as excp:
                self.logger.warning(
                    f"Calling {service}, got a non json response {response.text}"
                )
                error = BazileError("Non JSON response")
                error.statusCode = 500
                raise error from excp

        if result is None:
            raise BazileError("Unhandled error")

        return result

    def post(self, service: str, data: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.getToken()}"}
        url = self.host + service
        self.logger.debug(f"Calling POST {url} with params {data}")
        response = requests.post(url, json=data, headers=headers)
        try:
            result = response.json()
        except json.decoder.JSONDecodeError as excp:
            self.logger.warning(
                f"POSTed {url} with {data} and got a non json respons {response.text}"
            )
            raise BazileError("Non JSON response") from excp
        return result

    def patch(self, service: str, data: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.getToken()}"}
        url = self.host + service
        self.logger.debug(f"Calling PATCH {url} with params {data}")
        response = requests.patch(url, json=data, headers=headers)
        try:
            result = response.json()
        except json.decoder.JSONDecodeError as excp:
            self.logger.warning(
                f"PATCHed {url} with {data} and got a non json respons {response.text}"
            )
            raise BazileError("Non JSON response") from excp
        return result

    @classmethod
    def formatMsisdn(cls, msisdn: str) -> str:
        if msisdn[0:1] == "0":
            msisdn = "33" + msisdn[1:]
        return msisdn

    @classmethod
    def getBazilePlanItem(cls, planItem: str) -> str:
        result = planItem
        if planItem[:-1] == "kid":
            result = "PL_750"
        return result

    def getMarques(self) -> dict:
        return self.get("/ext/marques")

    def getPlans(self) -> dict:
        return self.get("/ext/plans")

    def postOrder(self, params: dict):
        return self.post("/ext/order", params)

    def getSimInfo(self, nsce: str) -> dict:
        url = f"/ext/sim/{nsce.replace(' ', '')}"
        return self.get(url)

    def isSimActive(self, nsce: str) -> bool:
        isActive = None
        try:
            response = self.getSimInfo(nsce)
            isActive = response["data"]["Sim_information"]["Statut"] == "Active"
        except BazileError:
            isActive = False

        return isActive

    def isSimAvailable(self, nsce: str) -> bool:
        isAvailable = None
        try:
            response = self.getSimInfo(nsce)
            isAvailable = response["data"]["Sim_information"]["Statut"] in [
                "Available",
                "Active",
            ]
        except BazileError:
            isAvailable = False

        return isAvailable

    def getNumFromSim(self, nsce: str) -> str | None:
        num = None
        try:
            response = self.getSimInfo(nsce)
            num = response["data"]["Sim_information"]["Numero"]
        except BazileError:
            num = None

        return num

    def palierHF(self, accountId: str, amount: float) -> dict:
        url = f"/ext/account/{accountId}"
        params = {"hfmax": amount}
        return self.patch(url, params)

    def authorizeHF(self, accountId: str, authorize=True) -> dict:
        url = f"/ext/account/{accountId}"
        params = {"hfautorise": "oui" if authorize else "non"}
        return self.patch(url, params)

    def getConso(self, accountId: str, month: str):
        return self.get(f"/ext/consommation/{accountId}/{month}")

    def simSwap(self, accountId: str, msisdn: str, newNsce: str) -> dict:
        url = "/ext/account/swap-sim"
        data = {
            "Accountid": accountId,
            "Msisdn": self.formatMsisdn(msisdn),
            "Nsce": newNsce,
        }
        return self.post(url, data)

    def changeSimOptions(
        self,
        msisdn: str,
        nsce: str,
        data: DataStatus | None = None,
        voicemail: bool | None = None,
        foreignStatus: ForeignStatus | None = None,
    ) -> dict:
        if data is None and voicemail is None and foreignStatus is None:
            self.logger.info("Nothing to do, exiting")
        url = "/ext/sim/options"
        params = {
            "Msisdn": self.formatMsisdn(msisdn),
            "Nsce": nsce,
        }
        if data is not None:
            params["Data"] = data.value
        if voicemail is not None:
            params["Voicemail"] = "Y" if voicemail else "N"
        if foreignStatus is not None:
            params["Foreignstatus"] = foreignStatus.value

        return self.post(url, params)

    def simSuspend(self, msisdn: str, nsce: str) -> dict:
        url = "/ext/sim/suspend"
        params = {
            "Msisdn": self.formatMsisdn(msisdn),
            "Nsce": nsce,
        }
        return self.post(url, params)

    def simActivate(self, msisdn: str, nsce: str) -> dict:
        url = "/ext/sim/reactivation"
        params = {
            "Msisdn": self.formatMsisdn(msisdn),
            "Nsce": nsce,
        }
        return self.post(url, params)

    def changePlan(self, accountId: str, plan: str, startDate: str) -> dict:
        data = {
            "Fidelisation": {
                "Account_id": accountId,
                "Marque_id": "14",
                "Plan_identifiant": plan,
                "Date_mise_en_place": startDate,
                "Paiement_id": "9",
            }
        }
        url = "/ext/fidelisation"
        return self.post(url, data)

    def getSimPortaHistory(self, nsce: str) -> dict:
        url = f"/ext/sim/portability/history/{nsce}"
        return self.get(url)

    def getSimplePortaHistory(self, nsce: str) -> dict | None:
        url = f"/ext/sim/portability/history/{nsce}"
        try:
            response = self.get(url)
        except BazileError as exp:
            if exp.statusCode == 404:
                self.logger.warning(f"SIM {nsce} not found")
                return
            raise exp
        history = {}
        if response["returnCode"] == 200:
            h = response["data"]["Historique"]
            h.sort(key=lambda e: e["date"])
            for event in h:
                if event["type"] == "IN" and event["statut"] == "PORTING DONE":
                    if "activated" not in history:
                        history["activated"] = datetime.fromisoformat(
                            event["date"].replace("Z", "+00:00")
                        )
                if (
                    event["type"] == "OUT" and event["statut"] == "PORTING DONE"
                ) or event["statut"].lower() == "terminaison":
                    if "terminated" not in history:
                        history["terminated"] = datetime.fromisoformat(
                            event["date"].replace("Z", "+00:00")
                        )
                else:
                    history[event["statut"]] = datetime.fromisoformat(
                        event["date"].replace("Z", "+00:00")
                    )

        return history

    def getActivationDate(self, nsce: str) -> str | None:
        history = self.getSimplePortaHistory(nsce)
        activationDate = None
        if history and "activated" in history:
            activationDate = history["activated"]

        return activationDate

    def getTerminationDate(self, nsce: str) -> str | None:
        history = self.getSimplePortaHistory(nsce)
        activationDate = None
        if history and "terminated" in history:
            activationDate = history["terminated"]

        return activationDate


class NormalizedBazileConnector(BazileConnector):
    def getSimInfo(self, nsce: str):
        url = f"/ext/sim/{nsce.replace(' ', '')}"
        response = self.get(url)
        if "data" not in response:
            raise BazileError(f"Unknown respons from Bazile {response}")
        simInfo = response["data"]["Sim_information"]

        def sanitize(value: str, lower=False):
            result = None
            if value:
                result = value.strip()
                if lower:
                    result = result.lower()
            return result

        status = sanitize(simInfo["Statut"], lower=True)
        msisdn = sanitize(simInfo["Numero"])
        if status is None and msisdn is None:
            status = "terminated"

        result = {
            "nsce": simInfo["Sim_serial"].strip(),
            "imsi": None,
            "typeSim": "SIM",
            "operator": "ORANGE",
            "puk1": sanitize(simInfo["Puck1"]),
            "pin1": sanitize(simInfo["Pin1"]),
            "puk2": sanitize(simInfo["Puck2"]),
            "pin2": sanitize(simInfo["Pin2"]),
            "status": status,
            "msisdn": msisdn,
            "operatorRef": sanitize(simInfo["Account_id"]),
            "international": sanitize(simInfo["Appels_internationaux"]),
            # Those too are ints so no need to sanitize
            "sva": bool(simInfo["Sva"] and int(simInfo["Sva"]) == 1),
            "wha": bool(simInfo["Wha"] and int(simInfo["Wha"]) == 1),
            "data": sanitize(simInfo["Data_statut"]),
            "voicemail": sanitize(simInfo["Messagerie_vocale"]),
            "rio": sanitize(simInfo["RIO"]),
            "oopAmount": sanitize(simInfo["Palier_HF"]),
            "oopDataAuth": sanitize(simInfo["HF Data autorisé"]) == "Oui",
            "activationDate": None,
            "terminationDate": None,
            "imei": simInfo["IMEI"],
        }

        history = self.getSimplePortaHistory(nsce)
        if history:
            if "activated" in history:
                result["activationDate"] = history["activated"]
            if "terminated" in history:
                result["terminationDate"] = history["terminated"]
        return result

    def getLineStatus(self, msisdn: str, nsce: str) -> str:
        response = self.getSimInfo(nsce)
        if response["msisdn"] and msisdn != response["msisdn"]:
            self.logger.warning(
                f"msisdn and nsce ({nsce}) mismatch ({msisdn} ≠ {response['msisdn']})"
            )
        return response["status"]
