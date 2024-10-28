import json
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta
from time import sleep
import requests
from .bazile import Connector as BazileConnector, BazileError


class GsmLine:
    msisdn: str
    nsce: str
    operator: str

    def __init__(self, msisdn, nsce, operator):
        self.msisdn = msisdn
        self.nsce = nsce
        self.operator = operator


class Connector:
    _connectors = {}
    defaultOperator: str = None

    def __init__(self, conf: dict, logger, cachetimeout=1):
        """cachetimeout controls the number of hours connectors will be kept in cache"""
        self.conf = conf
        self.logger = logger
        self.cachetimeout = cachetimeout

    def initConnector(self, operator):
        if operator.lower() == "bazile":
            self._connectors["bazile"] = {
                "connector": NormalizedBazileConnector(
                    self.conf["BazileAPI"], self.logger
                ),
                "lastCalled": None,
            }
        elif operator.lower() == "phenix":
            self._connectors["phenix"] = {
                "connector": PhenixConnector(self.conf["PhenixAPI"], self.logger),
                "lastCalled": None,
            }
        else:
            raise RuntimeError(f"Unknown operator {operator}")

    def setDefaultOperator(self, operator: str):
        self.defaultOperator = operator

    def callMethod(self, operator=None, **kwargs):
        if not self.calledMethod:
            raise RuntimeError("callMethod called with no method to call :-/")
        ope = operator or self.defaultOperator
        self.logger.debug(ope)
        if ope:
            # If no connector exists, or if connector was last called for more than self.cachetimeout hours
            if (
                ope not in self._connectors
                or self._connectors[ope]["lastCalled"]
                + relativedelta(hours=self.cachetimeout)
                < datetime.now()
            ):
                self.initConnector(ope)

            self._connectors[ope]["lastCalled"] = datetime.now()
            self.logger.debug(self._connectors)
            func = getattr(self._connectors[ope]["connector"], self.calledMethod)
        else:
            raise RuntimeError("No operator specified")
        return func(**kwargs)

    def __getattr__(self, name):
        self.calledMethod = name
        return self.callMethod


class PhenixError(Exception):
    statusCode = None
    pass


class PhenixConnector:
    def __init__(self, conf, logger):
        self.host = conf["host"]
        self.login = conf["login"]
        self.password = conf["password"]
        self.partnerId = conf["partnerId"]
        self.purchaseCostCode = conf["purchaseCostCode"]
        self.logger = logger

        self.token = None

    def getToken(self):
        if self.token is None:
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

        self.logger.debug(f"Token is {self.token[:10]}…")
        return self.token

    def get(self, service, data={}):
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
                    self.logger.info(f"Retrying {3-retry+1}/3")
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
        return result

    def post(self, service, data):
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

    def patch(self, service, data):
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
    def textToDate(cls, dateTxt):
        return (
            pytz.timezone("Europe/Paris").localize(datetime.fromisoformat(dateTxt))
            if dateTxt is not None
            else None
        )

    def getSimInfo(self, nsce):
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
            "status": responseSim["etat"].lower(),
            "msisdn": responseSim["msisdn"],
            "orderSimId": responseSim["commandeSimId"],
            "operatorRef": None,
            "rio": None,
            "international": None,
            "sva": None,
            "wha": None,
            "roaming": None,
            "voicemail": None,
            "oopAmount": None,
            "oopDataAuth": None,
            "imei": None,
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
                    "international": None,
                    "sva": None,
                    "wha": None,
                    "roaming": None,
                    "voicemail": None,
                    "oopAmount": None,
                    "oopDataAuth": None,
                    "activationDate": self.textToDate(responseLine["dateActivation"]),
                    "terminationDate": self.textToDate(responseLine["dateResiliation"]),
                }
            )
        return result

    def getLineInfo(self, msisdn):
        url = "/GsmApi/V2/MsisdnConsult"
        try:
            response = self.get(url, data={"msisdn": msisdn})
        except PhenixError as exp:
            if exp.statusCode in [404, 400]:
                self.logger.warning(f"Msisdn {msisdn} not found")
                return None
            raise exp
        return response

    def getConso(self, msisdn, month):
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

    def getActivationDate(self, nsce):
        msisdn = self.getNumFromSim(nsce)
        activationDate = None
        if msisdn:
            response = self.getLineInfo(msisdn)
            if "dateActivation" in response and response["dateActivation"]:
                activationDate = self.textToDate(response["dateActivation"])

        return activationDate

    def getTerminationDate(self, nsce):
        msisdn = self.getNumFromSim(nsce)
        terminationDate = None
        if msisdn:
            response = self.getLineInfo(msisdn)
            if "dateResiliation" in response and response["dateResiliation"]:
                terminationDate = self.textToDate(response["dateResiliation"])

        return terminationDate

    def getNumFromSim(self, nsce):
        num = None
        response = None
        try:
            response = self.getSimInfo(nsce)
        except PhenixError:
            num = None
        if response:
            num = response["msisdn"]

        return num

    def getLineStatus(self, msisdn, nsce):
        result = None
        response = self.getLineInfo(msisdn)
        if response:
            if response["simsn"] and nsce != response["simsn"]:
                self.logger.warning(
                    f"msisdn ({msisdn}) and nsce mismatch ({nsce} ≠ {response['simsn']})"
                )
            result = response["etat"].lower()
        return result

    def getOptions(self, provider):
        url = "/GsmApi/V2/GetGsmProduitsByOperator"
        data = {"operateur": provider.upper()}
        return self.get(url, data=data)

    def requestActivation(self, params):
        url = "/GsmApi/V2/MsisdnActivate"
        data = params
        return self.post(url, data)


class NormalizedBazileConnector(BazileConnector):
    def getSimInfo(self, nsce):
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
            "sva": simInfo["Sva"],
            "wha": simInfo["Wha"],
            "roaming": sanitize(simInfo["Data_statut"]),
            "voicemail": sanitize(simInfo["Messagerie_vocale"]),
            "rio": sanitize(simInfo["RIO"]),
            "oopAmount": sanitize(simInfo["Palier_HF"]),
            "oopDataAuth": sanitize(simInfo["HF Data autorisé"]),
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

    def getLineStatus(self, msisdn, nsce):
        response = self.getSimInfo(nsce)
        if response["msisdn"] and msisdn != response["msisdn"]:
            self.logger.warning(
                f"msisdn and nsce ({nsce}) mismatch ({msisdn} ≠ {response['msisdn']})"
            )
        return response["status"]
