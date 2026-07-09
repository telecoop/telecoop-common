from datetime import date, datetime

import pytz

from .utils import sellsyValues


class SellsyClient:
    def __init__(self, id):
        self.id = id
        self.creationDate: datetime
        self.conversionToClientDate = None
        self.actif = None
        self.reference = None
        self.type = None
        self.label = None
        self.civility = None
        self.name = None
        self.firstname = None
        self.companyName = None
        self.email = None
        self.invoiceEmail = None
        self.phoneNumber = None
        # Should delete this one, but not sur if used somewhere
        self.msisdn = None
        self.web = None
        self.mainContactId = None
        self.birthDate = None
        self.birthPlace = None
        self.address = None
        self.zipCode = None
        self.city = None
        self.country = None
        self.oneInvoicePerLine = None
        self.autoValidation = None
        self.status = None
        self.preferredPaymentMethod = None
        self.member = None
        self.memberCategory = None
        self.phoneModel = None
        self.meanDataUsage = None
        self.meanMessagesSent = None
        self.meanVoiceUsage = None
        self.phoneState = None
        self.phoneYear = None

        self.optinTeleCommown = None
        self.telecommownStart = None
        self.telecommownEnd = None
        self.telecommownAbo = None
        self.telecommownOrigin = None
        self.sponsorCode = None
        self.sponsorLink = None
        self.sponsorNbUse = None
        self.sponsorNbDiscount = None
        self.sponsorNbCodeDonated = None
        self.refereeCode: str
        self.promoCode: str
        self.slimpayMandateStatus = None
        self.discounts: int

        self.lines = []

    def __str__(self):
        return f"#{self.id} {self.reference} {self.label} {self.email} {self.status} {self.creationDate.isoformat()}"

    @classmethod
    def create(cls, values, sellsyConnector):
        sc = sellsyConnector
        if "name" not in values:
            raise ValueError("Client name is missing")
        data = {"third": {}}
        fields = [
            "name",
            "ident",
            "type",
            "email",
            "mobile",
            "joinDate",
            "web",
            "siret",
            "siren",
            "vat",
            "rcs",
            "apenaf",
            "tags",
        ]
        for fld in fields:
            if fld in values:
                data["third"][fld] = values[fld]
        if "contact" in values:
            fields = [
                "name",
                "forename",
                "email",
                "mobile",
                "web",
                "position",
                "civil",
                "birthdate",
            ]
            contact = values["contact"]
            data["contact"] = {}
            for fld in fields:
                if fld in contact:
                    data["contact"][fld] = contact[fld]
        if "address" in values:
            fields = [
                "name",
                "part1",
                "part2",
                "part3",
                "part4",
                "zip",
                "town",
                "countrycode",
            ]
            address = values["address"]
            data["address"] = {}
            for fld in fields:
                if fld in address:
                    data["address"][fld] = address[fld]

        response = sc.api(method="Client.create", params=data)
        sc.logger.debug(response)
        clientId = response["client_id"]
        if "customFields" in values:
            cfIds = sellsyValues[sc.env]["custom_fields"]
            for cfName, cfValue in values["customFields"].items():
                sc.updateCustomField("client", clientId, cfIds[cfName], cfValue)

        cli = SellsyClient(clientId)
        cli.load(sc)
        return cli

    def load(self, connector):
        self.loadWithValues(connector.getClientValues(self.id))

    def loadWithValues(self, cli):
        parisTZ = pytz.timezone("Europe/Paris")
        email = cli["email"]
        invoiceEmail = None
        name = cli["people_name"]
        firstname = cli["people_forename"]
        civility = cli.get("people_civil")
        # recherche du contact principal
        mainContactId = cli["maincontactid"]
        if "contacts" in cli:
            for contactId, contact in cli["contacts"].items():
                if contactId == mainContactId:
                    email = contact["email"]
                    name = contact["name"]
                    firstname = contact["forename"]
                    civility = contact["civil"]
                elif (
                    "isBillingContact" in contact and contact["isBillingContact"] == "Y"
                ):
                    invoiceEmail = contact["email"]
        if invoiceEmail is None:
            invoiceEmail = email

        actif = cli.get("actif")
        self.creationDate = parisTZ.localize(datetime.fromisoformat(cli["joindate"]))
        if (
            cli["dateTransformProspect"] is not None
            and cli["dateTransformProspect"][0:4] != "0000"
        ):
            self.conversionToClientDate = parisTZ.localize(
                datetime.fromisoformat(cli["dateTransformProspect"])
            )
        self.tags = (
            [t["word"] for _, t in cli["smartTags"].items()]
            if "smartTags" in cli and cli["smartTags"] != []
            else []
        )
        self.actif = actif == "Y" if actif else None
        self.reference = cli["ident"]
        self.type = cli["type"]
        self.label = cli["name"]
        self.name = name
        self.firstname = firstname
        self.civility = civility
        self.companyName = cli["name"] if self.type == "corporation" else None
        self.email = email
        self.invoiceEmail = invoiceEmail
        self.phoneNumber = cli["mobile"]
        self.web = cli.get("web")
        self.msisdn = cli["mobile"].replace("+33", "0") if cli["mobile"] else None
        self.mainContactId = mainContactId
        self.address = cli["addr_part1"]
        self.zipCode = cli["addr_zip"]
        self.city = cli["addr_town"]
        self.country = cli["addr_countrycode"]
        self.lines = []
        for f in cli["customfields"]:
            code = f["code"]
            if code == "facturationmanuelle":
                if f["formatted_value"] == "hors process":
                    self.autoValidation = None
                else:
                    self.autoValidation = f["formatted_value"] in ["", "automatique"]
            elif code == "facture-unique":
                self.oneInvoicePerLine = f["boolval"] == "N"
            elif code == "statut-client-abo-mobile" and "formatted_value" in f:
                self.status = f["formatted_value"]
            elif code == "paiementfavori":
                self.preferredPaymentMethod = f["formatted_value"]

            elif code == "societaire":
                self.member = f["textval"]
            elif code == "categorie-societaire":
                self.memberCategory = f["formatted_value"]
            elif code == "typetelephone":
                self.phoneModel = f["textval"]
            elif code == "consomoyenneclient":
                self.meanDataUsage = int(f["numericval"])
            elif code == "smsmoyen":
                self.meanMessagesSent = int(f["numericval"])
            elif code == "hrappel":
                self.meanVoiceUsage = int(f["numericval"])
            elif code == "neufreconditionne":
                self.phoneState = f["formatted_value"]
            elif code == "achattelephone":
                self.phoneYear = int(f["numericval"])

            elif code == "parrainage-code":
                self.sponsorCode = f["textval"]
            elif code == "parrainage-lien":
                self.sponsorLink = f["textval"]
            elif code == "parrainage-code-nb-use":
                self.sponsorNbUse = int(f["numericval"])
            elif code == "parrainage-nb-discount":
                self.sponsorNbDiscount = int(f["numericval"])
            elif code == "parrainage-code-parrain":
                self.refereeCode = f["textval"]
            elif code == "parrainage-nb-code-donated":
                self.sponsorNbCodeDonated = int(f["numericval"])

            elif (
                code == "offre-telecommown"
                and "formatted_ymd" in f
                and f["formatted_ymd"] != ""
            ):
                self.optinTeleCommown = parisTZ.localize(
                    datetime.strptime(f["formatted_ymd"], "%Y-%m-%d")
                )
            elif (
                code == "telecommown-date-debut"
                and "formatted_ymd" in f
                and f["formatted_ymd"] != ""
            ):
                self.telecommownStart = parisTZ.localize(
                    datetime.strptime(f["formatted_ymd"], "%Y-%m-%d")
                )
            elif (
                code == "telecommown-date-fin"
                and "formatted_ymd" in f
                and f["formatted_ymd"] != ""
            ):
                self.telecommownEnd = parisTZ.localize(
                    datetime.strptime(f["formatted_ymd"], "%Y-%m-%d")
                )
            elif code == "telecommown-origine":
                self.telecommownOrigin = f["formatted_value"]
            elif code == "abo-telecommown":
                if isinstance(f["boolval"], bool):
                    self.telecommownAbo = f["boolval"]
                else:
                    self.telecommownAbo = f["boolval"] == "Y"

            elif (
                code == "datenaissance"
                and "formatted_ymd" in f
                and f["formatted_ymd"] != ""
            ):
                self.birthDate = date.fromisoformat(f["formatted_ymd"])
            elif code == "lieunaissance":
                self.birthPlace = f["textval"]

            elif code == "code-promo":
                self.promoCode = f["textval"]

            elif code == "slimpay-mandate-status":
                self.slimpayMandateStatus = f["textval"]

    def getOpportunities(self, connector):
        opps = connector.getClientOpportunities(self.id)
        for opp in opps:
            opp.client = self
        return opps

    def updateStatus(self, connector, context=None):
        clientOpps = self.getOpportunities(connector)
        nbActiveLines = 0
        for clientOpp in clientOpps:
            if (
                clientOpp.funnelId in connector.funnelIdSim
                and clientOpp.isActiveOrSuspended(connector)
            ):
                nbActiveLines += 1
        if nbActiveLines == 0:
            status = "Résilié"
            if context is None:
                status = "Résilié"
            elif context == "termination":
                status = "Résilié avec dettes ou crédits"
            connector.updateCustomField(
                "client", self.id, connector.cfIdStatusClientMobile, status
            )
