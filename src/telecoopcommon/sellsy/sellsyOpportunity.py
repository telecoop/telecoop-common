import os
from datetime import datetime

import pytz

from .sellsyClient import SellsyClient
from .utils import getSourceIdFromValue, sellsyValues, sourceNameFromId, stepNameFromId


class SellsyOpportunity:
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
        self.tags = None
        self.stepId: int
        self.stepStart = None
        self.steps: dict
        self.status = None
        self.nsce = None
        self.msisdn = None
        self.operator = None
        self.simType = None
        self.operatorRef = None
        self.rio = None
        self.plan = None
        self.planItem = None
        self.mobileDataOutOfPlan = None
        self.achatSimPhysique = None
        self.onSite = None  # Same as above
        self.dateActivationSimAsked = None
        self.optinTeleCommown = None
        self.telecommownStart = None
        self.telecommownEnd = None
        self.telecommownAbo = None
        self.telecommownOrigin = None
        self.promoCode = None
        self.refereeCode = None
        self.packDepannage = None
        self.packDepannageUsed = None
        self.invoicingSetting = None
        self.proNbSims = None
        self.proNbPorta = None
        self.proDateEngagement = None
        self.proAncienOperateur = None
        self.proEstimConso = None
        self.proComment = None
        self.proPrefRappel = None
        self.proNomUtilisateur = None
        self.proMailUtilisateur = None
        self.proPalierSuspension = None
        self.proAppelsInternationaux = None
        self.proDonneesMobiles = None
        self.proAchatContenu = None
        self.proAchatsSurtaxes = None

        self.plans = sellsyValues[self.env]["plans"]

    @property
    def stepName(self):
        return stepNameFromId(self.stepId)

    @property
    def sourceName(self):
        return sourceNameFromId(self.sourceId)

    def __str__(self):
        return f"#{self.id} {self.creationDate} {self.msisdn} client #{self.clientId}"

    @classmethod
    def create(cls, values, sellsyConnector):
        sc = sellsyConnector
        if "name" not in values:
            raise ValueError("Opportunity name is missing")
        data = {"opportunity": {}}
        fields = [
            ("linkedtype", "type"),
            ("linkedid", "clientId"),
            ("ident", "reference"),
            ("sourceid", "sourceId"),
            ("creationDate", "creationDate"),
            ("name", "name"),
            ("funnelid", "funnelId"),
            ("stepid", "stepId"),
            ("contacts", "contacts"),
            ("potential", "amount"),
            ("dueDate", "dueDate"),
        ]
        for fldSellsy, fld in fields:
            if fld in values:
                data["opportunity"][fldSellsy] = values[fld]

        if "linkedtype" not in data["opportunity"]:
            data["opportunity"]["linkedtype"] = "third"

        response = sc.api(method="Opportunities.create", params=data)
        sc.logger.debug(response)
        oppId = response
        if "customFields" in values:
            cfIds = sellsyValues[sc.env]["custom_fields"]
            for cfName, cfValue in values["customFields"].items():
                sc.updateCustomField("opportunity", oppId, cfIds[cfName], cfValue)

        opp = SellsyOpportunity(oppId)
        opp.load(sc)
        return opp

    @classmethod
    def createPlanChange(cls, values, sellsyConnector):
        sc = sellsyConnector
        values["name"] = "changement de forfait"
        values["funnelId"] = sc.funnelIdPlanChange
        values["stepId"] = sc.stepPlanChangeInProgress
        return cls.create(values, sc)

    def load(self, connector):
        values = connector.getOpportunityValues(self.id)
        self.loadWithValues(values)

    def getClient(self, connector) -> SellsyClient:
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
        self.funnelId = int(opp["funnelid"])
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
        self.tags = opp["smarttags"].split(",") if opp["smarttags"] is not None else []

        for _, field in opp["customfields"].items():
            if "code" in field:
                code = field["code"]
                if code == "rio":
                    self.rio = field["textval"]
                if code == "forfait":
                    # plan should always be known
                    # BUT there's a bug in Sellsy in DEV env where custom field 'forfait' is unknown and unsettable.
                    # O joy.
                    if self.env == "DEV" and "formatted_value" in field:
                        self.plan = field["formatted_value"]
                    elif (
                        self.env in ["PROD", "LOCAL_PROD"]
                        and "formatted_value" in field
                    ):
                        self.plan = field["formatted_value"]
                if code == "nsce":
                    self.nsce = field["textval"]
                if code == "numerotelecoop":
                    self.msisdn = field["textval"]
                if code == "operateur":
                    val = field["formatted_value"]
                    self.operator = "Bazile" if val == "" else val
                if code == "sim-type":
                    self.simType = field["formatted_value"]
                if code == "refbazile":
                    self.operatorRef = field["textval"]
                if code == "depassement-forfait-data":
                    self.mobileDataOutOfPlan = field["formatted_value"]
                if code == "achatsimphysique":
                    if isinstance(field["boolval"], bool):
                        self.achatSimPhysique = field["boolval"]
                    else:
                        self.achatSimPhysique = field["boolval"] == "Y"
                    self.onSite = self.achatSimPhysique
                if (
                    code == "date-activation-sim-souhaitee"
                    and "formatted_ymd" in field
                    and field["formatted_ymd"] != ""
                ):
                    self.dateActivationSimAsked = datetime.strptime(
                        field["formatted_ymd"], "%Y-%m-%d"
                    ).astimezone(parisTZ)
                if (
                    code == "offre-telecommown"
                    and "formatted_ymd" in field
                    and field["formatted_ymd"] != ""
                ):
                    self.optinTeleCommown = datetime.strptime(
                        field["formatted_ymd"], "%Y-%m-%d"
                    ).astimezone(parisTZ)
                if (
                    code == "telecommown-date-debut"
                    and "formatted_ymd" in field
                    and field["formatted_ymd"] != ""
                ):
                    self.telecommownStart = datetime.strptime(
                        field["formatted_ymd"], "%Y-%m-%d"
                    ).astimezone(parisTZ)
                if (
                    code == "telecommown-date-fin"
                    and "formatted_ymd" in field
                    and field["formatted_ymd"] != ""
                ):
                    self.telecommownEnd = datetime.strptime(
                        field["formatted_ymd"], "%Y-%m-%d"
                    ).astimezone(parisTZ)
                if code == "telecommown-origine":
                    self.telecommownOrigin = field["formatted_value"]
                if code == "abo-telecommown":
                    if isinstance(field["boolval"], bool):
                        self.telecommownAbo = field["boolval"]
                    else:
                        self.telecommownAbo = field["boolval"] == "Y"
                if code == "code-promo":
                    self.promoCode = field["textval"]
                if code == "parrainage-code-parrain":
                    self.refereeCode = field["textval"]
                if code == "pack-depannage":
                    self.packDepannage = int(field["numericval"])
                if code == "pack-depannage-utilises":
                    self.packDepannageUsed = int(field["numericval"])
                if code == "choix-facturation":
                    self.invoicingSetting = field["formatted_value"]
                if code == "pro-nb-sims":
                    self.proNbSims = int(field["numericval"])
                if code == "pro-nb-porta":
                    self.proNbPorta = int(field["numericval"])
                if (
                    code == "pro-date-engagement"
                    and "formatted_ymd" in field
                    and field["formatted_ymd"] != ""
                ):
                    self.proDateEngagement = datetime.strptime(
                        field["formatted_ymd"], "%Y-%m-%d"
                    ).astimezone(parisTZ)
                if code == "pro-ancien-operateur":
                    self.proAncienOperateur = field["textval"]
                if code == "pro-estim-conso":
                    self.proEstimConso = field["textval"]
                if code == "pro-comment":
                    self.proComment = field["textval"]
                if code == "pro-pref-rappel":
                    self.proPrefRappel = field["textval"]
                if code == "pro-nom-utilisateur":
                    self.proNomUtilisateur = field["textval"]
                if code == "pro-mail-utilisateur":
                    self.proMailUtilisateur = field["textval"]
                if code == "pro-palier-suspension":
                    try:
                        self.proPalierSuspension = int(field["formatted_value"])
                    except ValueError:
                        self.proPalierSuspension = 150
                if code == "pro-appels-internationaux":
                    self.proAppelsInternationaux = field["formatted_value"]
                if code == "pro-donnees-mobiles":
                    self.proDonneesMobiles = field["formatted_value"]
                if code == "pro-achats-contenu":
                    self.proAchatContenu = field["boolval"]
                if code == "pro-achats-surtaxes":
                    self.proAchatsSurtaxes = field["boolval"]

        if self.plan in self.plans:
            self.planItem = self.plans[self.plan]

    def updateStep(self, stepId, connector):
        connector.api(
            method="Opportunities.updateStep", params={"oid": self.id, "stepid": stepId}
        )
        self.steps[stepId] = datetime.now().astimezone(pytz.timezone("Europe/Paris"))

    def updateStatus(self, status, connector):
        connector.api(
            method="Opportunities.updateStatus",
            params={"id": self.id, "status": status},
        )
        self.status = status

    def isPorta(self):
        return self.rio is not None and self.rio != "N/A" and self.rio != ""

    def isOldBazileLine(self):
        return self.rio is not None and self.rio[0:2] == "56"

    def getPlanItem(self):
        return self.planItem

    def getSimStateFromStep(self, sellsyConnector):
        sc = sellsyConnector
        state = None
        if self.stepId in [
            sc.stepNew,
            sc.stepReminder,
            sc.stepSimToSend,
            sc.stepSimToSendTransition,
            sc.stepProSimsInactive,
            sc.stepEsimOperatorChange,
            sc.stepEsimNewClient,
            sc.stepEsimVowifiRequest,
            sc.stepEsimEsimRequest,
        ]:
            state = "new"
        elif self.stepId in [
            sc.stepSimSent,
            sc.stepSimReceived,
            sc.stepProSimsAwaiting,
            sc.stepSimHandDelivered,
            sc.stepEsimSimSent,
        ]:
            state = "sent"
        elif self.stepId in [
            sc.stepSimPendingPorta,
            sc.stepSimPendingNew,
            sc.stepProSimActivating,
            sc.stepEsimPending,
        ]:
            state = "porta"
        elif self.stepId in [sc.stepSimActivated, sc.stepProSimsActivated]:
            state = "active"
        elif self.stepId in [sc.stepSimSuspended, sc.stepProSimsSuspended]:
            state = "suspended"
        elif self.stepId in [
            sc.stepSimTerminated,
            sc.stepProSimsTerminated,
            sc.stepEsimActivated,
        ]:
            state = "terminated"
        return state

    def terminate(self, connector, internal=False):
        if self.funnelId not in connector.funnelIdSim:
            raise RuntimeError(
                f"Unable to terminate opportunity {self.id}, {self.funnelId} not in {connector.funnelIdSim}"
            )

        stepTerminated = None
        if self.funnelId == connector.funnelIdVdc:
            stepTerminated = connector.stepSimTerminated
        elif self.funnelId == connector.funnelIdSimsPro:
            stepTerminated = connector.stepProSimsTerminated
        # If ligne is transfered from one of our operators to another, we don't want to mark the line as terminated
        # mostly not to send the client a termination email
        if not internal:
            self.updateStep(stepTerminated, connector)

        # update client status
        client = self.getClient(connector)
        client.updateStatus(connector, context="termination")

    def isActive(self, connector):
        return (
            str(connector.stepSimActivated) in self.steps
            or str(connector.stepProSimsActivated) in self.steps
        )

    def isSuspended(self, connector):
        return (
            str(connector.stepSimSuspended) in self.steps
            or str(connector.stepProSimsSuspended) in self.steps
        )

    def isActiveOrSuspended(self, connector):
        return self.isActive(connector) or self.isSuspended(connector)
