import json
from datetime import datetime, timedelta, timezone
from time import sleep

import pytz
import requests


class PhenixError(Exception):
    statusCode: int | None = None
    pass


class PhenixConnector:
    statusTranslate = {
        "disponible": "available",
        "active": "active",
        "réservée": "reserved",
        "suspendue": "suspended",
        "résiliée": "terminated",
        "delete": "deleted",
        "reserved": "reserved",
        "send": "send",
        "suspend": "suspend",
        "available": "available",
        "saved": "saved",
    }

    def __init__(self, conf: dict, logger):
        self.host = conf["host"]
        self.login = conf["login"]
        self.password = conf["password"]
        self.partnerId = conf["partnerId"]
        self.purchaseCostCode = conf["purchaseCostCode"]
        self.logger = logger

        self.token = None
        self.token_expiry_date = None

    def getToken(self) -> str:
        now = datetime.now(tz=timezone.utc)
        if self.token is None or (
            self.token_expiry_date is None or self.token_expiry_date < now
        ):
            data = {"username": self.login, "password": self.password}
            url = self.host + "/Auth/authenticate"
            response = requests.post(url, json=data, timeout=30)
            self.logger.debug(f"Response from phenix: {response.text}")
            try:
                jsonResp = response.json()
            except json.decoder.JSONDecodeError as excp:
                self.logger.warning(
                    f"POSTed {url} with {data} and got a non json respons {response.text}"
                )
                raise PhenixError("Non JSON response") from excp
            self.token = jsonResp["access_token"]
            self.token_expiry_date = now + timedelta(seconds=jsonResp["expires_in"])

        self.logger.debug(f"Token is {self.token[:10]}…")
        return self.token

    def get(self, service: str, data={}) -> dict:
        headers = {"Authorization": "Bearer " + self.getToken()}
        url = self.host + service
        params = data
        params["partenaireId"] = self.partnerId
        self.logger.debug(
            f"Calling GET {url} with headers 'Authorization': 'Bearer {self.getToken()[:10]}'"
        )
        retry = 3
        result = None
        while retry >= 0:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                if response.status_code != 200:
                    exc = PhenixError(
                        f"Got code {response.status_code} \n{response.text}"
                    )
                    exc.statusCode = response.status_code
                    raise exc
                # We only want to retry when we got a 503 http code
                retry = -1
                result = response.json()
                if (
                    "Conso" not in service
                    and "Produits" not in service
                    and "etat" not in result
                ):
                    raise PhenixError(f"Unknown response from Phenix {result}")
            except PhenixError as excp:
                if response.status_code in [503, 502] and retry >= 1:
                    # When too many calls on Bazile API, we get a 503 error, waiting some time solves the problem
                    self.logger.info(f"Retrying {3 - retry + 1}/3")
                    retry -= 1
                    sleep(5)
                    continue
                self.logger.warning(excp)
                self.logger.warning(f"Service called was {service} with {params}")
                raise excp
            except requests.exceptions.JSONDecodeError as excp:
                self.logger.warning(
                    f"Calling {service}, got a non json response {response.text}"
                )
                raise PhenixError("Non JSON response") from excp

        if result is None:
            raise PhenixError("Unhandled error")

        return result

    def post(self, service: str, data: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.getToken()}"}
        url = self.host + service
        data["partenaireId"] = self.partnerId
        self.logger.debug(f"Calling POST {url} with params {data}")
        response = requests.post(url, json=data, headers=headers, timeout=30)
        try:
            result = response.json()
        except json.decoder.JSONDecodeError as excp:
            self.logger.warning(
                f"POSTed {url} with {data} and got a non json respons {response.text}"
            )
            raise PhenixError("Non JSON response") from excp
        return result

    def patch(self, service: str, data: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.getToken()}"}
        url = self.host + service
        data["partenaireId"] = self.partnerId
        self.logger.debug(f"Calling PATCH {url} with params {data}")
        response = requests.patch(url, json=data, headers=headers, timeout=30)
        try:
            result = response.json()
        except json.decoder.JSONDecodeError as excp:
            self.logger.warning(
                f"PATCHed {url} with {data} and got a non json respons {response.text}"
            )
            raise PhenixError("Non JSON response") from excp
        return result

    @classmethod
    def textToDate(cls, dateTxt: str) -> datetime | None:
        return (
            pytz.timezone("Europe/Paris").localize(datetime.fromisoformat(dateTxt))
            if dateTxt is not None
            else None
        )

    def getSimInfo(self, nsce: str) -> dict | None:
        urlSim = "/GsmApi/V2/GetInfoSim"
        try:
            responseSim = self.get(urlSim, data={"simSN": nsce.replace(" ", "")})
        except PhenixError as exp:
            if exp.statusCode in [404, 400]:
                self.logger.warning(f"Nsce {nsce} not found")
                return None
            raise exp
        if "etat" not in responseSim:
            raise PhenixError(f"Unknown response from Phenix {responseSim}")
        result = {
            "nsce": responseSim["simSN"],
            "imsi": responseSim["imsi"],
            "typeSim": responseSim["typeSim"],
            "operator": responseSim["operateur"],
            "puk1": responseSim["puk1"],
            "pin1": responseSim["pin1"],
            "puk2": responseSim["puk2"],
            "pin2": responseSim["pin2"],
            "status": self.statusTranslate[responseSim["etat"].lower()],
            "msisdn": responseSim["msisdn"],
            "orderSimId": responseSim["commandeSimId"],
            "operatorRef": None,
            "rio": None,
            "international": None,
            "sva": None,
            "wha": None,
            "data": None,
            "voicemail": None,
            "oopAmount": None,
            "oopDataAuth": None,
            "imei": None,
            "activationDate": None,
            "terminationDate": None,
        }
        urlLine = "/GsmApi/V2/MsisdnConsult"
        if result["msisdn"]:
            try:
                responseLine = self.get(urlLine, data={"msisdn": result["msisdn"]})
            except PhenixError as exp:
                if exp.statusCode in [404, 400]:
                    self.logger.warning(f"Nsce {nsce} not found")
                    return None
                raise exp
            if "etat" not in responseLine:
                raise PhenixError(f"Unknown response from Phenix {responseLine}")
            result.update(
                {
                    "operatorRef": responseLine["numAbo"],
                    "rio": responseLine["rio"],
                    "international": False,
                    "sva": True,
                    "wha": True,
                    "data": "N",
                    "voicemail": False,
                    "oopAmount": None,
                    "oopDataAuth": None,
                    "activationDate": self.textToDate(responseLine["dateActivation"]),
                    "terminationDate": self.textToDate(responseLine["dateResiliation"]),
                }
            )
            for product in responseLine["produits"]:
                code = None
                if "code" in product:
                    code = product["code"]
                if "codeProduit" in product:
                    code = product["codeProduit"]
                if not code:
                    self.logger.warning(f"Unknown product format {product}")
                # Roaming option
                if code == "RM":
                    result["international"] = "IR"
                if code == "ISVA":
                    result["sva"] = False
                if code == "BWHA":
                    result["wha"] = False
                # Mode voice international without data.
                # Don't touch if it was already initialized (e.g. by RM)
                if code == "MVI" and not result["international"]:
                    result["international"] = "IV"
                if code == "WV":
                    result["voicemail"] = None
                # "Accès international" calls FR -> INT
                if code == "INT" and not result["international"]:
                    result["international"] = "I"
                if code == "SDC" or code == "DATA":
                    result["data"] = "4G"

        return result

    def getLineInfo(self, msisdn: str) -> dict | None:
        url = "/GsmApi/V2/MsisdnConsult"
        try:
            response = self.get(url, data={"msisdn": msisdn})
        except PhenixError as exp:
            if exp.statusCode in [404, 400]:
                self.logger.warning(f"Msisdn {msisdn} not found")
                return None
            raise exp
        return response

    def getConso(self, msisdn: str, month: datetime) -> dict | None:
        url = "/GsmApi/GetConsoMsisdnFromCDR"
        data = {"msisdn": msisdn, "moisAnnee": month.strftime("%m%Y")}
        try:
            response = self.get(url, data=data)
        except PhenixError as exp:
            if exp.statusCode in [404, 400]:
                self.logger.warning(f"Msisdn {msisdn} not found")
                return None
            raise exp
        return response

    def getActivationDate(self, nsce: str) -> datetime | None:
        msisdn = self.getNumFromSim(nsce)
        activationDate = None
        if msisdn:
            response = self.getLineInfo(msisdn)
            if response and "dateActivation" in response and response["dateActivation"]:
                activationDate = self.textToDate(response["dateActivation"])

        return activationDate

    def getTerminationDate(self, nsce: str) -> datetime | None:
        msisdn = self.getNumFromSim(nsce)
        terminationDate = None
        if msisdn:
            response = self.getLineInfo(msisdn)
            if (
                response
                and "dateResiliation" in response
                and response["dateResiliation"]
            ):
                terminationDate = self.textToDate(response["dateResiliation"])

        return terminationDate

    def getNumFromSim(self, nsce: str) -> str | None:
        num = None
        response = None
        try:
            response = self.getSimInfo(nsce)
        except PhenixError:
            num = None
        if response:
            num = response["msisdn"]

        return num

    def getLineStatus(self, msisdn: str, nsce: str) -> str | None:
        result = None
        response = self.getLineInfo(msisdn)
        if response:
            if response["simsn"] and nsce != response["simsn"]:
                self.logger.warning(
                    f"msisdn ({msisdn}) and nsce mismatch ({nsce} ≠ {response['simsn']})"
                )
            result = response["etat"].lower()
        return result

    def getOptions(self, provider: str) -> dict:
        url = "/GsmApi/V2/GetGsmProduitsByOperator"
        data = {"operateur": provider.upper()}
        return self.get(url, data=data)

    def requestActivation(self, params: dict) -> dict:
        url = "/GsmApi/V2/MsisdnActivate"
        data = params
        return self.post(url, data)

    def getProductsOrange(self) -> dict:
        url = "/GsmApi/V2/GetGsmProduitsByOperator"
        data = {"operateur": "ORANGE"}
        return self.get(url, data)
