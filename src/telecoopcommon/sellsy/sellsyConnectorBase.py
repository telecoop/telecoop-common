import os
from abc import ABC, abstractmethod

from .utils import sellsyValues


class TcSellsyConnectorBase(ABC):
    def __init__(self, conf: dict, logger, emailTemplates=None):
        env = os.getenv("ENV", "LOCAL")
        self.env = "PROD" if env in ["PROD", "LOCAL_PROD"] else "DEV"
        self.conf = conf
        self.logger = logger
        self.values = sellsyValues[self.env]
        self.url = ""
        self.conf = conf
        self.logger = logger
        self._connector = None
        self._getConnector()

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

        # === Funnels

        # Funnel VdC
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

        # Funnel Membership
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

        # Funnel Dev Pro
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

        # Funnel Sim Pro
        self.funnelIdSimsPro = sellsyValues[self.env]["funnel_id_sims_pro"]
        self.stepProSimsInactive = sellsyValues[self.env]["step_pro_sims_inactive"]
        self.stepProSimsAwaiting = sellsyValues[self.env]["step_pro_sims_awaiting"]
        self.stepProSimActivating = sellsyValues[self.env]["step_pro_sims_activating"]
        self.stepProSimsActivated = sellsyValues[self.env]["step_pro_sims_activated"]
        self.stepProSimsSuspended = sellsyValues[self.env]["step_pro_sims_suspended"]
        self.stepProSimsTerminated = sellsyValues[self.env]["step_pro_sims_terminated"]

        # Funnel Operator Change
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

        # Funnel Add New Line
        self.funnelIdAddNewLine = sellsyValues[self.env]["funnel_id_add_new_line"]
        self.stepAddNewLineSubscription = sellsyValues[self.env][
            "step_new_line_subscription"
        ]
        self.stepAddNewLineSimNewClientSob = sellsyValues[self.env][
            "step_new_line_new_client_sobriete"
        ]
        self.stepAddNewLineSimNewClientTrans = sellsyValues[self.env][
            "step_new_line_new_client_transition"
        ]
        self.stepAddNewLineSimNewClientKid = sellsyValues[self.env][
            "step_new_line_new_client_kid"
        ]
        self.stepAddNewLineSimSent = sellsyValues[self.env]["step_new_line_sim_sent"]

        # ===
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

    @abstractmethod
    def _getConnector(self) -> None:
        pass
