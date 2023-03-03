import json
from datetime import datetime
from time import sleep
from enum import Enum
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


class Connector:
    def __init__(self, conf, logger):
        self.host = conf["host"]
        self.login = conf["login"]
        self.password = conf["password"]
        self.logger = logger

        self.token = None

    def getToken(self):
        if self.token is None:
            data = {"login": self.login, "password": self.password}
            response = requests.post(self.host + "/ext/authentication", json=data)
            jsonResp = response.json()
            self.token = jsonResp["data"]["token"]

        self.logger.debug("Token is {}".format(self.token))
        return self.token

    def get(self, service):
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
                    raise BazileError(f"Unknown response from Bazile {result}")
            except BazileError as excp:
                if response.status_code in [503, 502] and retry >= 1:
                    # When too many calls on Bazile API, we get a 503 error, waiting some time solves the problem
                    self.logger.info(f"Retrying {3-retry+1}/3")
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
                raise BazileError("Non JSON response") from excp
        return result

    def post(self, service, data):
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

    def patch(self, service, data):
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

    def getMarques(self):
        return self.get("/ext/marques")

    def getPlans(self):
        return self.get("/ext/plans")

    def postOrder(self, params):
        # print(params)
        return self.post("/ext/order", params)

    def getSimInfo(self, nsce):
        url = f"/ext/sim/{nsce.replace(' ', '')}"
        return self.get(url)

    def isSimActive(self, nsce):
        isActive = None
        try:
            response = self.getSimInfo(nsce)
            isActive = response["data"]["Sim_information"]["Statut"] == "Active"
        except BazileError:
            isActive = False

        return isActive

    def getNumFromSim(self, nsce):
        num = None
        try:
            response = self.getSimInfo(nsce)
            num = response["data"]["Sim_information"]["Numero"]
        except BazileError:
            num = None

        return num

    def palierHF(self, accountId, amount):
        url = f"/ext/account/{accountId}"
        params = {"hfmax": amount}
        return self.patch(url, params)

    def getConso(self, accountId, month):
        return self.get(f"/ext/consommation/{accountId}/{month}")

    def simSwap(self, accountId, msisdn, newNsce):
        url = "/ext/account/swap-sim"
        data = {
            "Accountid": accountId,
            "Msisdn": msisdn,
            "Nsce": newNsce,
        }
        return self.post(url, data)

    def changeSimOptions(
        self,
        msisdn: str,
        nsce: str,
        data: DataStatus = None,
        voicemail: bool = None,
        foreignStatus: ForeignStatus = None,
    ):
        if data is None and voicemail is None and foreignStatus is None:
            self.logger.info("Nothing to do, exiting")
        url = "/ext/sim/options"
        params = {
            "Msisdn": msisdn,
            "Nsce": nsce,
        }
        if data is not None:
            params["Data"] = data.value
        if voicemail is not None:
            params["Voicemail"] = "Y" if voicemail else "N"
        if foreignStatus is not None:
            params["Foreignstatus"] = foreignStatus.value

        return self.post(url, params)

    def simSuspend(self, msisdn, nsce):
        url = "/ext/sim/suspend"
        params = {
            "Msisdn": msisdn,
            "Nsce": nsce,
        }
        return self.post(url, params)

    def simActivate(self, msisdn, nsce):
        url = "/ext/sim/reactivation"
        params = {
            "Msisdn": msisdn,
            "Nsce": nsce,
        }
        return self.post(url, params)

    def changePlan(self, accountId, plan, startDate):
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

    def getSimPortaHistory(self, nsce):
        url = f"/ext/sim/portability/history/{nsce}"
        return self.get(url)

    def getSimplePortaHistory(self, nsce):
        url = f"/ext/sim/portability/history/{nsce}"
        try:
            response = self.get(url)
        except BazileError as exp:
            if exp.statusCode == 404:
                self.logger.warning(f"SIM {nsce} not found")
                return
            else:
                raise exp
        history = {}
        if response["returnCode"] == 200:
            h = response["data"]["Historique"]
            h.sort(key=lambda e: e["date"])
            for event in h:
                if event["statut"] == "PORTING DONE":
                    if "activated" not in history:
                        history["activated"] = datetime.fromisoformat(
                            event["date"].replace("Z", "+00:00")
                        )
                else:
                    history[event["statut"]] = datetime.fromisoformat(
                        event["date"].replace("Z", "+00:00")
                    )

        return history
