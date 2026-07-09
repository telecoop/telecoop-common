import os
from datetime import datetime

import pytz

from .sellsyClient import SellsyClient
from .utils import getSourceIdFromValue, sourceNameFromId, stepNameFromId


class SellsyMemberOpportunity:
    def __init__(self, id):
        env = os.getenv("ENV", "LOCAL")
        self.env = "PROD" if env in ["PROD", "LOCAL_PROD"] else "DEV"

        self.id = id
        self.reference = None
        self.name = None
        self.clientId = None
        self.client = None
        self.prospectId = None
        self.funnelId = None
        self.sourceId: int
        self.creationDate = None
        self.stepId: int
        self.stepStart = None
        self.steps = None
        self.status = None
        self.nbShares = None
        self.sharesAmount = None
        self.paymentDate = None
        self.acceptedDate = None
        self.paymentLabel = None
        self.paymentMode = None
        self.formSentDate = None

    @property
    def stepName(self):
        return stepNameFromId(self.stepId)

    @property
    def sourceName(self):
        return sourceNameFromId(self.sourceId)

    def __str__(self):
        return f"#{self.id} {self.creationDate} {self.nbShares} {self.stepName} / client #{self.clientId}"

    def load(self, connector):
        values = connector.getMembershipOpportunityValues(self.id)
        self.loadWithValues(values)

    def getClient(self, connector):
        if self.client is None and self.clientId is not None:
            self.client = SellsyClient(self.clientId)
            self.client.load(connector)
        return self.client

    def loadWithValues(self, opp):
        parisTZ = pytz.timezone("Europe/Paris")
        if opp["relationType"] == "client":
            self.clientId = opp["linkedid"]
        else:
            self.prospectId = opp["linkedid"]
        self.reference = opp["ident"]
        self.name = opp["name"]
        self.funnelId = opp["funnelid"]
        sourceId = (
            opp["sourceid"]
            if "sourceid" in opp
            else getSourceIdFromValue(opp["source"])
        )
        if sourceId:
            self.sourceId = int(sourceId)
        self.creationDate = parisTZ.localize(datetime.fromisoformat(opp["created"]))
        self.status = opp["statusLabel"]
        self.stepId = int(opp["stepid"])
        self.stepStart = parisTZ.localize(datetime.fromisoformat(opp["stepEnterDate"]))
        self.steps = {opp["stepid"]: self.stepStart}

        for _, field in opp["customfields"].items():
            if "code" in field:
                code = field["code"]
                if code == "partssocialessouhaite":
                    self.nbShares = field["numericval"]
                elif code == "montantparts":
                    self.sharesAmount = field["numericval"]
                elif (
                    code == "dateversementsocietariat"
                    and "formatted_ymd" in field
                    and field["formatted_ymd"] != ""
                ):
                    self.paymentDate = parisTZ.localize(
                        datetime.strptime(field["formatted_ymd"], "%Y-%m-%d")
                    )
                elif (
                    code == "dateacceptationsocietariat"
                    and "formatted_ymd" in field
                    and field["formatted_ymd"] != ""
                ):
                    self.acceptedDate = parisTZ.localize(
                        datetime.strptime(field["formatted_ymd"], "%Y-%m-%d")
                    )
                elif code == "moyen-de-paiement":
                    self.paymentMode = field["formatted_value"]
                elif code == "reference-paiement":
                    self.paymentLabel = field["textval"]
                elif (
                    code == "dateattestationenvoyee"
                    and "formatted_ymd" in field
                    and field["formatted_ymd"] != ""
                ):
                    self.formSentDate = parisTZ.localize(
                        datetime.strptime(field["formatted_ymd"], "%Y-%m-%d")
                    )

    def updateStep(self, stepId, connector):
        connector.api(
            method="Opportunities.updateStep", params={"oid": self.id, "stepid": stepId}
        )

    def updateStatus(self, status, connector):
        connector.api(
            method="Opportunities.updateStatus",
            params={"id": self.id, "status": status},
        )

    @classmethod
    def getOpportunities(
        cls,
        sellsyConnector,
        logger,
        startDate=None,
        limit=None,
        searchParams=None,
        paymentMedium=None,
    ):
        result = []
        sc = sellsyConnector
        for funnelId in [sc.funnelIdMembership, sc.funnelIdMembership2]:
            params = {
                "pagination": {"nbperpage": 1000, "pagenum": 1},
                "search": {"funnelid": funnelId},
            }
            if startDate is not None:
                params["search"]["periodecreated_start"] = startDate.timestamp()
            if searchParams is not None:
                for k, value in searchParams.items():
                    params["search"][k] = value

            opportunities = sc.api(method="Opportunities.getList", params=params)
            infos = opportunities["infos"]
            nbPages = infos["nbpages"]
            currentPage = 1
            while currentPage <= nbPages:
                logger.debug("Processing page {}/{}".format(currentPage, nbPages))
                for id, opp in opportunities["result"].items():
                    o = SellsyMemberOpportunity(id)
                    o.loadWithValues(opp)
                    result.append(o)
                    if limit is not None and limit <= len(result):
                        return result

                currentPage += 1
                if infos["pagenum"] <= nbPages:
                    params["pagination"]["pagenum"] = currentPage
                    opportunities = sc.api(
                        method="Opportunities.getList", params=params
                    )
                    infos = opportunities["infos"]

        return result
