import json
import pytz
from datetime import datetime
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

    def __init__(self, conf: dict, logger):
        self.conf = conf
        self.logger = logger

    def initConnector(self, operator):
        if operator.lower() == "bazile":
            self._connectors["bazile"] = NormalizedBazileConnector(
                self.conf["BazileAPI"], self.logger
            )
        elif operator.lower() == "phenix":
            self._connectors["phenix"] = PhenixConnector(
                self.conf["PhenixAPI"], self.logger
            )
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
            if ope not in self._connectors:
                self.initConnector(ope)

            self.logger.debug(self._connectors)
            func = getattr(self._connectors[ope], self.calledMethod)
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
        self.logger = logger

        self.token = None

    def getToken(self):
        if self.token is None:
            data = {"username": self.login, "password": self.password}
            url = self.host + "/Auth/authenticate"
            response = requests.post(url, json=data)
            self.logger.debug(f"Response from phenix: {response.text}")
            try:
                jsonResp = response.json()
            except json.decoder.JSONDecodeError as excp:
                self.logger.warning(
                    f"POSTed {url} with {data} and got a non json respons {response.text}"
                )
                raise PhenixError("Non JSON response") from excp
            self.token = jsonResp["access_token"]

        self.logger.debug(f"Token is {self.token}")
        return self.token

    def get(self, service, data={}):
        headers = {"Authorization": "Bearer " + self.getToken()}
        url = self.host + service
        params = data
        params["partenaireId"] = self.partnerId
        self.logger.debug(f"Calling GET {url} with headers {headers}")
        retry = 3
        result = None
        while retry >= 0:
            try:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code != 200:
                    exc = PhenixError(
                        f"Got code {response.status_code} \n{response.text}"
                    )
                    exc.statusCode = response.status_code
                    raise exc
                # We only want to retry when we got a 503 http code
                retry = -1
                result = response.json()
                if "etat" not in result:
                    raise PhenixError(f"Unknown response from Bazile {result}")
            except PhenixError as excp:
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
                raise PhenixError("Non JSON response") from excp
        return result

    def post(self, service, data):
        headers = {"Authorization": f"Bearer {self.getToken()}"}
        url = self.host + service
        data["partenaireId"] = self.partnerId
        self.logger.debug(f"Calling POST {url} with params {data}")
        response = requests.post(url, json=data, headers=headers)
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
        response = requests.patch(url, json=data, headers=headers)
        try:
            result = response.json()
        except json.decoder.JSONDecodeError as excp:
            self.logger.warning(
                f"PATCHed {url} with {data} and got a non json respons {response.text}"
            )
            raise PhenixError("Non JSON response") from excp
        return result

    def getSimInfo(self, nsce):
        url = "/GsmApi/V2/GetInfoSim"
        response = self.get(url, data={"simSN": nsce.replace(" ", "")})
        if "etat" not in response:
            raise PhenixError(f"Unknown response from Phenix {response}")
        result = {
            "nsce": response["simSN"],
            "imsi": response["imsi"],
            "typeSim": response["typeSim"],
            "operator": response["operateur"],
            "puk1": response["puk1"],
            "pin1": response["pin1"],
            "puk2": response["puk2"],
            "pin2": response["pin2"],
            "status": response["etat"].lower(),
            "msisdn": response["msisdn"],
            "clientCode": response["codeClient"],
            "orderSimId": response["commandeSimId"],
            "international": None,
            "sva": None,
            "wha": None,
            "roaming": None,
            "voicemail": None,
            "oopAmount": None,
        }
        return result

    def getLineInfo(self, msisdn):
        url = "/GsmApi/V2/MsisdnConsult"
        try:
            response = self.get(url, data={"msisdn": msisdn})
        except PhenixError as exp:
            if exp.statusCode == 404:
                self.logger.warning(f"Msisdn {msisdn} not found")
                return None
            raise exp
        return response

    def getActivationDate(self, msisdn):
        response = self.getLineInfo(msisdn)
        if "dateActivation" not in response:
            raise PhenixError("Unexpected response")

        activationDate = pytz.timezone("Europe/Paris").localize(
            datetime.fromisoformat(response["dateActivation"])
        )

        return activationDate

    def getNumFromSim(self, nsce):
        num = None
        try:
            response = self.getSimInfo(nsce)
            num = response["msisdn"]
        except PhenixError:
            num = None

        return num

    def getLineStatus(self, msisdn, nsce):
        response = self.getLineInfo(msisdn)
        if nsce != response["simsn"]:
            raise PhenixError("msisdn and nsce mismatch")
        return response["etat"].lower()


class NormalizedBazileConnector(BazileConnector):
    def getSimInfo(self, nsce):
        url = f"/ext/sim/{nsce.replace(' ', '')}"
        response = self.get(url)
        if "data" not in response:
            raise BazileError(f"Unknown respons from Bazile {response}")
        simInfo = response["data"]["Sim_information"]
        result = {
            "nsce": simInfo["Sim_serial"].strip(),
            "imsi": None,
            "typeSim": "SIM",
            "operator": "ORANGE",
            "puk1": simInfo["Puck1"].strip(),
            "pin1": simInfo["Pin1"].strip(),
            "puk2": simInfo["Puck2"].strip(),
            "pin2": simInfo["Pin2"].strip(),
            "status": simInfo["Statut"].strip().lower(),
            "msisdn": simInfo["Numero"].strip(),
            "clientCode": simInfo["Account_id"].strip(),
            "international": simInfo["Appels_internationaux"].strip(),
            "sva": simInfo["Sva"],
            "wha": simInfo["Wha"],
            "roaming": simInfo["Data_statut"].strip(),
            "voicemail": simInfo["Messagerie_vocale"].strip(),
            "rio": simInfo["RIO"].strip(),
            "oopAmount": simInfo["Palier_HF"].strip(),
            "oopDataAuth": simInfo["HF Data autorisé"].strip(),
        }
        return result

    def getLineStatus(self, msisdn, nsce):
        response = self.getSimInfo(nsce)
        if msisdn != response["msisdn"]:
            raise BazileError("msisdn and nsce mismatch")
        return response["status"]
