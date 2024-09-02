#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import pytz
from datetime import datetime, date

from telecoopcommon.sellsy import (
    TcSellsyConnector,
    SellsyClient,
    SellsyOpportunity,
    sellsyValues,
    SellsyInvoice,
)
from telecoopcommon.sellsy import SellsyMemberOpportunity
from telecoopcommon.telecoop import Connector as TcConnector
from telecoopcommon.operator import Connector as TelecomConnector
from telecoopcommon.bazile import Connector as BazileConnector

# Script utils
import argparse
import configparser


def cmdline():
    parser = argparse.ArgumentParser(description="TeleCoop Common lib client")
    parser.add_argument(
        "--log-level",
        metavar="LOGLEVEL",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "CONFIG"],
        default="CONFIG",
        help="Log level of the script",
    )
    parser.add_argument(
        "command",
        metavar="COMMAND",
        choices=[
            "get-opportunity",
            "get-client",
            "get-client-from-ref",
            "get-clients",
            "get-opportunities-in-step",
            "get-client-opportunities",
            "create-client",
            "create-opportunity",
            "terminate-opp",
            "get-invoice",
            "get-invoices",
            "update-invoice-status",
            "update-invoice-paydate",
            "send-invoice",
            "create-payment",
            "delete-payment",
            "get-member-opp",
            "get-member-opps",
            "update-client",
            "update-cf",
            "get-tc-token",
            "get-code",
            "get-codes",
            "create-code",
            "get-sponsorship-code",
            "link-to-referee",
            "applied-to-referee",
            "get-updated-opportunities",
            "bazile-get-conso",
            "bazile-get-simple-porta-history",
            "authorize-hf",
            "get-sim-info",
            "get-conso",
            "get-phenix-options",
            "script",
        ],
        help="command",
    )
    parser.add_argument(
        "arguments", metavar="ARGS", nargs="*", help="command arguments"
    )
    return parser.parse_args()


class Logger:
    def critical(self, message):
        print(message)

    def warning(self, message):
        print(message)

    def info(self, message):
        print(message)

    def debug(self, message):
        print(message)


class Runner:
    def __init__(self, env, config, logger, args):
        self.env = env
        self.config = config
        self.logger = logger
        self.args = args

        if env in ["DEV", "LOCAL", "DOCKER"]:
            self.confSellsy = config["SellsyDev"]
        elif env == "PROD":
            self.confSellsy = config["SellsyProd"]

        self.dbConnStr = []
        for cnf in config.items("Bdd"):
            self.dbConnStr.append("{item}={value}".format(item=cnf[0], value=cnf[1]))

    def getBazileConnector(self):
        return BazileConnector(self.config["BazileAPI"], self.logger)

    def getSellsyConnector(self):
        return TcSellsyConnector(self.confSellsy, self.logger)

    def getTelecoopConnector(self):
        return TcConnector(self.config["TeleCoopApi"], self.logger)

    def getTelecomConnector(self):
        return TelecomConnector(self.config, self.logger)

    def getArg(self, name, type="str", help=None):
        if len(self.args.arguments) == 0:
            message = f"{name} needed"
            if help is not None:
                message += f" {help}"
            self.logger.critical(message)
            sys.exit(1)
        valueStr = self.args.arguments.pop(0)
        if type == "date":
            try:
                value = date.fromisoformat(valueStr)
            except ValueError:
                self.logger.critical(f"{name} (YYYY-MM-DD) needed")
                sys.exit(1)
        elif type == "datetime":
            try:
                value = datetime.fromisoformat(valueStr)
            except ValueError:
                self.logger.critical(f"{name} (YYYY-MM-DD HH-MI-SS) needed")
                sys.exit(1)
        elif type == "bool":
            value = valueStr == "true"
        else:
            value = valueStr
        return value

    def run(self, command):
        if command == "get-opportunity":
            id = self.getArg("Opportunity id")
            sellsyConnector = self.getSellsyConnector()
            # o = SellsyMemberOpportunity(id)
            o = SellsyOpportunity(id)
            o.load(sellsyConnector)
            print(o)
            print(o.planItem)
            print(o.status)
            print(o.getSimStateFromStep(sellsyConnector))
            print(o.operator)
            print(o.tags)
            print(o.mobileDataOutOfPlan)
            print(o.sourceId)
            print(o.sourceName)
            print(o.stepName)

        if command == "get-client":
            id = self.getArg("Client id")
            client = self.getSellsyConnector().getClient(id)
            print(client)
            print(client.invoiceEmail)
            print(client.conversionToClientDate)
            print(client.member)
            print(client.phoneModel)
            print(client.meanDataUsage)
            print(client.meanMessagesSent)
            print(client.meanVoiceUsage)
            print(client.phoneState)
            print(client.phoneYear)
            print(isinstance(client.telecommownAbo, bool))

        if command == "get-client-from-ref":
            ref = self.getArg("Client ref")
            client = self.getSellsyConnector().getClientFromRef(ref)
            print(client)
            print(client.oneInvoicePerLine)
            print(client.memberCategory)
            print(client.preferredPaymentMethod)

        if command == "get-clients":
            clients = self.getSellsyConnector().getClients(True)
            print(len(clients))
            print(next(iter(clients.values())))

        if command == "create-opportunity":
            name = self.getArg("name")
            ref = self.getArg("Reference")
            clientId = self.getArg("Client ID")
            funnel = self.getArg("Funnel")
            step = self.getArg("Step")
            msisdn = self.getArg("Msisdn")
            env = "PROD" if self.env == "PROD" else "DEV"
            sc = self.getSellsyConnector()
            values = {
                "name": name,
                "reference": ref,
                "clientId": clientId,
                "sourceId": sc.opportunitySourceInterne,
                "funnelId": sellsyValues[env][funnel],
                "stepId": sellsyValues[env][step],
                "customFields": {
                    "pro-nb-sims": 10,
                    "nsce": "12345",
                    "forfait": "Sobriété",
                    "pack-depannage": 1,
                    "abo-telecommown": "Y",
                    "date-activation-sim-souhaitee": datetime.now(pytz.utc).timestamp(),
                    "numerotelecoop": msisdn,
                },
            }
            print(values)
            opp = SellsyOpportunity.create(values, sc)
            print(opp)

        if command == "terminate-opp":
            tsc = self.getSellsyConnector()
            oppId = self.getArg("Oppontunity id")
            opp = SellsyOpportunity(oppId)
            opp.load(tsc)
            opp.terminate(tsc)

        if command == "get-opportunities-in-step":
            funnelId = self.getArg("Funnel id")
            step = self.getArg("Step")
            startDate = None
            if len(self.args.arguments) > 0:
                startDate = self.getArg("Start date", "datetime")
            limit = None
            if len(self.args.arguments) > 0:
                limit = int(self.getArg("Limit"))
            connector = self.getSellsyConnector()
            env = "PROD" if self.env == "PROD" else "DEV"
            stepId = sellsyValues[env][step] if step != "all" else step
            # searchParams = {'status': ['open', 'won', 'lost', 'late', 'closed']}
            searchParams = None
            opps = connector.getOpportunitiesInStep(
                funnelId,
                stepId,
                limit=limit,
                startDate=startDate,
                searchParams=searchParams,
            )
            print(len(opps))
            # for opp in opps:
            #   print(f"{opp.id} {opp.planItem}")

        if command == "get-client-opportunities":
            clientId = self.getArg("Client id")
            opps = self.getSellsyConnector().getClientOpportunities(clientId)
            print(opps)

        if command == "create-client":
            name = self.getArg("name")
            ref = self.getArg("Reference")
            clientType = self.getArg("Type")
            sc = self.getSellsyConnector()
            values = {"name": name, "ident": ref, "type": clientType}
            if clientType == "person":
                values["contact"] = {
                    "name": "GEOFFROY",
                    "forename": "Pierre",
                    "mobile": "0610658293",
                }
            values["address"] = {
                "name": "facturation",
                "part1": "28 rue Jean Bras",
                "zip": "35200",
                "town": "Rennes",
                "countrycode": "FR",
            }
            values["customFields"] = {
                "facturationmanuelle": "automatique",
                "telecommown-date-debut": datetime.now(pytz.utc).timestamp(),
                "mean-messages-sent": "10",
                "phone-model": "fairphone 4",
            }
            cli = SellsyClient.create(values, sc)
            print(cli)

        if command == "get-invoice":
            invoiceId = self.getArg("Invoice id")
            docType = self.getArg("Doc type")
            invoice = SellsyInvoice(invoiceId, docType)
            invoice.load(self.getSellsyConnector())
            print(invoice)
            print(invoice.docType)
            print(invoice.payMediums)

        if command == "get-invoices":
            searchParams = None
            if len(self.args.arguments) > 0:
                invoiceStatus = self.getArg("Invoice status")
                searchParams = {
                    "steps": [
                        invoiceStatus,
                    ]
                }
            invoices = SellsyInvoice.getInvoices(
                self.getSellsyConnector(),
                self.logger,
                startDate=datetime(2022, 1, 1),
                searchParams=searchParams,
                paymentMedium="prélèvement",
                limit=10,
                fetchLines=True,
            )
            print(invoices)

        if command == "update-invoice-status":
            invoiceId = self.getArg("Invoice id")
            status = self.getArg("Status")
            self.getSellsyConnector().updateInvoiceStatus(invoiceId, status)

        if command == "update-invoice-paydate":
            invoiceId = self.getArg("Invoice id")
            nbDays = self.getArg("Nb days")
            self.getSellsyConnector().updateInvoicePaymentDate(invoiceId, nbDays)

        if command == "send-invoice":
            invoiceId = self.getArg("Invoice id")
            docType = self.getArg("Doc Type")
            email = self.getArg("email")
            templateCode = self.getArg("Template code")

            syC = self.getSellsyConnector()
            templateId = syC.emailTemplates[templateCode]
            invoice = SellsyInvoice(invoiceId, docType)
            invoice.load(syC)
            invoice.sendByMail(email, syC, templateId)

        if command == "create-payment":
            invoiceId = self.getArg("Invoice id")
            docType = self.getArg("Doc type")
            amount = float(self.getArg("Amount"))
            label = self.getArg("Label")
            paymentDate = datetime.now()
            paymentId = self.getSellsyConnector().createPayment(
                invoiceId, paymentDate, amount, label, docType
            )
            print(paymentId)

        if command == "delete-payment":
            paymentId = self.getArg("Payment id")
            invoiceId = self.getArg("Invoice id")
            docType = self.getArg("Doc type")
            self.getSellsyConnector().deletePayment(paymentId, invoiceId, docType)

        if command == "get-member-opp":
            opportunityId = self.getArg("Opportunity id")
            opp = SellsyMemberOpportunity(opportunityId)
            opp.load(self.getSellsyConnector())
            print(opp)
            print(
                f"{opp.sharesAmount} {opp.paymentDate} {opp.acceptedDate} {opp.formSentDate}"
            )

        if command == "get-member-opps":
            opps = SellsyMemberOpportunity.getOpportunities(
                self.getSellsyConnector(), self.logger
            )
            print(len(opps))
            print(next(iter(opps)))

        if command == "update-client":
            id = self.getArg("Client id")
            prop = self.getArg("Property")
            value = self.getArg("Property value")
            response = self.getSellsyConnector().updateClientProperty(id, prop, value)
            print(response)

        if command == "update-cf":
            env = "PROD" if self.env == "PROD" else "DEV"
            entity = self.getArg("entity")
            id = self.getArg("Entity id")
            customField = self.getArg("Custom field")
            cfid = sellsyValues[env]["custom_fields"][customField]
            value = self.getArg("Value")
            if value == "True":
                value = True
            if value == "False":
                value = False
            response = self.getSellsyConnector().updateCustomField(
                entity, id, cfid, value
            )
            print(response)

        if command == "get-tc-token":
            response = self.getTelecoopConnector().getToken()
            print(response.text)

        if command == "get-code":
            code = self.getArg("code")
            response = self.getTelecoopConnector().getCode(code)
            print(response.text)

        if command == "get-codes":
            codeType = self.getArg("code type")
            codeType = int(codeType) if codeType != "-" else None
            response = self.getTelecoopConnector().getCodes(codeType=codeType)
            print(response.text)
            print(response.json())
            print([c["value"] for c in response.json()])

        if command == "create-code":
            type = self.getArg("code type")
            amount = self.getArg("code amount")
            value = None
            if len(self.args.arguments) > 0:
                value = self.getArg("value")
            response = self.getTelecoopConnector().createCode(
                value=value, type=type, amount=amount
            )
            print(response.text)

        if command == "get-sponsorship-code":
            clientRef = self.getArg("Client ref")
            response = self.getTelecoopConnector().getSponsorshipCode(clientRef)
            print(response.text)

        if command == "link-to-referee":
            referee = self.getArg("Referee")
            clientRef = self.getArg("Client ref")
            response = self.getTelecoopConnector().linkToReferee(referee, clientRef)
            print(response.text)

        if command == "applied-to-referee":
            referee = self.getArg("Referee")
            clientRef = self.getArg("Client ref")
            response = self.getTelecoopConnector().appliedToReferee(referee, clientRef)
            print(response.text)

        if command == "get-updated-opportunities":
            startDate = self.getArg("Start date", "datetime")
            start = pytz.timezone("Europe/Paris").localize(startDate)
            sellsyConnector = self.getSellsyConnector()
            params = {"filters": {"updated_status": {"start": start.isoformat()}}}
            results = sellsyConnector.api2Post("/opportunities/search", params)
            print(json.dumps(results.json(), indent=2))

        if command == "bazile-get-conso":
            accountId = self.getArg("Account id")
            month = self.getArg("Month", "date")
            bazileConnector = self.getBazileConnector()
            print(
                json.dumps(
                    bazileConnector.getConso(accountId, month.strftime("%Y-%m")),
                    indent=2,
                )
            )

        if command == "authorize-hf":
            accountId = self.getArg("Account id")
            authorize = self.getArg("Authorize")
            if authorize in ("oui", "non"):
                auth = authorize == "oui"
            else:
                self.logger.critical("Authorize should be 'oui' or 'non'")
                return

            bazileConnector = self.getBazileConnector()
            print(json.dumps(bazileConnector.authorizeHF(accountId, authorize=auth)))

        if command == "bazile-get-simple-porta-history":
            nsce = self.getArg("NSCE")
            bazileConnector = self.getBazileConnector()
            print(
                json.dumps(
                    bazileConnector.getSimplePortaHistory(nsce), indent=2, default=str
                )
            )

        if command == "get-sim-info":
            operator = self.getArg("Operator")
            nsce = self.getArg("Sim num")
            tlC = self.getTelecomConnector()

            tlC.setDefaultOperator(operator)
            print(json.dumps(tlC.getSimInfo(nsce=nsce), indent=2, default=str))

        if command == "get-conso":
            msisdn = self.getArg("msisdn")
            month = self.getArg("month", "date")
            tlC = self.getTelecomConnector()

            tlC.setDefaultOperator("phenix")
            response = tlC.getConso(msisdn=msisdn, month=month)
            print(json.dumps(response, indent=2, default=str))

        if command == "get-phenix-options":
            provider = self.getArg("Provider")
            tlC = self.getTelecomConnector()
            tlC.setDefaultOperator("phenix")
            print(json.dumps(tlC.getOptions(provider=provider), indent=2, default=str))

        if command == "script":
            nsce = self.getArg("NSCE")
            bzC = self.getBazileConnector()
            print(bzC.isSimAvailable(nsce))


def main():
    args = cmdline()

    logger = Logger()

    fileDir = os.path.dirname(os.path.realpath(__file__))
    # Parent directory of this file's directory
    root = os.path.dirname(os.path.dirname(fileDir))
    os.chdir(root)

    env = os.getenv("ENV", "LOCAL")
    print(env)
    if env in ["DOCKER", "PROD", "TEST"]:
        confFile = "/etc/telecoop-common/conf.cfg"
    elif env is None or env == "LOCAL":
        confFile = os.path.join(fileDir, "../conf/conf.cfg")
    if not os.path.isfile(confFile):
        raise IOError("{} : file not found".format(confFile))
    config = configparser.ConfigParser()
    config.read(confFile)

    runner = Runner(env, config, logger, args)

    command = args.command

    runner.run(command)


if __name__ == "__main__":
    main()
