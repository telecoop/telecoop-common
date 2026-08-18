import json


def getSimInfo(self) -> None:
    operator = str(self.getArg("Operator"))
    nsce = self.getArg("Sim num")
    tlC = self.getTelecomOperatorConnector()

    tlC.setDefaultOperator(operator)
    print(json.dumps(tlC.getSimInfo(nsce=nsce), indent=2, default=str))


def getConso(self) -> None:
    msisdn = self.getArg("msisdn")
    month = self.getArg("month", "date")
    tlC = self.getTelecomOperatorConnector()

    tlC.setDefaultOperator("phenix")
    response = tlC.getConso(msisdn=msisdn, month=month)
    print(json.dumps(response, indent=2, default=str))


def getPhenixOptions(self) -> None:
    provider = self.getArg("Provider")
    tlC = self.getTelecomOperatorConnector()
    tlC.setDefaultOperator("phenix")
    print(json.dumps(tlC.getOptions(provider=provider), indent=2, default=str))


commands = {
    "get-sim-info": getSimInfo,
    "get-conso": getConso,
    "get-phenix-options": getPhenixOptions,
}


def execute(runner, command):  # pragma: no cover
    if command in commands:
        commands[command](runner)
