import os
from datetime import datetime
from decimal import Decimal

import phpserialize
import pytz

from .sellsyError import SellsyError


class SellsyInvoice:
    def __init__(self, invoiceId, docType):
        env = os.getenv("ENV", "LOCAL")
        self.env = "PROD" if env in ["PROD", "LOCAL_PROD"] else "DEV"

        self.id = invoiceId
        self.docType = docType
        self.reference = None
        self.sellsyStatus = None
        self.status = None
        self.amountHT: float | Decimal
        self.tva = None
        self.amountTTC: float | Decimal
        self.amountDue: float | Decimal
        self.paymentDate = None
        self.clientRef = None
        self.clientId = None
        self.subject = None
        self.creationDate = None
        self.payMediums = []

        self.rows = None

    def __str__(self):
        display = f"Invoice #{self.id} - {self.reference} {self.sellsyStatus}"
        display += f" : {round(self.amountTTC, 2)} € TTC ({round(self.amountHT, 2)} € HT) | {self.subject}"
        return display

    def load(self, sellsyConnector):
        values = sellsyConnector.getInvoiceValues(self.id, self.docType)
        self.loadWithValues(values)

    def loadWithValues(self, values):
        parisTZ = pytz.timezone("Europe/Paris")
        self.reference = values["ident"]
        self.sellsyStatus = values["status"]
        self.status = values["step_id"]
        self.amountHT = Decimal(values["totalAmountTaxesFree"])
        self.tva = Decimal(values["taxesAmountSum"])
        self.amountTTC = Decimal(values["totalAmount"])
        self.amountDue = Decimal(values["dueAmount"])
        try:
            self.paymentDate = parisTZ.localize(
                datetime.fromisoformat(values["payDateCustom"])
            )
        except ValueError:
            self.paymentDate = None
        self.clientRef = values["thirdident"]
        self.clientId = int(values["thirdid"])
        self.subject = values["subject"]
        self.payMediums = []
        if values["payMediumsText"] is not None and values["payMediumsText"] != "":
            self.payMediums = [
                v.decode("utf-8")
                for k, v in phpserialize.loads(
                    values["payMediumsText"].encode("utf-8")
                ).items()
            ]

        self.creationDate = parisTZ.localize(datetime.fromisoformat(values["created"]))

        if "rows" in values:
            self.rows = values["rows"]

    def createPayment(self, paymentDate, amount, label, sellsyConnector):
        return sellsyConnector.createPayment(
            self.id, paymentDate, amount, label, self.docType
        )

    def deletePayment(self, paymentId, sellsyConnector):
        sellsyConnector.deletePayment(paymentId, self.id, self.docType)

    @classmethod
    def getInvoices(
        cls,
        sellsyConnector,
        logger,
        startDate=None,
        limit=None,
        searchParams=None,
        paymentMedium=None,
        fetchLines=False,
    ):
        result = []
        for docType in ["invoice", "creditnote"]:
            params = {
                "doctype": docType,
                "pagination": {"nbperpage": 1000, "pagenum": 1},
                "search": {},
            }
            if startDate is not None:
                params["search"]["periodecreationDate_start"] = startDate.timestamp()
            if searchParams is not None:
                for k, value in searchParams.items():
                    params["search"][k] = value

            invoices = sellsyConnector.api(method="Document.getList", params=params)
            infos = invoices["infos"]
            nbPages = infos["nbpages"]
            currentPage = 1
            while currentPage <= nbPages:
                logger.debug(f"Processing page {currentPage}/{nbPages}")
                for invoiceId, invoice in invoices["result"].items():
                    i = SellsyInvoice(invoiceId, docType)
                    if fetchLines:
                        # Invoice lines are only present in Sellsy API call Document.getOne, so we must call getOne for each invoice
                        # … yeah, lame, I know
                        i.load(sellsyConnector)
                    else:
                        i.loadWithValues(invoice)
                    if paymentMedium is None or paymentMedium in i.payMediums:
                        result.append(i)
                    if limit is not None and limit <= len(result):
                        return result

                currentPage += 1
                if infos["pagenum"] <= nbPages:
                    params["pagination"]["pagenum"] = currentPage
                    invoices = sellsyConnector.api(
                        method="Document.getList", params=params
                    )
                    infos = invoices["infos"]

        return result

    @classmethod
    def generate(cls, invoiceId, data, connector, logger):
        logger.info(f"[Invoice #{invoiceId}] Generating in Sellsy")

        modelIds = connector.getModelIds()
        isPro = data["isPro"]
        modelId = modelIds["Facture mensuelle"]
        if isPro:
            modelId = modelIds["Facture Mensuelle Pro"]
        elif data["isFirstInvoice"]:
            modelId = modelIds["Forfait Sobriété - Prorata"]
        params = {
            "docid": modelId,
            "newDoctype": "invoice",
            "thirdid": data["sellsyClientId"],
        }
        model = connector.api(method="Document.getModel", params=params)
        params["docid"] = modelIds["Forfait Sobriété"]
        modelPL750 = connector.api(method="Document.getModel", params=params)
        params["docid"] = modelIds["Forfait Engagé"]
        modelFlex = connector.api(method="Document.getModel", params=params)

        rateCategories = connector.getRateCategories()
        docType = (
            "creditnote" if data["amount"] < 0 and data["isLastInvoice"] else "invoice"
        )
        params = {
            "document": {
                "doctype": docType,
                "thirdid": data["sellsyClientId"],
                "docspeakerStaffId": connector.ownerId,
                "subject": data["subject"].format(subject=model["subject"]),
                "doclayout": model["doclayout"],
                "payMediums": data["payMediums"],
                "enabledPaymentGateways": (
                    data["gateways"] if "gateways" in data else []
                ),
                "notes": data["notes"].format(
                    notes=model["notes"],
                    notesPL750=modelPL750["notes"],
                    notesFlex=modelFlex["notes"],
                ),
                "hidePayment": "Y",
                "rateCategory": (
                    rateCategories["Tarif HT"] if isPro else rateCategories["Tarif TTC"]
                ),
            },
            "paydate": {
                "id": model["paydate"],
                "xdays": model["paydate_xdays"],
                # 'xdays': TcSlimPayConnector.DELAY,
            },
            "row": {},
        }
        if data["parentInvoiceId"] is not None:
            params["document"]["parentId"] = data["parentInvoiceId"]
        if data["slimpayMandateStatus"] == "active":
            params["paydate"]["xdays"] = data["paymentDelay"]
            params["payMediums"] = None
        if data["paymentMethod"] == "Prélèvement":
            params["document"]["payMediums"] = [data["payMediums"]["prélèvement"]]
        elif data["paymentMethod"] == "Carte bancaire":
            params["document"]["payMediums"] = [data["payMediums"]["carte bancaire"]]
            params["document"]["enabledPaymentGateways"] = ["stripe"]
        elif data["paymentMethod"] == "Virement":
            params["document"]["payMediums"] = [data["payMediums"]["virement bancaire"]]

        hasKidPlan = False
        for i, row in enumerate(data["rows"]):
            if row["type"] == "item":
                if row["item"][0:3] == "kid":
                    hasKidPlan = True
                params["row"][i] = {
                    "row_type": row["type"],
                    "row_linkedid": row["serviceId"],
                    # 'row_unit': line['unitId'],
                    "row_unitAmount": row["unitAmount"],
                    "row_name": row["name"],
                    "row_notes": row["notes"],
                    "row_taxid": row["taxId"],
                    "row_qt": row["quantity"],
                }
            elif row["type"] in ["comment", "title"]:
                params["row"][i] = {
                    "row_type": row["type"],
                    f"row_{row['type']}": row[row["type"]],
                }
            else:
                params["row"][i] = {
                    "row_type": row["type"],
                }

        tags = []
        if data["isLastInvoice"]:
            tags.append("derniere-facture")
        if hasKidPlan:
            tags.append("forfait-enfant")
        if "tags" in data:
            tags += data["tags"]
        params["document"]["tags"] = ",".join(tags)

        method = "Document.create"
        if "docId" in data:
            method = "Document.update"
            params["docid"] = data["docId"]

        result = connector.api(method=method, params=params)
        # print(json.dumps(result, indent=2))
        if method == "Document.create":
            docId = result["doc_id"]
        else:
            docId = data["docId"]
        invoice = SellsyInvoice(docId, docType)

        logger.info(f"[Invoice #{invoiceId}] Fetching reference")
        try:
            invoice.load(connector)

            lessThan1 = data["amount"] > 0 and data["amount"] <= 0.2
            if (
                method == "Document.create"
                and data["automaticValidation"]
                and not lessThan1
                and (data["isLastInvoice"] or data["amount"] > 0)
            ):
                logger.info(
                    f"[Invoice #{invoiceId}] Automatic validation enabled : validating invoice"
                )
                invoice.validate(connector)
                invoice.sellsyStatus = "due"
        except SellsyError as exp:
            if exp.sellsy_code_error == "E_OBJ_NOT_LOADABLE":
                # Sellsy object was created (we have the docId) but not accessible yet through API
                # -> we use the docId as a reference and another process will check later
                #    to finish the validation of the invoice
                invoice.reference = invoice.id
            else:
                raise exp

        return invoice

    def validate(self, connector):
        params = {
            "docid": self.id,
            "document": {
                "doctype": self.docType,
                "step": "due" if self.docType == "invoice" else "stored",
            },
        }
        connector.api(method="Document.updateStep", params=params)

    def sendByMail(self, email, connector, templateId=None):
        if email:
            method = "Mails.sendOne"
            params = {
                "email": {
                    # We should specify only document informations if we want the template filled with its information
                    # If we supply client information, document id is ignored
                    # "linkedtype": "third",
                    # "linkedid": self.clientId,
                    "relatedtype": self.docType,
                    "relatedid": self.id,
                    "emails": [email],
                    "templateId": templateId,
                }
            }
            if templateId is None:
                method = "Document.sendDocByMail"
                params = {
                    "docid": self.id,
                    "email": {
                        "doctype": "invoice",
                        "emails": [email],
                        "includeAttachments": "N",
                    },
                }
            try:
                connector.api(method=method, params=params)
            except SellsyError as excp:
                connector.logger.warning(
                    f"Whoops, something went wrong sending the email : {excp}"
                )
        else:
            connector.logger.warning("Tried to send invoice to client without email")

    def validateAndSend(self, email, connector):
        self.validate(connector)
        self.sendByMail(email, connector, None)

    def updateCustomField(self, cfid, value, sellsyConnector):
        sellsyConnector.updateCustomField("document", self.id, cfid, value)

    def addPayMedium(self, payMedium, sellsyConnector):
        syC = sellsyConnector
        self.payMediums.append(payMedium)
        allPayMediums = syC.getPayMediums()
        payMediums = []
        for medium in self.payMediums:
            payMediums.append(allPayMediums[medium])
        params = {
            "docid": self.id,
            "document": {"doctype": self.docType, "payMediums": payMediums},
        }
        sellsyConnector.api(method="Document.update", params=params)

    @classmethod
    def enableStripe(cls, docId, invoiceData, sellsyConnector, logger):
        if "gateways" not in invoiceData:
            invoiceData["gateways"] = []
        invoiceData["gateways"] += ["stripe"]
        invoiceData["docId"] = docId
        cls.generate(docId, invoiceData, sellsyConnector, logger)

    def processSEPARejection(
        self, rejectCode, rejectReason, paymentId, sellsyConnector, invoiceData, logger
    ):
        syC = sellsyConnector
        # For payment rejected before paymentDate, we won't have created the payment in Sellsy yet
        if paymentId is not None:
            self.deletePayment(paymentId, syC)

        self.updateCustomField(
            syC.cfidSlimpayRejectReason, f"{rejectCode} - {rejectReason}", syC
        )

        # Add card payment method for easier recovery process
        # self.addPayMedium("carte bancaire", syC)
        # Enable Stripe
        if invoiceData is not None:
            self.enableStripe(self.id, invoiceData, syC, logger)
        else:
            logger.warning(
                "Cannot enable Stripe because we don't have invoice content in db"
            )
