import json
from datetime import datetime

from dateutil.relativedelta import relativedelta

from .operators.bazile import NormalizedBazileConnector
from .operators.phenix import PhenixConnector


class GsmLine:
    msisdn: str
    nsce: str
    operator: str

    def __init__(self, msisdn, nsce, operator):
        self.msisdn = msisdn
        self.nsce = nsce
        self.operator = operator


class TelecomOperatorConnector:
    _connectors = {}
    defaultOperator: str | None = None

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
        self.logger.debug(f"[Operator] callMethod - operator:{ope}")
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


# Commands
commands = {
    "get-products-orange": lambda runner: print(
        json.dumps(
            runner.getTelecomConnector().getProductsOrange(operator="phenix"), indent=2
        )
    )
}


def execute(runner, command):
    if command in commands:
        commands[command](runner)
