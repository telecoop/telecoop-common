import json


def authorizeHf(self) -> None:
    accountId = self.getArg("Account id")
    authorize = self.getArg("Authorize")
    if authorize in ("oui", "non"):
        auth = authorize == "oui"
    else:
        self.logger.critical("Authorize should be 'oui' or 'non'")
        return

    bazileConnector = self.getBazileConnector()
    print(json.dumps(bazileConnector.authorizeHF(accountId, authorize=auth)))


def getSimplePortaHistory(self) -> None:
    nsce = self.getArg("NSCE")
    bazileConnector = self.getBazileConnector()
    print(
        json.dumps(bazileConnector.getSimplePortaHistory(nsce), indent=2, default=str)
    )


def getConso(self) -> None:
    accountId = self.getArg("Account id")
    month = self.getArg("Month", "date")
    bazileConnector = self.getBazileConnector()
    print(
        json.dumps(
            bazileConnector.getConso(accountId, month.strftime("%Y-%m")),
            indent=2,
        )
    )


commands = {
    "authorize-hf": authorizeHf,
    "get-conso": getConso,
    "get-simple-porta-history": getSimplePortaHistory,
}


def execute(runner, command):  # pragma: no cover
    if command in commands:
        commands[command](runner)
