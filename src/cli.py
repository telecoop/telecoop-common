#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

import pytz
import psycopg2
from nats import NATS
from datetime import datetime

from telecoopcommon.sellsy import (
    TcSellsyConnector,
    SellsyClient,
    SellsyOpportunity,
    sellsyValues,
    SellsyInvoice,
    SellsyFile
)
#import telecoopcommon
#from telecoopcommon import *
from telecoopcommon.sellsy import SellsyMemberOpportunity
from telecoopcommon.telecoop import Connector as TcConnector
from telecoopcommon.operator import Connector as TelecomConnector
from telecoopcommon.bazile import Connector as BazileConnector
from telecoopcommon.runner import TcRunner, main
from telecoopcommon.natsWorker import TcNatsConnector

serviceName = "telecoop-common"
defaultPackageName = "telecoopcommon"

"""
modules = {
    "default": defaultPackageName,
    "main": {
        "name": defaultPackageName,
        "excluded": [
            "bazile",
            "runner",
            "cursor",
            "telecoop",
            "logs",
        ],
        "module": telecoopcommon,
    }
}
"""

additionalCommands = [
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
    "upload-file",
    "script",
]


class Runner(TcRunner):
    def __init__(self, env, config, logger, args, modules):
        super().__init__(env, config, logger, args, modules)
        self.postgres = psycopg2

        if env in ["DEV", "LOCAL", "DOCKER"]:
            self.confSellsy = config["SellsyDev"]
        elif env == "PROD":
            self.confSellsy = config["SellsyProd"]
        # self.confSellsy = config["Sellsy"]

    def getBazileConnector(self):
        return BazileConnector(self.config["BazileAPI"], self.logger)

    def getSellsyConnector(self):
        return TcSellsyConnector(self.confSellsy, self.logger)

    def getTelecoopConnector(self):
        return TcConnector(self.config["TeleCoopApi"], self.logger)

    def getTelecomConnector(self):
        return TelecomConnector(self.config, self.logger)

    async def getNatsConnection(self):
        nConn = NATS()
        if "cred" in self.config["Nats"]:
            await nConn.connect(
                self.config["Nats"]["url"],
                user_credentials=self.config["Nats"]["cred"],
                connect_timeout=10,
            )
        else:
            await nConn.connect(self.config["Nats"]["url"])
        return TcNatsConnector(nConn)

    def uploadFile(self):
        logger = self.logger
        sc = self.getSellsyConnector()
        kargs = json.loads(self.getArg("json"))
        # {"fileName":"toto", "filePath": "/tmp/toto.pdf", "fileMimetype":"application/pdf", "directoryId": "", "directoryType":"opportunity"}
        upload = SellsyFile.upload( 
            self,
            sellsyConnector=sc,
            logger=logger,
            **kargs
        )
        logger.debug("Upload response: " + upload)

    def getClient(self):
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

    def getClientFromRef(self):
        ref = self.getArg("Client ref")
        client = self.getSellsyConnector().getClientFromRef(ref)
        print(client)
        print(client.oneInvoicePerLine)
        print(client.memberCategory)
        print(client.preferredPaymentMethod)

    def getClients(self):
        clients = self.getSellsyConnector().getClients(True)
        print(len(clients))
        print(next(iter(clients.values())))

    def createOpportunity(self):
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

    def terminateOpp(self):
        tsc = self.getSellsyConnector()
        oppId = self.getArg("Oppontunity id")
        opp = SellsyOpportunity(oppId)
        opp.load(tsc)
        opp.terminate(tsc)

    def getOpportunitiesInStep(self):
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

    def getClientOpportunities(self):
        clientId = self.getArg("Client id")
        opps = self.getSellsyConnector().getClientOpportunities(clientId)
        print(opps)

    def createClient(self):
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

    def getInvoice(self):
        invoiceId = self.getArg("Invoice id")
        docType = self.getArg("Doc type")
        invoice = SellsyInvoice(invoiceId, docType)
        invoice.load(self.getSellsyConnector())
        print(invoice)
        print(invoice.docType)
        print(invoice.payMediums)

    def getInvoices(self):
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

    def updateInvoiceStatus(self):
        invoiceId = self.getArg("Invoice id")
        status = self.getArg("Status")
        self.getSellsyConnector().updateInvoiceStatus(invoiceId, status)

    def updateInvoicePaydate(self):
        invoiceId = self.getArg("Invoice id")
        nbDays = self.getArg("Nb days")
        self.getSellsyConnector().updateInvoicePaymentDate(invoiceId, nbDays)

    def sendInvoice(self):
        invoiceId = self.getArg("Invoice id")
        docType = self.getArg("Doc Type")
        email = self.getArg("email")
        templateCode = self.getArg("Template code")

        syC = self.getSellsyConnector()
        templateId = syC.emailTemplates[templateCode]
        invoice = SellsyInvoice(invoiceId, docType)
        invoice.load(syC)
        invoice.sendByMail(email, syC, templateId)

    def createPayment(self):
        invoiceId = self.getArg("Invoice id")
        docType = self.getArg("Doc type")
        amount = float(self.getArg("Amount"))
        label = self.getArg("Label")
        paymentDate = datetime.now()
        paymentId = self.getSellsyConnector().createPayment(
            invoiceId, paymentDate, amount, label, docType
        )
        print(paymentId)

    def deletePayment(self):
        paymentId = self.getArg("Payment id")
        invoiceId = self.getArg("Invoice id")
        docType = self.getArg("Doc type")
        self.getSellsyConnector().deletePayment(paymentId, invoiceId, docType)

    def getMemberOpp(self):
        opportunityId = self.getArg("Opportunity id")
        opp = SellsyMemberOpportunity(opportunityId)
        opp.load(self.getSellsyConnector())
        print(opp)
        print(
            f"{opp.sharesAmount} {opp.paymentDate} {opp.acceptedDate} {opp.formSentDate}"
        )

    def getMemberOpps(self):
        opps = SellsyMemberOpportunity.getOpportunities(
            self.getSellsyConnector(), self.logger
        )
        print(len(opps))
        print(next(iter(opps)))

    def updateClient(self):
        id = self.getArg("Client id")
        prop = self.getArg("Property")
        value = self.getArg("Property value")
        response = self.getSellsyConnector().updateClientProperty(id, prop, value)
        print(response)

    def updateCf(self):
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
        response = self.getSellsyConnector().updateCustomField(entity, id, cfid, value)
        print(response)

    def getTcToken(self):
        response = self.getTelecoopConnector().getToken()
        print(response.text)

    def getCode(self):
        code = self.getArg("code")
        response = self.getTelecoopConnector().getCode(code)
        print(response.text)

    def getCodes(self):
        codeType = self.getArg("code type")
        codeType = int(codeType) if codeType != "-" else None
        response = self.getTelecoopConnector().getCodes(codeType=codeType)
        print(response.text)
        print(response.json())
        print([c["value"] for c in response.json()])

    def createCode(self):
        type = self.getArg("code type")
        amount = self.getArg("code amount")
        value = None
        if len(self.args.arguments) > 0:
            value = self.getArg("value")
        response = self.getTelecoopConnector().createCode(
            value=value, type=type, amount=amount
        )
        print(response.text)

    def getSponsorshipCode(self):
        clientRef = self.getArg("Client ref")
        response = self.getTelecoopConnector().getSponsorshipCode(clientRef)
        print(response.text)

    def linkToReferee(self):
        referee = self.getArg("Referee")
        clientRef = self.getArg("Client ref")
        response = self.getTelecoopConnector().linkToReferee(referee, clientRef)
        print(response.text)

    def appliedToReferee(self):
        referee = self.getArg("Referee")
        clientRef = self.getArg("Client ref")
        response = self.getTelecoopConnector().appliedToReferee(referee, clientRef)
        print(response.text)

    def getUpdatedOpportunities(self):
        startDate = self.getArg("Start date", "datetime")
        start = pytz.timezone("Europe/Paris").localize(startDate)
        sellsyConnector = self.getSellsyConnector()
        params = {"filters": {"updated_status": {"start": start.isoformat()}}}
        results = sellsyConnector.api2Post("/opportunities/search", params)
        print(json.dumps(results.json(), indent=2))

    def bazileGetConso(self):
        accountId = self.getArg("Account id")
        month = self.getArg("Month", "date")
        bazileConnector = self.getBazileConnector()
        print(
            json.dumps(
                bazileConnector.getConso(accountId, month.strftime("%Y-%m")),
                indent=2,
            )
        )

    def authorizeHf(self):
        accountId = self.getArg("Account id")
        authorize = self.getArg("Authorize")
        if authorize in ("oui", "non"):
            auth = authorize == "oui"
        else:
            self.logger.critical("Authorize should be 'oui' or 'non'")
            return

        bazileConnector = self.getBazileConnector()
        print(json.dumps(bazileConnector.authorizeHF(accountId, authorize=auth)))

    def bazileGetSimplePortaHistory(self):
        nsce = self.getArg("NSCE")
        bazileConnector = self.getBazileConnector()
        print(
            json.dumps(
                bazileConnector.getSimplePortaHistory(nsce), indent=2, default=str
            )
        )

    def getSimInfo(self):
        operator = self.getArg("Operator")
        nsce = self.getArg("Sim num")
        tlC = self.getTelecomConnector()

        tlC.setDefaultOperator(operator)
        print(json.dumps(tlC.getSimInfo(nsce=nsce), indent=2, default=str))

    def getConso(self):
        msisdn = self.getArg("msisdn")
        month = self.getArg("month", "date")
        tlC = self.getTelecomConnector()

        tlC.setDefaultOperator("phenix")
        response = tlC.getConso(msisdn=msisdn, month=month)
        print(json.dumps(response, indent=2, default=str))

    def getPhenixOptions(self):
        provider = self.getArg("Provider")
        tlC = self.getTelecomConnector()
        tlC.setDefaultOperator("phenix")
        print(json.dumps(tlC.getOptions(provider=provider), indent=2, default=str))

    def script(self):
        nsce = self.getArg("NSCE")
        bzC = self.getBazileConnector()
        print(bzC.isSimAvailable(nsce))


if __name__ == "__main__":
    main(serviceName, Runner, defaultPackageName, additionalCommands)
