import json

from .sellsyClient import SellsyClient
from .sellsyOpportunity import SellsyOpportunity
from .utils import sellsyValues


def getOpportunity(runner):
    id = runner.getArg("Opportunity id")
    sellsyConnector = runner.getSellsyConnector()
    o = SellsyOpportunity(id)
    o.load(sellsyConnector)
    print(o)
    print(o.isPorta())
    print(o.planItem)
    print(o.status)
    print(o.getSimStateFromStep(sellsyConnector))
    print(o.operator)
    print(o.tags)
    print(o.mobileDataOutOfPlan)
    print(o.sourceId)
    print(o.sourceName)
    print(o.stepName)


def getClient(runner):
    id = runner.getArg("Client id")
    sellsyConnector = runner.getSellsyConnector()
    c = SellsyClient(id)
    c.load(sellsyConnector)
    print(c)
    print(c.tags)


def getCustomField(runner):
    syC = runner.getSellsyConnector()

    cfName = runner.getArg("Custom field ref")
    response = syC.api(
        method="CustomFields.getOne",
        params={"id": sellsyValues["PROD"]["custom_fields"][cfName]},
    )
    print(json.dumps(response, indent=2))


def getService(runner):
    syC = runner.getSellsyConnector()
    ref = runner.getArg("Service ref")
    response = syC.api(
        method="Catalogue.getOneByRef",
        params={
            "type": "service",
            "ref": ref,
        },
    )
    print(json.dumps(response, indent=2))


def testV2(runner):
    syC = runner.getSellsyConnector()

    events = syC.api2Get("/webhooks/events")
    print(json.dumps(events.json(), indent=2))


commands = {
    "get-client": lambda runner: getClient(runner),
    "get-opportunity": lambda runner: getOpportunity(runner),
    "get-services": lambda runner: print(
        json.dumps(runner.getSellsyConnector().getServices(), indent=2)
    ),
    "test-v2": testV2,
    "get-custom-field": getCustomField,
    "get-service": getService,
    "get-taxes": lambda runner: print(
        runner.getSellsyConnector().api(method="AccountDatas.getTaxes", params={})
    ),
    "get-categories": lambda runner: print(
        runner.getSellsyConnector().api(method="Catalogue.getCategories", params={})
    ),
}


def execute(runner, command):
    if command in commands:
        commands[command](runner)
