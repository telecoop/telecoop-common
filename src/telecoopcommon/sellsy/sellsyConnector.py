import json
import os
import time
from datetime import datetime
from decimal import Decimal
from json import JSONDecodeError

import oauthlib.oauth1 as oauth1
import pytz
import requests
import requests_oauthlib

from .sellsyClient import SellsyClient
from .sellsyError import SellsyAuthenticateError, SellsyError, TcSellsyError
from .sellsyMemberOpportunity import SellsyMemberOpportunity
from .sellsyOpportunity import SellsyOpportunity
from .utils import sellsyValues

DEFAULT_URL = "https://apifeed.sellsy.com/0/"


class TcSellsyConnector:
    def __init__(self, conf, logger, emailTemplates=None):
        env = os.getenv("ENV", "LOCAL")
        self.env = "PROD" if env in ["PROD", "LOCAL_PROD"] else "DEV"
        self.conf = conf
        self.logger = logger
        self.values = sellsyValues[self.env]
        self.url = DEFAULT_URL
        self._client = requests_oauthlib.OAuth1Session(
            conf["consumer_token"],
            conf["consumer_secret"],
            conf["user_token"],
            conf["user_secret"],
            signature_method=oauth1.SIGNATURE_PLAINTEXT,
            signature_type=oauth1.SIGNATURE_TYPE_BODY,
        )
        self._connector = None
        self.ownerId = sellsyValues[self.env]["owner_id"]
        self.staff = sellsyValues[self.env]["staff"]
        self.plans = sellsyValues[self.env]["plans"]
        self.plansByRef = {
            v: k
            for k, v in sellsyValues[self.env]["plans"].items()
            if k != "Centrale Photovoltaïque"
        }
        self.paydateId = sellsyValues[self.env]["paydate_id"]
        self.sellsyNewClientMailTemplateId = sellsyValues[self.env][
            "new_client_mail_template_id"
        ]
        customFields = sellsyValues[self.env]["custom_fields"]
        self.cfidPlan = customFields["forfait"]
        self.cfidOnSite = customFields["achatsimphysique"]
        self.cfidOperator = customFields["operateur"]
        self.cfidSIMType = customFields["sim-type"]
        self.cfidRio = customFields["rio"]
        self.cfidNsce = customFields["nsce"]
        self.customFieldBazileNb = customFields["refbazile"]
        self.customFieldTelecomNum = customFields["numerotelecoop"]
        self.cfidMobileDataOutOfPlan = customFields["depassement-forfait-data"]
        self.cfidManuelInvoice = customFields["facturationmanuelle"]
        self.cfidMergeInvoices = customFields["facture-unique"]
        self.cfIdStatusClientMobile = customFields["statut-client-abo-mobile"]
        self.cfIdTeleCommownOffre = customFields["offre-telecommown"]
        self.cfIdTeleCommownOrigine = customFields["telecommown-origine"]
        self.cfIdTeleCommownDateDebut = customFields["telecommown-date-debut"]
        self.cfIdTeleCommownDateFin = customFields["telecommown-date-fin"]
        self.cfIdTeleCommownBoth = customFields["abo-telecommown"]
        self.cfidSponsorCode = customFields["parrainage-code"]
        self.cfidSponsorLink = customFields["parrainage-lien"]
        self.cfidSponsorNbUse = customFields["parrainage-code-nb-use"]
        self.cfidSponsorNbDiscount = customFields["parrainage-nb-discount"]
        self.cfidSponsorRefereeCode = customFields["parrainage-code-parrain"]
        self.cfidSponsorNbCodeDonated = customFields["parrainage-nb-code-donated"]
        self.cfidPromoCode = customFields["code-promo"]
        self.cfidPackDepannage = customFields["pack-depannage"]
        self.cfidPackDepannageUsed = customFields["pack-depannage-used"]
        self.cfidPackInter = customFields["pack-data-roaming-available"]
        self.cfidPackInterUsed = customFields["pack-data-roaming-used"]
        self.cfidSlimpayMandateStatus = customFields["slimpay-mandate-status"]
        self.cfidInvoicingSetting = customFields["choix-facturation"]
        self.cfidProNbSims = customFields["pro-nb-sims"]
        self.cfidProNbPorta = customFields["pro-nb-porta"]
        self.cfidProDateEngagement = customFields["pro-date-engagement"]
        self.cfidProAncienOperateur = customFields["pro-ancien-operateur"]
        self.cfidProEstimConso = customFields["pro-estim-conso"]
        self.cfidProComment = customFields["pro-comment"]
        self.cfidProPrefRappel = customFields["pro-pref-rappel"]
        self.cfidProNomUtilisateur = customFields["pro-nom-utilisateur"]
        self.cfidProMailUtilisateur = customFields["pro-mail-utilisateur"]
        self.cfidProService = customFields["pro-service"]
        self.cfidProPalierSuspension = customFields["pro-palier-suspension"]
        self.cfidProAppelInternationaux = customFields["pro-appels-internationaux"]
        self.cfidProDonneesMobiles = customFields["pro-donnees-mobiles"]
        self.cfidProAchatsContenu = customFields["pro-achats-contenu"]
        self.cfidProAchatsSurtaxes = customFields["pro-achats-surtaxes"]
        self.cfidMembershipRef = customFields["membership-ref"]
        self.cfidMembershipNbShares = customFields["membership-nb-shares"]
        self.cfidMembershipAmount = customFields["membership-amount"]
        self.cfidMembershipPaymentMode = customFields["membership-payment-mode"]
        self.cfidMembershipPaymentLabel = customFields["membership-payment-label"]
        self.cfidMembershipPaymentDate = customFields["membership-payment-date"]
        self.cfidMembershipAcceptedDate = customFields["membership-accepted-date"]
        self.cfidMembershipCategory = customFields["membership-category"]
        self.cfidMembershipFormSentDate = customFields["membership-form-sent-date"]

        self.cfidSlimpayPaymentDate = customFields["slimpay-date-prelevement"]
        self.cfidSlimpayRefundDate = customFields["slimpay-refund-date"]
        self.cfidSlimpayPaymentLink = customFields["slimpay-lien-prelevement"]
        self.cfidSlimpayRejectReason = customFields["slimpay-reject-reason"]
        self.cfidSlimpayPaymentStatus = customFields["slimpay-payment-status"]

        self.opportunitySourceInterne = sellsyValues[self.env][
            "opportunity_source_interne"
        ]
        self.opportunitySourceSiteWeb = sellsyValues[self.env][
            "opportunity_source_site_web"
        ]
        self.opportunitySourceEspaceClient = sellsyValues[self.env][
            "opportunity_source_espace_client"
        ]
        self.opportunitySourceTelMail = sellsyValues[self.env][
            "opportunity_source_tel_mail"
        ]

        self.funnelIdVdc = sellsyValues[self.env]["funnel_id_vie_du_contrat"]
        self.stepNew = sellsyValues[self.env]["step_new"]
        self.stepReminder = sellsyValues[self.env]["step_reminder"]
        self.stepSimToSend = sellsyValues[self.env]["step_sim_to_send"]
        self.stepSimToSendTransition = sellsyValues[self.env][
            "step_sim_to_send_transition"
        ]
        self.stepSimSent = sellsyValues[self.env]["step_sim_sent"]
        self.stepSimHandDelivered = sellsyValues[self.env]["step_sim_hand_delivered"]
        self.stepSimReceived = sellsyValues[self.env]["step_sim_received"]
        self.stepSimPendingPorta = sellsyValues[self.env]["step_sim_pending_porta"]
        self.stepSimPendingNew = sellsyValues[self.env]["step_sim_pending_new"]
        self.stepSimActivated = sellsyValues[self.env]["step_sim_activated"]
        self.stepSimSuspended = sellsyValues[self.env]["step_sim_suspended"]
        self.stepSimTerminated = sellsyValues[self.env]["step_sim_terminated"]

        self.funnelIdMembership = sellsyValues[self.env]["funnel_id_membership"]
        self.stepMembershipAsked = sellsyValues[self.env]["step_membership_asked"]
        self.stepMembershipSign = sellsyValues[self.env]["step_membership_sign"]
        self.stepMembershipRemainder = sellsyValues[self.env][
            "step_membership_reminder"
        ]
        self.stepMembershipSigned = sellsyValues[self.env]["step_membership_signed"]
        self.stepMembershipPaid = sellsyValues[self.env]["step_membership_paid"]
        self.stepMembershipActive = sellsyValues[self.env]["step_membership_active"]

        self.funnelIdMembership2 = sellsyValues[self.env]["funnel_id_membership2"]
        self.stepMembership2Created = sellsyValues[self.env]["step_membership2_created"]
        self.stepMembership2Sign = sellsyValues[self.env]["step_membership2_sign"]
        self.stepMembership2Remainder = sellsyValues[self.env][
            "step_membership2_reminder"
        ]
        self.stepMembership2Payment = sellsyValues[self.env]["step_membership2_payment"]
        self.stepMembership2Verified = sellsyValues[self.env][
            "step_membership2_verified"
        ]
        self.stepMembership2Validated = sellsyValues[self.env][
            "step_membership2_validated"
        ]
        self.stepMembership2Refused = sellsyValues[self.env]["step_membership2_refused"]

        self.funnelIdDevPro = sellsyValues[self.env]["funnel_id_dev_pro"]
        self.stepProNew = sellsyValues[self.env]["step_pro_new"]
        self.stepProContacted = sellsyValues[self.env]["step_pro_contacted"]
        self.stepProAptPlanned = sellsyValues[self.env]["step_pro_apt_planned"]
        self.stepProMissingInfo = sellsyValues[self.env]["step_pro_missing_info"]
        self.stepProAwaiting = sellsyValues[self.env]["step_pro_awaiting"]
        self.stepProPropTodo = sellsyValues[self.env]["step_pro_prop_todo"]
        self.stepProPropInternalValidation = sellsyValues[self.env][
            "step_pro_prop_internal_validation"
        ]
        self.stepProPropAwaiting = sellsyValues[self.env]["step_pro_prop_awaiting"]
        self.stepProPropAccepted = sellsyValues[self.env]["step_pro_prop_accepted"]
        self.stepProAccountComplete = sellsyValues[self.env][
            "step_pro_account_complete"
        ]
        self.stepProEnd = sellsyValues[self.env]["step_pro_end"]
        self.stepProNewSims = sellsyValues[self.env]["step_pro_new_sims"]

        self.funnelIdSimsPro = sellsyValues[self.env]["funnel_id_sims_pro"]
        self.stepProSimsInactive = sellsyValues[self.env]["step_pro_sims_inactive"]
        self.stepProSimsAwaiting = sellsyValues[self.env]["step_pro_sims_awaiting"]
        self.stepProSimActivating = sellsyValues[self.env]["step_pro_sims_activating"]
        self.stepProSimsActivated = sellsyValues[self.env]["step_pro_sims_activated"]
        self.stepProSimsSuspended = sellsyValues[self.env]["step_pro_sims_suspended"]
        self.stepProSimsTerminated = sellsyValues[self.env]["step_pro_sims_terminated"]

        self.funnelIdOperatorChange = sellsyValues[self.env][
            "funnel_id_operator_change"
        ]
        self.stepEsimOperatorChange = sellsyValues[self.env][
            "step_esim_operator_change"
        ]
        self.stepEsimNewClient = sellsyValues[self.env][
            "step_esim_new_client_esim_vowifi"
        ]
        self.stepEsimVowifiRequest = sellsyValues[self.env]["step_esim_vowifi_request"]
        self.stepEsimEsimRequest = sellsyValues[self.env]["step_esim_esim_request"]
        self.stepEsimSimSent = sellsyValues[self.env][
            "step_esim_vowifi_request_sim_sent"
        ]
        self.stepEsimPending = sellsyValues[self.env]["step_esim_pending"]
        self.stepEsimActivated = sellsyValues[self.env]["step_esim_activated"]

        self.services = None
        self.itemIds = None
        self.modelIds = None
        self.taxId = None
        self.payMediums = None
        self.rateCategories = None

        self.funnelIdSim = [
            self.funnelIdVdc,
            self.funnelIdSimsPro,
            self.funnelIdOperatorChange,
        ]

        self.funnelIdPlanChange = sellsyValues[self.env]["funnel_id_plan_change"]
        self.stepPlanChangeReceivedTran = sellsyValues[self.env][
            "step_plan_change_received_tran"
        ]
        self.stepPlanChangeReceivedSobr = sellsyValues[self.env][
            "step_plan_change_received_sobr"
        ]
        self.stepPlanChangeReceivedPro = sellsyValues[self.env][
            "step_plan_change_received_pro"
        ]
        self.stepPlanChangeCondAccepted = sellsyValues[self.env][
            "step_plan_change_cond_accepted"
        ]
        self.stepPlanChangeInProgress = sellsyValues[self.env][
            "step_plan_change_in_progress"
        ]
        self.stepPlanChangeActive = sellsyValues[self.env]["step_plan_change_active"]

        self.emailTemplates = sellsyValues[self.env]["emailTemplates"]
        # if specific config is given, update default ones
        if emailTemplates is not None:
            # we could use .update() but we want to be sure given keys exists
            for key, value in dict(emailTemplates).items():
                # update only if key is known
                if key in self.emailTemplates:
                    self.emailTemplates[key] = value
                else:
                    self.logger.warning(
                        f"unknown email template was spcified in conf file ({key})"
                    )

    def _api(self, method="Infos.getInfos", params={}) -> dict:
        headers = {"content-type": "application/json", "cache-control": "no-cache"}
        payload = {"method": method, "params": params}

        response = self._client.post(
            self.url,
            data={"request": 1, "io_mode": "json", "do_in": json.dumps(payload)},
            headers=headers,
        )

        # Handle OAuth error (401 status code returned)
        if response.status_code == 401:
            raise SellsyAuthenticateError(response.text)

        # Error handler
        response_json = response.json()
        if response_json["status"] == "error":
            error_code, error_message = (
                response_json["error"]["code"],
                response_json["error"]["message"],
            )
            raise SellsyError(error_code, error_message)

        return response_json["response"]

    def api(self, method: str, params={}) -> dict:
        self.logger.debug(f"Calling Sellsy {method} with params {params}")
        result = {}
        MAX_RETRIES = 10  # Max 8 minutes
        retry = MAX_RETRIES
        try:
            while retry >= 0:
                if retry < MAX_RETRIES:
                    self.logger.info(f"Retrying for the {MAX_RETRIES - retry}th time")
                try:
                    result = self._api(method, params)
                    retry = -1
                except (requests.JSONDecodeError, JSONDecodeError, TypeError) as e:
                    if retry < 1:
                        self.logger.warning(e)
                        raise e
                    retry -= 1
                    time.sleep(pow(2, MAX_RETRIES - retry))
                except SellsyError as e:
                    if e.sellsy_code_error == "E_OBJ_NOT_LOADABLE":
                        if retry < 1:
                            self.logger.warning(e)
                            raise e
                        retry -= 1
                        time.sleep(pow(2, MAX_RETRIES - retry))
                    else:
                        raise e
        except (
            SellsyAuthenticateError
        ) as excp:  # raised if credential keys are not valid
            self.logger.warning(f"Authentication failed ! Details : {excp}")
            raise excp
        except SellsyError as excp:  # raised if an error is returned by Sellsy API
            self.logger.warning(excp)
            raise excp
        # Sellsy API is throttled at 5 requests per second, we take a margin of 0.25s
        time.sleep(0.25)
        return result

    def updateClientProperty(self, clientId: int, property: str, value):
        client = self.getClient(clientId)
        params = {
            "clientid": clientId,
            "third": {
                "name": client.label,
            },
        }
        response = None
        if property in ["mobile", "email"]:
            if client.type == "person":
                params = {
                    "clientid": clientId,
                    "third": {"name": client.name, property: value},
                    "contact": {
                        "name": client.name,
                        "forename": client.firstname,
                        property: value,
                    },
                }
                response = self.api(method="Client.update", params=params)
            else:
                params = {
                    "clientid": clientId,
                    "contactid": client.mainContactId,
                    "contact": {"name": client.name, property: value},
                }
                response = self.api(method="Client.updateContact", params=params)

        return response

    def updateCustomField(self, entity: str, entityId: int, cfid: int, value):
        knownEntities = ["client", "opportunity", "document"]
        if entity not in knownEntities:
            raise ValueError(f"Unknown entity {entity}, should be in {knownEntities}")
        params = {
            "linkedtype": entity,
            "linkedid": entityId,
            "values": [
                {"cfid": cfid, "value": str(value) if value == 0 else value},
            ],
        }
        return self.api(method="CustomFields.recordValues", params=params)

    def createTask(self, data: dict) -> int:
        """Wrapper to create a task in Sellsy with pre-defined owners"""

        self.logger.info(
            f"Creating task in Sellsy ({data['eventType']} #{data['eventId']})"
        )

        result = self.api(method="Agenda.getAvailableLabels")
        labelId = None
        for lId, label in result.items():
            if "value" in label and label["value"] == "Rappel":
                labelId = lId
                break

        description = data["description"]

        params = {
            "type": "task",
            "task": {
                "description": description,
                "label": labelId,
                "allDay": "N",
                "start": round(datetime.today().timestamp()),
                "end": round(datetime.today().timestamp()),
                "isPrivate": "N",
                "canEdit": "Y",
                "staffids": [
                    self.staff["support-client"],
                    self.staff["support-societaire"],
                ],
                "staffs": [
                    {"id": self.staff["support-client"], "canEdit": "Y"},
                    # {"id": self.staff["support-client-2"], "canEdit": "Y"},
                    {"id": self.staff["support-client-3"], "canEdit": "Y"},
                    {"id": self.staff["support-client-4"], "canEdit": "Y"},
                ],
            },
        }
        if data["eventType"] == "facture":
            params["task"]["relatedtype"] = "invoice"
            params["task"]["relatedid"] = data["eventId"]
        elif data["eventType"] == "creditnote":
            params["task"]["relatedtype"] = "creditnote"
            params["task"]["relatedid"] = data["eventId"]
        elif data["eventType"] in ["acompte", "avoir", "line-out"]:
            params["task"]["relatedtype"] = "third"
            params["task"]["relatedid"] = data["sellsyId"]
        self.logger.debug(params)

        result = self.api(method="Agenda.create", params=params)
        self.logger.debug(result)
        return result["taskid"]

    def getClientRef(self, clientId: int) -> str:
        response = self.api(method="Client.getOne", params={"clientid": clientId})
        return response["ident"]

    def getTeleCommownOptinDate(self, clientId=None, opportunityId=None):
        if clientId is None and opportunityId is None:
            raise ValueError("Either clientId or opportunityId should be not None")
        response = None
        if clientId is not None:
            response = self.api(method="Client.getOne", params={"clientid": clientId})
        if opportunityId is not None:
            response = self.api(
                method="opportunities.getOne", params={"id": opportunityId}
            )

        if response is None:
            raise TcSellsyError(
                f"Could not get client or opportunity with given ids. Client={clientId}, Opp={opportunityId}"
            )

        optinDate = None
        for ln in response["customFields"]:
            if ln["name"] == "Z-Offre TeleCommown":
                fields = (
                    ln["list"] if isinstance(ln["list"], list) else ln["list"].values()
                )
                for f in fields:
                    if (
                        f["code"] == "offre-telecommown"
                        and "formatted_ymd" in f
                        and f["formatted_ymd"] != ""
                    ):
                        optinDate = pytz.timezone("Europe/Paris").localize(
                            datetime.strptime(f["formatted_ymd"], "%Y-%m-%d")
                        )
                        break
                break
        return optinDate

    def getClient(self, id: int):
        c = SellsyClient(id)
        c.loadWithValues(self.getClientValues(id))
        return c

    def getClientValues(self, id: int):
        cli = self.api(method="Client.getOne", params={"clientid": id})

        mainContactId = cli["client"]["maincontactid"]

        result = {
            "ident": cli["client"]["ident"],
            "type": cli["client"]["type"],
            "joindate": cli["client"]["joindate"],
            "dateTransformProspect": cli["client"]["transformationDate"],
            "people_name": "",
            "people_forename": "",
            "email": "",
            "mobile": "",
            "maincontactid": mainContactId,
            "addr_part1": "",
            "addr_zip": "",
            "addr_town": "",
            "addr_countrycode": "",
            "contacts": {},
            "smartTags": cli["tags"],
        }
        customFields = {
            "refbazile": {"code": "refbazile", "textval": ""},
            "facturationmanuelle": {
                "code": "facturationmanuelle",
                "formatted_value": "",
            },
            "facture-unique": {"code": "facture-unique", "formatted_value": ""},
            "statut-client-abo-mobile": {
                "code": "statut-client-abo-mobile",
                "textval": "",
            },
            "parrainage-code": {"code": "parrainage-code", "textval": ""},
            "parrainage-lien": {"code": "parrainage-lien", "textval": ""},
            "parrainage-code-nb-use": {
                "code": "parrainage-code-nb-use",
                "defaultValue": "0",
            },
            "parrainage-nb-discount": {
                "code": "parrainage-nb-discount",
                "defaultValue": "0",
            },
            "parrainage-code-parrain": {
                "code": "parrainage-code-parrain",
                "textval": "",
            },
            "parrainage-nb-code-donated": {
                "code": "parrainage-nb-code-donated",
                "defaultValue": "0",
            },
            "offre-telecommown": {"code": "offre-telecommown", "timestampval": ""},
            "telecommown-date-debut": {
                "code": "telecommown-date-debut",
                "timestampval": "",
            },
            "telecommown-date-fin": {
                "code": "telecommown-date-fin",
                "timestampval": "",
            },
            "telecommown-origine": {
                "code": "telecommown-origine",
                "formatted_value": "",
            },
            "abo-telecommown": {"code": "abo-telecommown", "defaultValue": ""},
            "code-promo": {"code": "code-promo", "textval": ""},
            "slimpay-mandate-status": {"code": "slimpay-mandate-status", "textval": ""},
            "societaire": {"code": "societaire", "textval": ""},
            "categorie-societaire": {
                "code": "categorie-societaire",
                "formatted_value": "",
            },
            "typetelephone": {"code": "typetelephone", "textval": ""},
            "consomoyenneclient": {"code": "consomoyenneclient", "defaultValue": "0"},
            "smsmoyen": {"code": "smsmoyen", "defaultValue": "0"},
            "hrappel": {"code": "hrappel", "defaultValue": "0"},
            "neufreconditionne": {"code": "neufreconditionne", "formatted_value": ""},
            "achattelephone": {"code": "achattelephone", "defaultValue": "0"},
            "lieunaissance": {"code": "lieunaissance", "textval": ""},
            "datenaissance": {"code": "datenaissance", "formatted_ymd": ""},
            "paiementfavori": {"code": "paiementfavori", "formatted_value": ""},
        }
        # Name + person data
        if cli["client"]["type"] == "person":
            contact = (
                cli["contact"] if "contact" in cli else cli["contacts"][mainContactId]
            )
            civility = "M" if contact["civil"] == "man" else "Mme"
            result["name"] = f"{civility} {contact['name']} {contact['forename']}"
            result["email"] = contact["email"]
            result["mobile"] = contact["mobile"]
            result["people_name"] = contact["name"]
            result["people_forename"] = contact["forename"]
        elif cli["client"]["type"] == "corporation":
            corporation = cli["corporation"]
            result["name"] = corporation["name"]
            result["email"] = corporation["email"]
            result["mobile"] = corporation["mobile"]
        # Contacts
        if "contacts" in cli and mainContactId in cli["contacts"]:
            result["contacts"][mainContactId] = cli["contacts"][mainContactId]
            for contactId, contact in cli["contacts"].items():
                if contact["isBillingContact"]:
                    result["contacts"][contactId] = contact
        elif "contact" in cli:
            result["contacts"][mainContactId] = cli["contact"]
        for addr in cli["address"]:
            if addr["name"] == "Address principale":
                result["addr_part1"] = addr["part"]
                result["addr_zip"] = addr["zip"]
                result["addr_town"] = addr["town"]
                result["addr_countrycode"] = addr["countrycode"]
        # Custom fields
        for ln in cli["customFields"]:
            fields = ln["list"].values() if isinstance(ln["list"], dict) else ln["list"]
            for f in fields:
                if "code" in f:
                    code = f["code"]
                    textFields = [
                        "refbazile",
                        "parrainage-code",
                        "parrainage-lien",
                        "societaire",
                        "typetelephone",
                        "parrainage-code-parrain",
                        "code-promo",
                        "slimpay-mandate-status",
                        "lieunaissance",
                    ]
                    selectFields = [
                        "facturationmanuelle",
                        "statut-client-abo-mobile",
                        "telecommown-origine",
                        "neufreconditionne",
                        "categorie-societaire",
                        "paiementfavori",
                    ]
                    dateFields = [
                        "offre-telecommown",
                        "telecommown-date-debut",
                        "telecommown-date-fin",
                        "datenaissance",
                    ]
                    intFields = [
                        "parrainage-nb-discount",
                        "parrainage-code-nb-use",
                        "parrainage-nb-code-donated",
                        "consomoyenneclient",
                        "smsmoyen",
                        "hrappel",
                        "achattelephone",
                    ]
                    if code in textFields:
                        customFields[code]["textval"] = f["defaultValue"]
                    elif code in selectFields and "formatted_value" in f:
                        customFields[code]["formatted_value"] = f["formatted_value"]
                    elif code in ["facture-unique", "abo-telecommown"]:
                        customFields[code]["boolval"] = f["defaultValue"] == "Y"
                    elif code in intFields:
                        try:
                            customFields[code]["numericval"] = int(f["defaultValue"])
                        except ValueError:
                            customFields[code]["numericval"] = 0
                    elif code in dateFields and "formatted_ymd" in f:
                        customFields[code]["formatted_ymd"] = f["formatted_ymd"]
        result["customfields"] = customFields.values()

        return result

    def getClientFromRef(self, ref):
        params = {"search": {"ident": ref}}
        clients = self.api(method="Client.getList", params=params)
        client = None
        if clients["result"]:
            for clientId, cli in clients["result"].items():
                if cli["ident"] == "CLI00001001":
                    # Référence ayant servie de test lors de la mise en prod du parcours souscription
                    continue
                if cli["ident"] == ref:
                    client = SellsyClient(clientId)
                    client.loadWithValues(cli)
                    break

        return client

    def getClientFromEmail(self, email):
        params = {"search": {"email": email}}
        clients = self.api(method="Client.getList", params=params)
        client = None
        if clients["result"]:
            for clientId, cli in clients["result"].items():
                if cli["ident"] == "CLI00001001":
                    # Référence ayant servie de test lors de la mise en prod du parcours souscription
                    continue
                if cli["email"] == email:
                    client = SellsyClient(clientId)
                    client.loadWithValues(cli)
                    break

        return client

    def getClients(self, includeMembers=False, includeNoRef=False, searchParams=None):
        result = {}
        params = {"pagination": {"nbperpage": 1000, "pagenum": 1}}
        if searchParams:
            params["search"] = searchParams
        clients = self.api(method="Client.getList", params=params)
        infos = clients["infos"]
        nbPages = infos["nbpages"]
        currentPage = 1
        while currentPage <= nbPages:
            self.logger.debug(f"Processing page {currentPage}/{nbPages}")
            for clientId, client in clients["result"].items():
                if client["ident"] == "CLI00001001":
                    # Référence ayant servie de test lors de la mise en prod du parcours souscription
                    continue

                # Fetching billing contact if needed
                if "contacts" in client and len(client["contacts"]) > 1:
                    billingContact = self.api(
                        method="Client.getBillingContact", params={"clientid": clientId}
                    )
                    if billingContact:
                        client["contacts"][billingContact["id"]] = billingContact
                cli = SellsyClient(clientId)
                cli.loadWithValues(client)
                if (
                    (client["ident"] is not None or includeNoRef)
                    and client["ident"] not in ["", "-1"]
                ) or (cli.member and includeMembers):
                    result[clientId] = cli
                else:
                    if cli.status != "Non abonné":
                        self.logger.warning(f"Client #{clientId} has no reference")

            currentPage += 1
            if infos["pagenum"] <= nbPages:
                params["pagination"]["pagenum"] = currentPage
                clients = self.api(method="Client.getList", params=params)
                infos = clients["infos"]

        return result

    def getOpportunity(self, id):
        o = SellsyOpportunity(id)
        o.loadWithValues(self.getOpportunityValues)
        return o

    @classmethod
    def getSourceIdFromValue(cls, source):
        env = os.getenv("ENV", "LOCAL")
        env = "PROD" if env in ["PROD", "LOCAL_PROD"] else "DEV"
        sourceId = None
        if source == "Site web":
            sourceId = sellsyValues[env]["opportunity_source_site_web"]
        if source == "Interne":
            sourceId = sellsyValues[env]["opportunity_source_interne"]
        if source == "Tel/Mail":
            sourceId = sellsyValues[env]["opportunity_source_tel_mail"]
        if source == "Espace client":
            sourceId = sellsyValues[env]["opportunity_source_espace_client"]
        if source == "Lita":
            sourceId = sellsyValues[env]["opportunity_source_lita"]
        if source == "Registre Excel":
            sourceId = sellsyValues[env]["opportunity_source_registre_excel"]

        return sourceId

    def getOpportunityValues(self, id):
        opp = self.api(method="Opportunities.getOne", params={"id": id})
        result = {
            "ident": opp["ident"],
            "name": opp["name"],
            "relationType": opp["relationType"],
            "linkedid": opp["linkedid"],
            "funnelid": opp["funnelid"],
            "sourceid": opp["source"],
            "created": opp["created"],
            "statusLabel": opp["statusLabel"],
            "stepEnterDate": opp["stepEnterDate"],
            "stepid": opp["stepid"],
            "smarttags": (
                ",".join([o["word"] for o in opp["tags"].values()])
                if isinstance(opp["tags"], dict)
                else ""
            ),
            "customfields": {
                "nsce": {"code": "nsce", "textval": ""},
                "numerotelecoop": {"code": "numerotelecoop", "textval": ""},
                "rio": {"code": "rio", "textval": ""},
                "operateur": {"code": "operateur", "formatted_value": ""},
                "sim-type": {"code": "sim-type", "formatted_value": ""},
                "refbazile": {"code": "refbazile", "textval": ""},
                "forfait": {"code": "forfait", "textval": ""},
                "depassement-forfait-data": {
                    "code": "depassement-forfait-data",
                    "formatted_value": "",
                },
                "achatsimphysique": {"code": "achatsimphysique", "boolval": False},
                "date-activation-sim-souhaitee": {
                    "code": "date-activation-sim-souhaitee",
                    "timestampval": 0,
                },
                "offre-telecommown": {"code": "offre-telecommown", "timestampval": 0},
                "parrainage-code-parrain": {
                    "code": "parrainage-code-parrain",
                    "textval": "",
                },
                "telecommown-date-debut": {
                    "code": "telecommown-date-debut",
                    "timestampval": 0,
                },
                "telecommown-date-fin": {
                    "code": "telecommown-date-fin",
                    "timestampval": 0,
                },
                "telecommown-origine": {
                    "code": "telecommown-origine",
                    "formatted_value": "",
                },
                "abo-telecommown": {"code": "abo-telecommown", "boolval": False},
                "code-promo": {"code": "code-promo", "textval": ""},
                "pack-depannage": {
                    "code": "pack-depannage",
                    "defaultValue": "0",
                    "numericval": 0,
                },
                "pack-depannage-utilises": {
                    "code": "pack-depannage-utilises",
                    "defaultValue": "0",
                    "numericval": 0,
                },
                "pro-nb-sims": {
                    "code": "pro-nb-sims",
                    "defaultValue": "0",
                    "numericval": 0,
                },
                "pro-nb-porta": {
                    "code": "pro-nb-porta",
                    "defaultValue": "0",
                    "numericval": 0,
                },
                "pro-date-engagement": {
                    "code": "pro-date-engagement",
                    "timestampval": 0,
                },
                "pro-ancien-operateur": {"code": "pro-ancien-operateur", "textval": ""},
                "pro-estim-conso": {"code": "pro-estim-conso", "textval": ""},
                "pro-comment": {"code": "pro-comment", "textval": ""},
                "pro-pref-rappel": {"code": "pro-pref-rappel", "textval": ""},
                "pro-nom-utilisateur": {"code": "pro-nom-utilisateur", "textval": ""},
                "pro-mail-utilisateur": {"code": "pro-mail-utilisateur", "textval": ""},
                "pro-palier-suspension": {
                    "code": "pro-palier-suspension",
                    "formatted_value": "",
                },
                "pro-appels-internationaux": {
                    "code": "pro-appels-internationaux",
                    "formatted_value": "",
                },
                "pro-donnees-mobiles": {
                    "code": "pro-donnees-mobiles",
                    "formatted_value": "",
                },
                "pro-achats-contenu": {"code": "pro-achats-contenu", "boolval": True},
                "pro-achats-surtaxes": {"code": "pro-achats-surtaxes", "boolval": True},
            },
        }

        for ln in opp["customFields"]:
            fields = ln["list"].values() if isinstance(ln["list"], dict) else ln["list"]
            for field in fields:
                if "code" in field:
                    code = field["code"]
                    textFields = [
                        "rio",
                        "nsce",
                        "numerotelecoop",
                        "refbazile",
                        "code-promo",
                        "parrainage-code-parrain",
                        "pro-estim-conso",
                        "pro-comment",
                        "pro-nom-utilisateur",
                        "pro-mail-utilisateur",
                        "pro-ancien-operateur",
                    ]
                    listFields = [
                        "telecommown-origine",
                        "forfait",
                        "depassement-forfait-data",
                        "pro-palier-suspension",
                        "pro-appels-internationaux",
                        "pro-donnees-mobiles",
                        "operateur",
                        "sim-type",
                    ]
                    dateFields = [
                        "date-activation-sim-souhaitee",
                        "offre-telecommown",
                        "telecommown-date-debut",
                        "telecommown-date-fin",
                        "pro-date-engagement",
                    ]
                    if code in textFields:
                        result["customfields"][code]["textval"] = field["defaultValue"]
                    if code in listFields and "formatted_value" in field:
                        result["customfields"][code]["formatted_value"] = field[
                            "formatted_value"
                        ]
                    if code in [
                        "achatsimphysique",
                        "abo-telecommown",
                        "pro-achats-contenu",
                        "pro-achats-surtaxes",
                    ]:
                        result["customfields"][code]["boolval"] = (
                            field["defaultValue"] == "Y"
                        )
                    if code in dateFields and "formatted_ymd" in field:
                        result["customfields"][code]["formatted_ymd"] = field[
                            "formatted_ymd"
                        ]
                    if code in [
                        "pack-depannage",
                        "pack-depannage-utilises",
                        "pro-nb-sims",
                        "pro-nb-porta",
                    ]:
                        try:
                            result["customfields"][code]["numericval"] = int(
                                field["defaultValue"]
                            )
                        except ValueError:
                            result["customfields"][code]["numericval"] = 0

        return result

    def getMembershipOpportunityValues(self, id: int):
        opp = self.api(method="Opportunities.getOne", params={"id": id})
        result = {
            "ident": opp["ident"],
            "name": opp["name"],
            "relationType": opp["relationType"],
            "linkedid": opp["linkedid"],
            "funnelid": opp["funnelid"],
            "sourceid": opp["source"],
            "created": opp["created"],
            "statusLabel": opp["statusLabel"],
            "stepEnterDate": opp["stepEnterDate"],
            "stepid": opp["stepid"],
            "customfields": {
                "partssocialessouhaite": {
                    "code": "partssocialessouhaite",
                    "defaultValue": "",
                },
                "montantparts": {"code": "montantparts", "defaultValue": ""},
                "dateversementsocietariat": {
                    "code": "dateversementsocietariat",
                    "timestampval": 0,
                },
                "dateacceptationsocietariat": {
                    "code": "dateacceptationsocietariat",
                    "timestampval": 0,
                },
                "moyen-de-paiement": {"code": "moyen-de-paiement", "textval": ""},
                "reference-paiement": {"code": "reference-paiement", "textval": ""},
                "dateattestationenvoyee": {
                    "code": "dateattestationenvoyee",
                    "timestampval": 0,
                },
            },
        }

        for ln in opp["customFields"]:
            fields = ln["list"].values() if isinstance(ln["list"], dict) else ln["list"]
            for field in fields:
                if "code" in field:
                    code = field["code"]
                    if (
                        code
                        in [
                            "dateversementsocietariat",
                            "dateacceptationsocietariat",
                            "dateattestationenvoyee",
                        ]
                        and "formatted_ymd" in field
                    ):
                        result["customfields"][code]["formatted_ymd"] = field[
                            "formatted_ymd"
                        ]
                    if code in ["partssocialessouhaite", "montantparts"]:
                        result["customfields"][code]["numericval"] = int(
                            field["defaultValue"]
                        )
                    if code == "moyen-de-paiement":
                        result["customfields"][code]["moyen-de-paiement"] = field[
                            "defaultValue"
                        ]
                    if code == "reference-paiement":
                        result["customfields"][code]["reference-paiement"] = field[
                            "defaultValue"
                        ]

        return result

    def getOpportunities(self, funnelId=None):
        if funnelId is None:
            funnelId = self.funnelIdVdc
        return self.getOpportunitiesInStep(funnelId=funnelId, stepId="all")

    def getOpportunitiesInStep(
        self, funnelId, stepId, limit=None, startDate=None, searchParams=None
    ):
        result = []
        params = {
            "pagination": {"nbperpage": 1000, "pagenum": 1},
            "search": {"funnelid": funnelId},
        }
        if stepId != "all":
            params["search"]["stepid"] = stepId
        if startDate is not None:
            params["search"]["periodecreated_start"] = startDate.timestamp()
        if searchParams is not None:
            for k, v in searchParams.items():
                params["search"][k] = v

        opportunities = self.api(method="Opportunities.getList", params=params)
        infos = opportunities["infos"]
        nbPages = infos["nbpages"]
        currentPage = 1
        while currentPage <= nbPages:
            self.logger.debug(f"Processing page {currentPage}/{nbPages}")
            for id, opp in opportunities["result"].items():
                if funnelId in [self.funnelIdMembership, self.funnelIdMembership2]:
                    o = SellsyMemberOpportunity(id)
                else:
                    o = SellsyOpportunity(id)
                o.loadWithValues(opp)
                result.append(o)
                if limit is not None and limit <= len(result):
                    return result

            currentPage += 1
            if infos["pagenum"] <= nbPages:
                params["pagination"]["pagenum"] = currentPage
                opportunities = self.api(method="Opportunities.getList", params=params)
                infos = opportunities["infos"]

        return result

    def getClientOpportunities(self, clientId):
        result = []
        params = {
            "search": {
                "thirds": [
                    clientId,
                ]
            },
            "pagination": {"nbperpage": 1000},
        }
        opportunities = self.api(method="Opportunities.getList", params=params)
        if len(opportunities["result"]) == 0:
            return result
        for opportunity in opportunities["result"].values():
            if opportunity["funnelid"] == str(self.funnelIdMembership):
                opp = SellsyMemberOpportunity(opportunity["id"])
            else:
                opp = SellsyOpportunity(opportunity["id"])
            opp.loadWithValues(opportunity)
            result.append(opp)
        return result

    def getOpportunityFromClientAndMsisdn(self, clientId, msisdn):
        opportunities = self.getClientOpportunities(clientId)
        for opp in opportunities:
            if opp.msisdn == msisdn:
                return opp
        raise LookupError(
            f"Could not opportunity with msisdn {msisdn} for client #{clientId}"
        )

    def getServices(self):
        if self.services is None:
            params = {
                "type": "service",
                "pagination": {
                    "nbperpage": 500,
                },
            }
            response = self.api(method="Catalogue.getList", params=params)
            services = response["result"]
            params["type"] = "item"
            response = self.api(method="Catalogue.getList", params=params)
            services |= response["result"]
            data = {}
            for _id, service in services.items():
                if "name" in service:
                    data[service["name"]] = {
                        "id": service["id"],
                        "unitAmount": service["unitAmountTaxesInc"],
                        "taxId": service["taxid"],
                        "notes": service["notes"],
                        "tradename": service["tradename"],
                        "type": service["type"],
                        "quantity": service["qt"],
                    }
            self.services = data

        return self.services

    def getItemIds(self):
        if self.itemIds is None:
            units = self.api(method="AccountDatas.getUnits", params={})
            data = {}
            for unitId, unit in units.items():
                if "value" in unit:
                    data[unit["value"]] = unitId
            self.itemIds = data

        return self.itemIds

    def getModelIds(self):
        if self.modelIds is None:
            params = {
                "doctype": "model",
                "pagination": {
                    "nbperpage": 100,
                },
            }
            models = self.api(method="Document.getList", params=params)
            data = {}
            for modelId, model in models["result"].items():
                if "ident" in model:
                    data[model["ident"]] = modelId
            self.modelIds = data

        return self.modelIds

    def getTaxId(self, taxRateString):
        if self.taxId is None:
            taxes = self.api(method="AccountDatas.getTaxes")
            for taxId, tax in taxes.items():
                if "value" in tax and tax["value"] == taxRateString:
                    self.taxId = taxId
                    break

        return self.taxId

    def getPayMediums(self):
        if self.payMediums is None:
            result = {}
            mediums = self.api(method="AccountDatas.getPayMediums")
            for id, medium in mediums.items():
                if "value" in medium and medium["value"] in [
                    "prélèvement",
                    "carte bancaire",
                    "virement bancaire",
                ]:
                    result[medium["value"]] = id
            self.payMediums = result

        return self.payMediums

    def getRateCategories(self):
        if self.rateCategories is None:
            categories = self.api(method="AccountDatas.getRateCategories")
            data = {}
            for id, category in categories.items():
                if "name" in category:
                    data[category["name"]] = id
            self.rateCategories = data

        return self.rateCategories

    def getSellsyClientInfo(self, clientRef):
        params = {"search": {"ident": clientRef}}
        result = self.api(method="Client.getList", params=params)
        for id, client in result["result"].items():
            if "ident" in client:
                # Email par défaut
                email = client["email"]
                # recherche du contact principal
                mainContactId = client["maincontactid"]
                for contactId, contact in client["contacts"].items():
                    if contactId == mainContactId:
                        email = contact["email"]
                return [id, email]

    def getInvoiceValues(self, id, docType="invoice"):
        try:
            invoice = self.api(
                method="Document.getOne", params={"doctype": docType, "docid": id}
            )
        except SellsyError:
            docType = "creditnote"
            invoice = self.api(
                method="Document.getOne", params={"doctype": docType, "docid": id}
            )
        result = {
            "docType": docType,
            "ident": invoice["ident"],
            "status": invoice["status"],
            "step_id": invoice["step"],
            "totalAmountTaxesFree": invoice["totalAmountTaxesFree"],
            "taxesAmountSum": invoice["taxesAmountSum"],
            "totalAmount": invoice["totalAmount"],
            "dueAmount": invoice["dueAmount"],
            "payDateCustom": datetime.strptime(
                invoice["paydate_custom"], "%d/%m/%Y"
            ).strftime("%Y-%m-%d"),
            "thirdident": invoice["thirdident"],
            "thirdid": invoice["thirdid"],
            "subject": invoice["subject"],
            "created": invoice["created"],
            "payMediumsText": invoice["paymediums_text"],
            "rows": [],
        }
        for row in invoice["map"]["rows"].values():
            if not isinstance(row, dict):
                # Sellsy sends rubbish like '_xml_childtag': 'row' in the json response …
                continue
            qt = Decimal(row["qt"])
            amount = Decimal(row["totalAmountTaxesInc"])
            if qt != 0 and amount != 0:
                result["rows"].append(
                    {
                        "item": row["type"],
                        "ref": row["name"],
                        "label": row["notes"],
                        "unitAmount": Decimal(row["unitAmountTaxesInc"]),
                        "quantity": qt,
                        "amount": amount,
                        "taxes": Decimal(row["taxAmount"]),
                        "amountTaxFree": Decimal(row["totalAmount"]),
                    }
                )

        return result

    def updateInvoiceStatus(self, invoiceId, status, docType="invoice"):
        params = {
            "docid": invoiceId,
            "document": {"doctype": docType, "step": status},
        }
        self.api(method="Document.updateStep", params=params)

    def updateInvoicePaymentDate(self, invoiceId, nbDays, docType="invoice"):
        params = {
            "docid": invoiceId,
            "document": {
                "doctype": docType,
            },
            "paydate": {"id": self.paydateId, "xdays": nbDays},
        }
        self.api(method="Document.update", params=params)

    def createPayment(self, invoiceId, paymentDate, amount, label, doctype):
        params = {
            "payment": {
                "date": paymentDate.timestamp(),
                "amount": f"{amount}",
                "medium": 1,
                "doctype": doctype,
                "docid": invoiceId,
                "ident": label,
            }
        }
        response = self.api(method="Document.createPayment", params=params)
        self.logger.debug(response)
        sellsyPaymentId = response["payrelid"]
        return sellsyPaymentId

    def deletePayment(self, paymentId, invoiceId, docType):
        params = {
            "payment": {
                "payid": paymentId,
                "doctype": docType,
                "docid": invoiceId,
            }
        }
        self.api(method="Document.deletePayment", params=params)
