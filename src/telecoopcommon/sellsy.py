import sellsy_api
import time
import pytz
import os
import phpserialize
from json import JSONDecodeError
from datetime import datetime
from decimal import Decimal

from requests_oauth2client import OAuth2Client, ApiClient
from requests_oauth2client.auth import OAuth2ClientCredentialsAuth

sellsyValues = {
  'DEV': {
    'owner_id': 170714,
    'staff': {
      'support-client': 170761,
      'support-client-2': 170761,
      'support-societaire': 170714,
      'finance': 170714,
      'technique': 170761
    },
    'plans': {
      'Sobriété': 'PL_807',
      'Transition': 'PL_827',
      'Sobriété Pro': 'PL_750_pro',
      'Transition Pro': 'PL_796_pro',
    },
    'paydate_id': 3691808,
    'new_client_mail_template_id': 62573,
    'custom_fields': {
      'refbazile': 103778,
      'numerotelecoop': 103448,
      'nsce': 103775,
      'rio': 103447,
      'forfait': 154395,
      'achatsimphysique': 125472,
      'facturationmanuelle': 109341,
      'facture-unique': 117454,
      'date-activation-sim-souhaitee': 134623,
      'statut-client-abo-mobile': 141160,
      'birth-date': 103675,
      'birth-place': 103674,
      'offre-telecommown': 139323,
      'telecommown-origine': 139327,
      'telecommown-date-debut': 139329,
      'telecommown-date-fin': 139332,
      'abo-telecommown': 139325,
      'parrainage-code': 139333,
      'parrainage-lien': 139334,
      'parrainage-code-nb-use': 139352,
      'parrainage-nb-discount': 139353,
      'parrainage-code-parrain': 140671,
      'parrainage-nb-code-donated': 146337,
      'code-promo': 143564,
      'pack-depannage': 145684,
      'slimpay-mandate-status': 154395,
      'member': 103773,
      'phone-model': 103462,
      'mean-data-usage': 103460,
      'mean-messages-sent': 103461,
      'mean-voice-usage': 103458,
      'phone-state': 114653,
      'phone-year': 114652,
      'nb-shares': 103581,
      'shares-amount': 104629,
      'membership-ref': 103773,
      'membership-nb-shares': 103581,
      'membership-amount': 104629,
      'membership-payment-label': 181460,
      'membership-payment-mode': 181473,
      'membership-payment-date': 144644,
      'membership-accepted-date': 144643,
      'membership-category': 170554,
      'pro-nb-sims': 180710,
      'pro-nb-porta': 180712,
      'pro-date-engagement': 180713,
      'pro-estim-conso': 180711,
      'pro-comment': 180714,
      'pro-nom-utilisateur': 180715,
      'pro-mail-utilisateur': 180716,
      'pro-palier-suspension': 181292,
      'pro-appels-internationaux': 181282,
      'pro-donnees-mobiles': 181306,
      'pro-achats-contenu': 181291,
      'pro-achats-surtaxes': 181289,
    },
    'opportunity_source_interne': 119862,
    'opportunity_source_site_web': 119864,
    'opportunity_source_espace_client': 167236,
    'opportunity_source_tel_mail': 119863,
    'opportunity_source_lita': 178933,
    'opportunity_source_registre_excel': 178934,
    'funnel_id_vie_du_contrat': 62579,
    'step_new': 447893,
    'step_sim_to_send': 447894,
    'step_sim_to_send_transition': 573010,
    'step_sim_sent': 447895,
    'step_sim_received': 447896,
    'step_sim_pending_porta': 447897,
    'step_sim_pending_new': 447898,
    'step_sim_activated': 447899,
    'step_sim_suspended': 447900,
    'step_sim_terminated': 447901,
    'funnel_id_membership': 62446,
    'step_membership_asked': 446849,
    'step_membership_sign': 545658,
    'step_membership_paid': 447902,
    'step_membership_active': 545659,
    'funnel_id_membership2': 81505,
    'step_membership2_validated': 587185,
    'funnel_id_dev_pro': 85811,
    'step_pro_new': 619617,
    'step_pro_apt_planned': 619618,
    'step_pro_missing_info': 619619,
    'step_pro_awaiting': 619620,
    'step_pro_prop_todo': 619621,
    'step_pro_prop_internal_validation': 619622,
    'step_pro_prop_awaiting': 619623,
    'step_pro_prop_accepted': 619624,
    'step_pro_account_incomplete': 619625,
    'step_pro_account_complete': 619626,
    'step_pro_end': 619627,
    'step_pro_new_sims': 619628,
    'funnel_id_sims_pro': 85813,
    'step_pro_sims_inactive': 619636,
    'step_pro_sims_awaiting': 619637,
    'step_pro_sims_activating': 620880,
    'step_pro_sims_activated': 619638,
    'step_pro_sims_suspended': 619639,
    'step_pro_sims_terminated': 619640,
  },
  'PROD': {
    'owner_id': 170799,
    'staff': {
      'support-client': 170799,
      'support-client-2': 206337,
      'support-societaire': 183494,
      'finance': 174036,
      'technique': 168911
    },
    'plans': {
      'Sobriété': 'PL_750',
      'Transition': 'PL_796',
      'Sobriété Pro': 'PL_801',
      'Transition Pro': 'PL_802',
    },
    'paydate_id': 3527781,
    'new_client_mail_template_id': 62591,
    'custom_fields': {
      'refbazile': 103227,
      'numerotelecoop': 103670,
      'nsce': 102689,
      'rio': 102688,
      'forfait': 103346,
      'achatsimphysique': 125604,
      'date-activation-sim-souhaitee': 134621,
      'facturationmanuelle': 109534,
      'facture-unique': 119383,
      'statut-client-abo-mobile': 132773,
      'birth-date': 102695,
      'birth-place': 102696,
      'offre-telecommown': 139951,
      'telecommown-origine': 139954,
      'telecommown-date-debut': 139955,
      'telecommown-date-fin': 139956,
      'abo-telecommown': 139952,
      'parrainage-code': 139957,
      'parrainage-lien': 139958,
      'parrainage-code-nb-use': 139959,
      'parrainage-nb-discount': 139961,
      'parrainage-code-parrain': 140672,
      'parrainage-nb-code-donated': 146338,
      'code-promo': 144015,
      'pack-depannage': 145683,
      'slimpay-mandate-status': 171542,
      'member': 103406,
      'phone-model': 102178,
      'mean-data-usage': 100269,
      'mean-messages-sent': 102694,
      'mean-voice-usage': 102693,
      'phone-state': 114654,
      'phone-year': 114656,
      'nb-shares': 103223,
      'shares-amount': 104627,
      'membership-ref': 103406,
      'membership-nb-shares': 103223,
      'membership-amount': 104627,
      'membership-payment-label': 182000,
      'membership-payment-mode': 182001,
      'membership-payment-date': 104863,
      'membership-accepted-date': 104864,
      'membership-category': 179117,
      'pro-nb-sims': 180710,
      'pro-nb-porta': 180712,
      'pro-date-engagement': 180713,
      'pro-estim-conso': 180711,
      'pro-comment': 180714,
      'pro-nom-utilisateur': 180715,
      'pro-mail-utilisateur': 180716,
      'pro-palier-suspension': 180717,
      'pro-appels-internationaux': 180718,
      'pro-donnees-mobiles': 180719,
      'pro-achats-contenu': 180721,
      'pro-achats-surtaxes': 180720,
    },
    'opportunity_source_interne': 115933,
    'opportunity_source_site_web': 115935,
    'opportunity_source_espace_client': 173871,
    'opportunity_source_tel_mail': 115934,
    'opportunity_source_lita': 178840,
    'opportunity_source_registre_excel': 178841,
    'funnel_id_vie_du_contrat': 60663,
    'step_new': 446190,
    'step_sim_to_send': 434062,
    'step_sim_to_send_transition': 566314,
    'step_sim_sent': 444468,
    'step_sim_received': 434063,
    'step_sim_pending_porta': 444469,
    'step_sim_pending_new': 444470,
    'step_sim_activated': 442523,
    'step_sim_suspended': 446191,
    'step_sim_terminated': 446192,
    'funnel_id_membership': 60664,
    'step_membership_asked': 434065,
    'step_membership_sign': 452137,
    'step_membership_paid': 434066,
    'step_membership_active': 452138,
    'funnel_id_membership2': 85419,
    'step_membership2_validated': 616765,
    'funnel_id_dev_pro': 0,
    'step_pro_new': 0,
    'step_pro_apt_planned': 0,
    'step_pro_missing_info': 0,
    'step_pro_awaiting': 0,
    'step_pro_prop_todo': 0,
    'step_pro_prop_internal_validation': 0,
    'step_pro_prop_awaiting': 0,
    'step_pro_prop_accepted': 0,
    'step_pro_account_incomplete': 0,
    'step_pro_account_complete': 0,
    'step_pro_end': 0,
    'step_pro_new_sims': 0,
    'funnel_id_sims_pro': 0,
    'step_pro_sims_inactive': 0,
    'step_pro_sims_awaiting': 0,
    'step_pro_sims_activating': 0,
    'step_pro_sims_activated': 0,
    'step_pro_sims_suspended': 0,
    'step_pro_sims_terminated': 0,
  }
}

def step_name_from_id(step_id: int):
  env = 'PROD' if os.getenv('ENV') == 'PROD' else 'DEV'
  for key, value in sellsyValues[env].items():
    if value == step_id:
      return key

class TcSellsyError(Exception):
  pass

class TcSellsyConnector:
  def __init__(self, conf, logger):
    env = os.getenv('ENV', 'LOCAL')
    self.env = 'PROD' if env == 'PROD' else 'DEV'
    self.conf = conf
    self.logger = logger
    self._client = sellsy_api.Client(
      conf['consumer_token'],
      conf['consumer_secret'],
      conf['user_token'],
      conf['user_secret'])
    self._connector = None
    self.ownerId = sellsyValues[self.env]['owner_id']
    self.staff = sellsyValues[self.env]['staff']
    self.plans = sellsyValues[self.env]['plans']
    self.paydateId = sellsyValues[self.env]['paydate_id']
    self.sellsyNewClientMailTemplateId = sellsyValues[self.env]['new_client_mail_template_id']
    customFields = sellsyValues[self.env]['custom_fields']
    self.customFieldBazileNb = customFields['refbazile']
    self.customFieldTelecomNum = customFields['numerotelecoop']
    self.cfidManuelInvoice = customFields['facturationmanuelle']
    self.cfidMergeInvoices = customFields['facture-unique']
    self.cfIdStatusClientMobile = customFields['statut-client-abo-mobile']
    self.cfIdTeleCommownOffre = customFields['offre-telecommown']
    self.cfIdTeleCommownOrigine = customFields['telecommown-origine']
    self.cfIdTeleCommownDateDebut = customFields['telecommown-date-debut']
    self.cfIdTeleCommownDateFin = customFields['telecommown-date-fin']
    self.cfIdTeleCommownBoth = customFields['abo-telecommown']
    self.cfidSponsorCode = customFields['parrainage-code']
    self.cfidSponsorLink = customFields['parrainage-lien']
    self.cfidSponsorNbUse = customFields['parrainage-code-nb-use']
    self.cfidSponsorNbDiscount = customFields['parrainage-nb-discount']
    self.cfidSponsorRefereeCode = customFields['parrainage-code-parrain']
    self.cfidSponsorNbCodeDonated = customFields['parrainage-nb-code-donated']
    self.cfidPromoCode = customFields['code-promo']
    self.cfidPackDepannage = customFields['pack-depannage']
    self.cfidSlimpayMandateStatus = customFields['slimpay-mandate-status']
    self.cfidProNbSims = customFields['pro-nb-sims']
    self.cfidProNbPorta = customFields['pro-nb-porta']
    self.cfidProDateEngagement = customFields['pro-date-engagement']
    self.cfidProEstimConso = customFields['pro-estim-conso']
    self.cfidProComment = customFields['pro-comment']
    self.cfidProNomUtilisateur = customFields['pro-nom-utilisateur']
    self.cfidProMailUtilisateur = customFields['pro-mail-utilisateur']
    self.cfidProPalierSuspension = customFields['pro-palier-suspension']
    self.cfidProAppelInternationaux = customFields['pro-appels-internationaux']
    self.cfidProDonneesMobiles = customFields['pro-donnees-mobiles']
    self.cfidProAchatsContenu = customFields['pro-achats-contenu']
    self.cfidProAchatsSurtaxes = customFields['pro-achats-surtaxes']

    self.opportunitySourceInterne = sellsyValues[self.env]['opportunity_source_interne']
    self.opportunitySourceSiteWeb = sellsyValues[self.env]['opportunity_source_site_web']
    self.opportunitySourceEspaceClient = sellsyValues[self.env]['opportunity_source_espace_client']
    self.opportunitySourceTelMail = sellsyValues[self.env]['opportunity_source_tel_mail']

    self.funnelIdVdc = sellsyValues[self.env]['funnel_id_vie_du_contrat']
    self.stepNew = sellsyValues[self.env]['step_new']
    self.stepSimToSend = sellsyValues[self.env]['step_sim_to_send']
    self.stepSimToSendTransition = sellsyValues[self.env]['step_sim_to_send_transition']
    self.stepSimSent = sellsyValues[self.env]['step_sim_sent']
    self.stepSimReceived = sellsyValues[self.env]['step_sim_received']
    self.stepSimPendingPorta = sellsyValues[self.env]['step_sim_pending_porta']
    self.stepSimPendingNew = sellsyValues[self.env]['step_sim_pending_new']
    self.stepSimActivated = sellsyValues[self.env]['step_sim_activated']
    self.stepSimSuspended = sellsyValues[self.env]['step_sim_suspended']
    self.stepSimTerminated = sellsyValues[self.env]['step_sim_terminated']

    self.funnelIdMembership = sellsyValues[self.env]['funnel_id_membership']
    self.stepMembershipAsked = sellsyValues[self.env]['step_membership_asked']
    self.stepMembershipSign = sellsyValues[self.env]['step_membership_sign']
    self.stepMembershipPaid = sellsyValues[self.env]['step_membership_paid']
    self.stepMembershipActive = sellsyValues[self.env]['step_membership_active']

    self.funnelIdMembership2 = sellsyValues[self.env]['funnel_id_membership2']
    self.stepMembership2Validated = sellsyValues[self.env]['step_membership2_validated']

    self.funnelIdDevPro = sellsyValues[self.env]['funnel_id_dev_pro']
    self.stepProNew = sellsyValues[self.env]['step_pro_new']
    self.stepProAptPlanned = sellsyValues[self.env]['step_pro_apt_planned']
    self.stepProMissingInfo = sellsyValues[self.env]['step_pro_missing_info']
    self.stepProAwaiting = sellsyValues[self.env]['step_pro_awaiting']
    self.stepProPropTodo = sellsyValues[self.env]['step_pro_prop_todo']
    self.stepProPropInternalValidation = sellsyValues[self.env]['step_pro_prop_internal_validation']
    self.stepProPropAwaiting = sellsyValues[self.env]['step_pro_prop_awaiting']
    self.stepProPropAccepted = sellsyValues[self.env]['step_pro_prop_accepted']
    self.stepProAccountIncomplete = sellsyValues[self.env]['step_pro_account_incomplete']
    self.stepProAccountComplete = sellsyValues[self.env]['step_pro_account_complete']
    self.stepProEnd = sellsyValues[self.env]['step_pro_end']
    self.stepProNewSims = sellsyValues[self.env]['step_pro_new_sims']

    self.funnelIdSimsPro = sellsyValues[self.env]['funnel_id_sims_pro']
    self.stepProSimsInactive = sellsyValues[self.env]['step_pro_sims_inactive']
    self.stepProSimsAwaiting = sellsyValues[self.env]['step_pro_sims_awaiting']
    self.stepProSimActivating = sellsyValues[self.env]['step_pro_sims_activating']
    self.stepProSimsActivated = sellsyValues[self.env]['step_pro_sims_activated']
    self.stepProSimsSuspended = sellsyValues[self.env]['step_pro_sims_suspended']
    self.stepProSimsTerminated = sellsyValues[self.env]['step_pro_sims_terminated']

  def getConnector(self):
    if self._connector is None:
      self._oauth2client = OAuth2Client(
        token_endpoint="https://login.sellsy.com/oauth2/access-tokens",
        auth=(self.conf['v2_client_id'], self.conf['v2_client_secret']),
      )
      self._connector = ApiClient(
        self.conf['v2_host'],
        auth=OAuth2ClientCredentialsAuth(self._oauth2client),
        raise_for_status=False
      )
    return self._connector

  def getToken(self):
    return self._oauth2client.client_credentials()

  def api2Get(self, endpoint):
    connector = self.getConnector()
    self.logger.debug(f"Calling Sellsy API v2 GET {endpoint}")
    return connector.get(endpoint)

  def api2Post(self, endpoint, data):
    connector = self.getConnector()
    self.logger.debug(f"Calling Sellsy API v2 POST {endpoint} with {data}")
    return connector.post(endpoint, json=data)

  def api(self, method, params={}):
    try:
      self.logger.debug(f"Calling Sellsy {method} with params {params}")
      retry = 3
      result = None
      while retry >= 0:
        if retry < 3:
          self.logger.info(f"Retrying for the {3-retry}th time")
        try:
          result = self._client.api(method, params)
          retry = -1
        except JSONDecodeError as e:
          if (retry < 1):
            self.logger.warning(e)
            raise e
          retry -= 1
          time.sleep(1)
        except sellsy_api.errors.SellsyError as e:
          if (e.sellsy_code_error == 'E_OBJ_NOT_LOADABLE'):
            if (retry < 1):
              self.logger.warning(e)
              raise e
            retry -= 1
            time.sleep(1)
          else:
            raise e
    except sellsy_api.errors.SellsyAuthenticateError as e:  # raised if credential keys are not valid
      self.logger.warning('Authentication failed ! Details : {}'.format(e))
      raise e
    except sellsy_api.errors.SellsyError as e:  # raised if an error is returned by Sellsy API
      self.logger.warning(e)
      raise e
    # Sellsy API is throttled at 5 requests per second, we take a margin of 0.25s
    time.sleep(0.25)
    return result

  def updateClientProperty(self, clientId, property, value):
    client = self.getClient(clientId)
    params = {
      'clientid': clientId,
      'third': {
        'name': client.label,
      }
    }
    response = None
    if property in ['mobile', 'email']:
      if client.type == 'person':
        params = {
          'clientid': clientId,
          'third': {
            'name': client.name,
            property: value
          },
          'contact': {
            'name': client.name,
            'forename': client.firstname,
            property: value
          }
        }
        response = self.api(method="Client.update", params=params)
      else:
        params = {
          'clientid': clientId,
          'contactid': client.mainContactId,
          'contact': {
            'name': client.name,
            property: value
          }
        }
        response = self.api(method="Client.updateContact", params=params)

    return response

  def updateCustomField(self, entity, entityId, cfid, value):
    knownEntities = ['client', 'opportunity']
    if (entity not in knownEntities):
      raise ValueError(f"Unknown entity {entity}, should be in {knownEntities}")
    params = {
      'linkedtype': entity,
      'linkedid': entityId,
      'values': [
        {'cfid': cfid, 'value': str(value) if value == 0 else value},
      ]
    }
    return self.api(method='CustomFields.recordValues', params=params)

  def getClientRef(self, clientId):
    response = self.api(method="Client.getOne", params={'clientid': clientId})
    return response['ident']

  def getTeleCommownOptinDate(self, clientId=None, opportunityId=None):
    if clientId is None and opportunityId is None:
      raise ValueError("Either clientId or opportunityId should be not None")
    response = None
    if clientId is not None:
      response = self.api(method="Client.getOne", params={'clientid': clientId})
    if opportunityId is not None:
      response = self.api(method="opportunities.getOne", params={'id': opportunityId})
    optinDate = None
    for ln in response['customFields']:
      if (ln['name'] == 'Z-Offre TeleCommown'):
        fields = ln['list'] if isinstance(ln['list'], list) else ln['list'].values()
        for f in fields:
          if (f['code'] == 'offre-telecommown' and 'formatted_ymd' in f and f['formatted_ymd'] != ""):
            optinDate = pytz.timezone('Europe/Paris').localize(datetime.strptime(f['formatted_ymd'], '%Y-%m-%d'))
            break
        break
    return optinDate

  def getClient(self, id):
    c = SellsyClient(id)
    c.loadWithValues(self.getClientValues(id))
    return c

  def getClientValues(self, id):
    cli = self.api(method="Client.getOne", params={'clientid': id})

    mainContactId = cli['client']['maincontactid']

    result = {
      'ident': cli['client']['ident'],
      'type': cli['client']['type'],
      'joindate': cli['client']['joindate'],
      'dateTransformProspect': cli['client']['transformationDate'],
      'people_name': '',
      'people_forename': '',
      'email': '',
      'mobile': '',
      'maincontactid':  mainContactId,
      'contacts': {},
    }
    customFields = {
      'refbazile':                  {'code': 'refbazile', 'textval': ''},
      'facturationmanuelle':        {'code': 'facturationmanuelle', 'formatted_value': ''},
      'facture-unique':             {'code': 'facture-unique', 'formatted_value': ''},
      'statut-client-abo-mobile':   {'code': 'statut-client-abo-mobile', 'textval': ''},
      'parrainage-code':            {'code': 'parrainage-code', 'textval': ''},
      'parrainage-lien':            {'code': 'parrainage-lien', 'textval': ''},
      'parrainage-code-nb-use':     {'code': 'parrainage-code-nb-use', 'defaultValue': '0'},
      'parrainage-nb-discount':     {'code': 'parrainage-nb-discount', 'defaultValue': '0'},
      'parrainage-code-parrain':    {'code': 'parrainage-code-parrain', 'textval': ''},
      'parrainage-nb-code-donated': {'code': 'parrainage-nb-code-donated', 'defaultValue': '0'},
      'offre-telecommown':          {'code': 'offre-telecommown', 'timestampval': ''},
      'telecommown-date-debut':     {'code': 'telecommown-date-debut', 'timestampval': ''},
      'telecommown-date-fin':       {'code': 'telecommown-date-fin', 'timestampval': ''},
      'telecommown-origine':        {'code': 'telecommown-origine', 'formatted_value': ''},
      'abo-telecommown':            {'code': 'abo-telecommown', 'defaultValue': ''},
      'code-promo':                 {'code': 'code-promo', 'textval': ''},
      'slimpay-mandate-status':     {'code': 'slimpay-mandate-status', 'textval': ''},
      'societaire':                 {'code': 'societaire', 'textval': ''},
      'typetelephone':              {'code': 'typetelephone', 'textval': ''},
      'consomoyenneclient':         {'code': 'consomoyenneclient', 'defaultValue': '0'},
      'smsmoyen':                   {'code': 'smsmoyen', 'defaultValue': '0'},
      'hrappel':                    {'code': 'hrappel', 'defaultValue': '0'},
      'neufreconditionne':          {'code': 'neufreconditionne', 'formatted_value': ''},
      'achattelephone':             {'code': 'achattelephone', 'defaultValue': '0'},
    }
    # Name + person data
    if (cli['client']['type'] == 'person'):
      contact = cli['contact'] if 'contact' in cli else cli['contacts'][mainContactId]
      civility = 'M' if contact['civil'] == 'man' else 'Mme'
      result['name'] = f"{civility} {contact['name']} {contact['forename']}"
      result['email'] = contact['email']
      result['mobile'] = contact['mobile']
      result['people_name'] = contact['name']
      result['people_forename'] = contact['forename']
    elif (cli['client']['type'] == 'corporation'):
      corporation = cli['corporation']
      result['name'] = corporation['name']
      result['email'] = corporation['email']
      result['mobile'] = corporation['mobile']
    # Contacts
    if ('contacts' in cli and mainContactId in cli['contacts']):
      result['contacts'][mainContactId] = cli['contacts'][mainContactId]
    elif ('contact' in cli):
      result['contacts'][mainContactId] = cli['contact']
    # Custom fields
    for ln in cli['customFields']:
      fields = ln['list'].values() if isinstance(ln['list'], dict) else ln['list']
      for f in fields:
        if ('code' in f):
          code = f['code']
          textFields = [
            "refbazile", 'parrainage-code', 'parrainage-lien', 'societaire', 'typetelephone',
            'parrainage-code-parrain', 'code-promo', 'slimpay-mandate-status']
          selectFields = ["facturationmanuelle", 'statut-client-abo-mobile', 'telecommown-origine', 'neufreconditionne']
          dateFields = ['offre-telecommown', 'telecommown-date-debut', 'telecommown-date-fin']
          intFields = ['parrainage-nb-discount', 'parrainage-code-nb-use', 'parrainage-nb-code-donated',
                       'consomoyenneclient', 'smsmoyen', 'hrappel', 'achattelephone']
          if (code in textFields):
            customFields[code]['textval'] = f["defaultValue"]
          elif (code in selectFields and 'formatted_value' in f):
            customFields[code]['formatted_value'] = f["formatted_value"]
          elif (code in ["facture-unique", 'abo-telecommown']):
            customFields[code]['boolval'] = (f["defaultValue"] == 'Y')
          elif (code in intFields):
            try:
              customFields[code]['numericval'] = int(f['defaultValue'])
            except ValueError:
              customFields[code]['numericval'] = 0
          elif (code in dateFields and 'formatted_ymd' in f):
            customFields[code]['formatted_ymd'] = f['formatted_ymd']
    result['customfields'] = customFields.values()

    return result

  def getClientFromRef(self, ref):
    params = {
      'search': {
        'ident': ref
      }
    }
    clients = self.api(method='Client.getList', params=params)
    client = None
    if clients['result']:
      for id, cli in clients['result'].items():
        if (cli['ident'] == 'CLI00001001'):
          # Référence ayant servie de test lors de la mise en prod du parcours souscription
          continue

        client = SellsyClient(id)
        client.loadWithValues(cli)
        break

    return client

  def getClients(self):
    result = {}
    params = {
      'pagination': {
        'nbperpage': 1000,
        'pagenum': 1
      }
    }
    clients = self.api(method='Client.getList', params=params)
    infos = clients["infos"]
    nbPages = infos["nbpages"]
    currentPage = 1
    while (currentPage <= nbPages):
      self.logger.info("Processing page {}/{}".format(currentPage, nbPages))
      for id, client in clients['result'].items():
        if (client['ident'] == 'CLI00001001'):
          # Référence ayant servie de test lors de la mise en prod du parcours souscription
          continue

        if (client['ident'] is not None and client['ident'] not in ['', '-1']):
          c = SellsyClient(id)
          c.loadWithValues(client)
          result[id] = c
        else:
          self.logger.warning(f"Client #{id} has no reference")

      currentPage += 1
      if (infos["pagenum"] <= nbPages):
        params['pagination']['pagenum'] = currentPage
        clients = self.api(method="Client.getList", params=params)
        infos = clients["infos"]

    return result

  def getOpportunity(self, id):
    o = SellsyOpportunity(id)
    o.loadWithValues(self.getOpportunityValues)
    return o

  def getOpportunityValues(self, id):
    opp = self.api(method="Opportunities.getOne", params={'id': id})
    result = {
      'ident': opp['ident'],
      'name': opp['name'],
      'relationType': opp['relationType'],
      'linkedid': opp['linkedid'],
      'funnelid': opp['funnelid'],
      'created': opp['created'],
      'statusLabel': opp['statusLabel'],
      'stepEnterDate': opp['stepEnterDate'],
      'stepid': opp['stepid'],
      'customfields': {
        'nsce': {'code': 'nsce', 'textval': ''},
        'numerotelecoop': {'code': 'numerotelecoop', 'textval': ''},
        'rio': {'code': 'rio', 'textval': ''},
        'refbazile': {'code': 'refbazile', 'textval': ''},
        'forfait': {'code': 'forfait', 'textval': ''},
        'achatsimphysique': {'code': 'achatsimphysique', 'boolval': False},
        'date-activation-sim-souhaitee': {'code': 'date-activation-sim-souhaitee', 'timestampval': 0},
        'offre-telecommown': {'code': 'offre-telecommown', 'timestampval': 0},
        'parrainage-code-parrain': {'code': 'parrainage-code-parrain', 'textval': ''},
        'telecommown-date-debut': {'code': 'telecommown-date-debut', 'timestampval': 0},
        'telecommown-date-fin': {'code': 'telecommown-date-fin', 'timestampval': 0},
        'telecommown-origine': {'code': 'telecommown-origine', 'formatted_value': ''},
        'abo-telecommown': {'code': 'abo-telecommown', 'boolval': False},
        'code-promo': {'code': 'code-promo', 'textval': ''},
        'pack-depannage': {'code': 'pack-depannage', 'defaultValue': '0', 'numericval': 0},
        'pro-nb-sims': {'code': 'pro-nb-sims', 'defaultValue': '0', 'numericval': 0},
        'pro-nb-porta': {'code': 'pro-nb-porta', 'defaultValue': '0', 'numericval': 0},
        'pro-date-engagement': {'code': 'pro-date-engagement', 'timestampval': 0},
        'pro-estim-conso': {'code': 'pro-estim-conso', 'textval': ''},
        'pro-comment': {'code': 'pro-comment', 'textval': ''},
        'pro-nom-utilisateur': {'code': 'pro-nom-utilisateur', 'textval': ''},
        'pro-mail-utilisateur': {'code': 'pro-mail-utilisateur', 'textval': ''},
        'pro-palier-suspension': {'code': 'pro-palier-suspension', 'formatted_value': ''},
        'pro-appels-internationaux': {'code': 'pro-appels-internationaux', 'formatted_value': ''},
        'pro-donnees-mobiles': {'code': 'pro-donnees-mobiles', 'formatted_value': ''},
        'pro-achats-contenu': {'code': 'pro-achats-contenu', 'boolval': True},
        'pro-achats-surtaxes': {'code': 'pro-achats-surtaxes', 'boolval': True},
      }
    }

    for ln in opp['customFields']:
      fields = ln['list'].values() if isinstance(ln['list'], dict) else ln['list']
      for field in fields:
        if ('code' in field):
          code = field['code']
          textFields = [
            'rio', 'nsce', 'numerotelecoop', 'refbazile', 'code-promo', 'parrainage-code-parrain',
            'pro-estim-conso', 'pro-comment', 'pro-nom-utilisateur', 'pro-mail-utilisateur']
          listFields = [
            'telecommown-origine', 'forfait',
            'pro-palier-suspension', 'pro-appels-internationaux', 'pro-donnees-mobiles']
          dateFields = [
            'date-activation-sim-souhaitee', 'offre-telecommown', 'telecommown-date-debut', 'telecommown-date-fin',
            'pro-date-engagement']
          if (code in textFields):
            result['customfields'][code]['textval'] = field['defaultValue']
          if (code in listFields and 'formatted_value' in field):
            result['customfields'][code]['formatted_value'] = field["formatted_value"]
          if (code in ['achatsimphysique', 'abo-telecommown', 'pro-achats-contenu', 'pro-achats-surtaxes']):
            result['customfields'][code]['boolval'] = (field["defaultValue"] == "Y")
          if (code in dateFields and 'formatted_ymd' in field):
            result['customfields'][code]['formatted_ymd'] = field['formatted_ymd']
          if (code in ['pack-depannage', 'pro-nb-sims', 'pro-nb-porta']):
            try:
              result['customfields'][code]['numericval'] = int(field['defaultValue'])
            except ValueError:
              result['customfields'][code]['numericval'] = 0

    return result

  def getMembershipOpportunityValues(self, id):
    opp = self.api(method="Opportunities.getOne", params={'id': id})
    result = {
      'ident': opp['ident'],
      'name': opp['name'],
      'relationType': opp['relationType'],
      'linkedid': opp['linkedid'],
      'funnelid': opp['funnelid'],
      'created': opp['created'],
      'statusLabel': opp['statusLabel'],
      'stepEnterDate': opp['stepEnterDate'],
      'stepid': opp['stepid'],
      'customfields': {
        'partssocialessouhaite': {'code': 'partssocialessouhaite', 'defaultValue': ''},
        'montantparts': {'code': 'montantparts', 'defaultValue': ''},
        'dateversementsocietariat': {'code': 'dateversementsocietariat', 'timestamptval': ''},
        'dateacceptationsocietariat': {'code': 'dateacceptationsocietariat', 'timestamptval': ''},
      }
    }

    for ln in opp['customFields']:
      fields = ln['list'].values() if isinstance(ln['list'], dict) else ln['list']
      for field in fields:
        if ('code' in field):
          code = field['code']
          if (code in ['dateversementsocietariat', 'dateacceptationsocietariat'] and 'formatted_ymd' in field):
            result['customfields'][code]['formatted_ymd'] = field['formatted_ymd']
          if (code in ['partssocialessouhaite', 'montantparts']):
            result['customfields'][code]['numericval'] = int(field['defaultValue'])

    return result

  def getOpportunities(self):
    return self.getOpportunitiesInStep(funnelId=self.funnelIdVdc, stepId="all")

  def getOpportunitiesInStep(self, funnelId, stepId, limit=None, startDate=None, searchParams=None):
    result = []
    params = {
      'pagination': {
        'nbperpage': 1000,
        'pagenum': 1
      },
      'search': {
        'funnelid': funnelId
      }
    }
    if stepId != 'all':
      params['search']['stepid'] = stepId
    if startDate is not None:
      params['search']['periodecreated_start'] = startDate.timestamp()
    if searchParams is not None:
      for k, v in searchParams.items():
        params['search'][k] = v

    opportunities = self.api(method='Opportunities.getList', params=params)
    infos = opportunities["infos"]
    nbPages = infos["nbpages"]
    currentPage = 1
    while (currentPage <= nbPages):
      self.logger.info("Processing page {}/{}".format(currentPage, nbPages))
      for id, opp in opportunities['result'].items():
        o = SellsyOpportunity(id)
        o.loadWithValues(opp)
        result.append(o)
        if limit is not None and limit <= len(result):
          return result

      currentPage += 1
      if (infos["pagenum"] <= nbPages):
        params['pagination']['pagenum'] = currentPage
        opportunities = self.api(method="Opportunities.getList", params=params)
        infos = opportunities["infos"]

    return result

  def getClientOpportunities(self, clientId):
    result = []
    params = {'search': {'thirds': [clientId, ]}, 'pagination': {'nbperpage': 200}}
    opportunities = self.api(method="Opportunities.getList", params=params)
    if len(opportunities['result']) == 0:
      return result
    for opp in opportunities['result'].values():
      o = SellsyOpportunity(opp['id'])
      o.loadWithValues(opp)
      result.append(o)
    return result

  def getOpportunityFromClientAndMsisdn(self, clientId, msisdn):
    opportunities = self.getClientOpportunities(clientId)
    for opp in opportunities:
      if opp.msisdn == msisdn:
        return opp
    else:
      raise LookupError(f"Could not opportunity with msisdn {msisdn} for client #{clientId}")

  def getServices(self):
    params = {
      'type': 'service',
      'pagination': {
        'nbperpage': 100,
      }
    }
    services = self.api(method='Catalogue.getList', params=params)
    data = {}
    for id, service in services['result'].items():
      if ('name' in service):
        data[service['name']] = {
          'id': service['id'],
          'unitAmount': service['unitAmountTaxesInc'],
          'taxId': service['taxid'],
          'notes': service['notes'],
          'tradename': service['tradename']
        }

    return data

  def getInvoiceValues(self, id):
    invoice = self.api(method="Document.getOne", params={'doctype': 'invoice', 'docid': id})
    result = {
      'ident': invoice['ident'],
      'status': invoice['status'],
      'step_id': invoice['step'],
      'totalAmountTaxesFree': invoice['totalAmountTaxesFree'],
      'taxesAmountSum': invoice['taxesAmountSum'],
      'totalAmount': invoice['totalAmount'],
      'dueAmount': invoice['dueAmount'],
      'payDateCustom': datetime.strptime(invoice['paydate_custom'], "%d/%m/%Y").strftime("%Y-%m-%d"),
      'thirdident': invoice['thirdident'],
      'subject': invoice['subject'],
      'created': invoice['created'],
      'payMediumsText': invoice['paymediums_text'],
      'rows': [],
    }
    for row in invoice['map']['rows'].values():
      if not isinstance(row, dict):
        # Sellsy sends rubbish like '_xml_childtag': 'row' in the json response …
        continue
      qt = Decimal(row['qt'])
      amount = Decimal(row['totalAmountTaxesInc'])
      if qt != 0 and amount != 0:
        result['rows'].append({
          'item': row['type'],
          'ref': row['name'],
          'label': row['notes'],
          'unitAmount': Decimal(row['unitAmountTaxesInc']),
          'quantity': qt,
          'amount': amount,
          'taxes': Decimal(row['taxAmount']),
          'amountTaxFree': Decimal(row['totalAmount']),
        })

    return result

  def updateInvoiceStatus(self, invoiceId, status):
    params = {
      'docid': invoiceId,
      'document': {
        'doctype': 'invoice',
        'step': status
      }
    }
    self.api(method='Document.updateStep', params=params)

  def updateInvoicePaymentDate(self, invoiceId, nbDays):
    params = {
      'docid': invoiceId,
      'document': {
        'doctype': 'invoice',
      },
      'paydate': {
        'id': self.paydateId,
        'xdays': nbDays
      }
    }
    self.api(method='Document.update', params=params)

  def createPayment(self, invoiceId, paymentDate, amount, label):
    params = {
      'payment': {
        'date': paymentDate.timestamp(),
        'amount': f"{amount}",
        'medium': 1,
        'doctype': 'invoice',
        'docid': invoiceId,
        'ident': label,
      }
    }
    response = self.api(method="Document.createPayment", params=params)
    self.logger.debug(response)
    sellsyPaymentId = response['payrelid']
    return sellsyPaymentId

  def deletePayment(self, paymentId, invoiceId):
    params = {
      'payment': {
        'payid': paymentId,
        'doctype': 'invoice',
        'docid': invoiceId,
      }
    }
    self.api(method="Document.deletePayment", params=params)


class SellsyClient:
  def __init__(self, id):
    self.id = id
    self.creationDate = None
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
    self.web = None
    self.mainContactId = None
    self.oneInvoicePerLine = None
    self.autoValidation = None
    self.status = None
    self.member = None
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
    self.refereeCode = None
    self.promoCode = None
    self.slimpayMandateStatus = None

  def __str__(self):
    return f"#{self.id} {self.reference} {self.label} {self.email} {self.status} {self.creationDate.isoformat()}"

  @classmethod
  def create(cls, values, sellsyConnector: TcSellsyConnector):
    sc = sellsyConnector
    if 'name' not in values:
      raise ValueError("Client name is missing")
    data = {'third': {}}
    fields = [
      'name', 'ident', 'type', 'email', 'mobile', 'joinDate', 'web', 'siret', 'siren', 'vat', 'rcs', 'apenaf', 'tags']
    for fld in fields:
      if fld in values:
        data['third'][fld] = values[fld]
    if 'contact' in values:
      fields = ['name', 'forename', 'email', 'mobile', 'web', 'position', 'civil', 'birthdate']
      contact = values['contact']
      data['contact'] = {}
      for fld in fields:
        if fld in contact:
          data['contact'][fld] = contact[fld]
    if 'address' in values:
      fields = ['name', 'part1', 'part2', 'part3', 'part4', 'zip', 'town', 'countrycode']
      address = values['address']
      data['address'] = {}
      for fld in fields:
        if fld in address:
          data['address'][fld] = address[fld]

    response = sc.api(method="Client.create", params=data)
    sc.logger.debug(response)
    clientId = response['client_id']
    if 'customFields' in values:
      cfIds = sellsyValues[sc.env]['custom_fields']
      for cfName, cfValue in values['customFields'].items():
        sc.updateCustomField('client', clientId, cfIds[cfName], cfValue)

    cli = SellsyClient(clientId)
    cli.load(sc)
    return cli

  def load(self, connector):
    self.loadWithValues(connector.getClientValues(self.id))

  def loadWithValues(self, cli):
    parisTZ = pytz.timezone('Europe/Paris')
    email = cli['email']
    name = cli['people_name']
    firstname = cli['people_forename']
    civility = cli.get('people_civil')
    # recherche du contact principal
    mainContactId = cli['maincontactid']
    if 'contacts' in cli:
      for contactId, contact in cli["contacts"].items():
        if (contactId == mainContactId):
          email = contact['email']
          name = contact['name']
          firstname = contact['forename']
          civility = contact['civil']

    actif = cli.get('actif')
    self.creationDate = parisTZ.localize(datetime.fromisoformat(cli['joindate']))
    if cli['dateTransformProspect'] is not None:
      self.conversionToClientDate = parisTZ.localize(datetime.fromisoformat(cli['dateTransformProspect']))
    self.actif = actif == 'Y' if actif else None
    self.reference = cli['ident']
    self.type = cli['type']
    self.label = cli['name']
    self.name = name
    self.firstname = firstname
    self.civility = civility
    self.companyName = cli['name'] if self.type == 'corporation' else None
    self.email = email
    self.web = cli.get('web')
    self.msisdn = cli['mobile']
    self.mainContactId = mainContactId
    self.lines = [{
      'msisdn': cli['mobile'].replace('+33', '0')
    }]
    for f in cli["customfields"]:
      code = f["code"]
      if (code == "refbazile"):
        self.lines[0]['bazileNum'] = f["textval"]
      elif (code == "facturationmanuelle"):
        self.autoValidation = (f["formatted_value"] in ['', 'automatique'])
      elif (code == "facture-unique"):
        if (isinstance(f["boolval"], bool)):
          self.oneInvoicePerLine = (not f["boolval"])
        else:
          self.oneInvoicePerLine = (f['boolval'] == 'N')
      elif (code == 'statut-client-abo-mobile' and 'formatted_value' in f):
        self.status = f["formatted_value"]

      elif code == 'societaire':
        self.member = f['textval']
      elif code == 'typetelephone':
        self.phoneModel = f['textval']
      elif code == 'consomoyenneclient':
        self.meanDataUsage = int(f['numericval'])
      elif code == 'smsmoyen':
        self.meanMessagesSent = int(f['numericval'])
      elif code == 'hrappel':
        self.meanVoiceUsage = int(f['numericval'])
      elif code == 'neufreconditionne':
        self.phoneState = f['formatted_value']
      elif code == 'achattelephone':
        self.phoneYear = int(f['numericval'])

      elif (code == 'parrainage-code'):
        self.sponsorCode = f['textval']
      elif (code == 'parrainage-lien'):
        self.sponsorLink = f['textval']
      elif (code == 'parrainage-code-nb-use'):
        self.sponsorNbUse = int(f['numericval'])
      elif (code == 'parrainage-nb-discount'):
        self.sponsorNbDiscount = int(f['numericval'])
      elif (code == 'parrainage-code-parrain'):
        self.refereeCode = f['textval']
      elif (code == 'parrainage-nb-code-donated'):
        self.sponsorNbCodeDonated = int(f['numericval'])

      elif (code == 'offre-telecommown' and 'formatted_ymd' in f and f['formatted_ymd'] != ''):
        self.optinTeleCommown = parisTZ.localize(datetime.strptime(f['formatted_ymd'], '%Y-%m-%d'))
      elif (code == 'telecommown-date-debut' and 'formatted_ymd' in f and f['formatted_ymd'] != ''):
        self.telecommownStart = parisTZ.localize(datetime.strptime(f['formatted_ymd'], '%Y-%m-%d'))
      elif (code == 'telecommown-date-fin' and 'formatted_ymd' in f and f['formatted_ymd'] != ''):
        self.telecommownEnd = parisTZ.localize(datetime.strptime(f['formatted_ymd'], '%Y-%m-%d'))
      elif (code == 'telecommown-origine'):
        self.telecommownOrigin = f['formatted_value']
      elif (code == 'abo-telecommown'):
        if (isinstance(f["boolval"], bool)):
          self.telecommownAbo = f['boolval']
        else:
          self.telecommownAbo = (f['boolval'] == 'Y')

      elif (code == 'code-promo'):
        self.promoCode = f['textval']

      elif code == 'slimpay-mandate-status':
        self.slimpayMandateStatus = f['textval']

  def getOpportunities(self, connector):
    opps = connector.getClientOpportunities(self.id)
    for opp in opps:
      opp.client = self
    return opps

class SellsyOpportunity:
  def __init__(self, id):
    env = os.getenv('ENV', 'LOCAL')
    self.env = 'PROD' if env == 'PROD' else 'DEV'

    self.id = id
    self.reference = None
    self.name = None
    self.clientId = None
    self.client = None
    self.prospectId = None
    self.funnelId = None
    self.creationDate = None
    self.stepId = None
    self.stepStart = None
    self.steps = None
    self.status = None
    self.nsce = None
    self.msisdn = None
    self.bazileNum = None
    self.rio = None
    self.plan = None
    self.planItem = None
    self.achatSimPhysique = None
    self.dateActivationSimAsked = None
    self.optinTeleCommown = None
    self.telecommownStart = None
    self.telecommownEnd = None
    self.telecommownAbo = None
    self.promoCode = None
    self.refereeCode = None
    self.packDepannage = None
    self.proNbSims = None
    self.proNbPorta = None
    self.proDateEngagement = None
    self.proEstimConso = None
    self.proComment = None
    self.proNomUtilisateur = None
    self.proMailUtilisateur = None
    self.proPalierSuspension = None
    self.proAppelsInternationaux = None
    self.proDonneesMobiles = None
    self.proAchatContenu = None
    self.proAchatsSurtaxes = None

    self.plans = sellsyValues[self.env]['plans']

  @property
  def stepName(self):
    return step_name_from_id(self.stepId)

  def __str__(self):
    return f"#{self.id} {self.creationDate} {self.msisdn} client #{self.clientId}"

  @classmethod
  def create(cls, values, sellsyConnector: TcSellsyConnector):
    sc = sellsyConnector
    if 'name' not in values:
      raise ValueError("Opportunity name is missing")
    data = {'opportunity': {}}
    fields = [
      ('linkedtype', 'type'),
      ('linkedid', 'clientId'),
      ('ident', 'reference'),
      ('sourceid', 'sourceId'),
      ('creationDate', 'creationDate'),
      ('name', 'name'),
      ('funnelid', 'funnelId'),
      ('stepid', 'stepId'),
      ('contacts', 'contacts'),
      ('potential', 'amount'),
    ]
    for fldSellsy, fld in fields:
      if fld in values:
        data['opportunity'][fldSellsy] = values[fld]

    if 'linkedtype' not in data['opportunity']:
      data['opportunity']['linkedtype'] = 'third'

    response = sc.api(method="Opportunities.create", params=data)
    sc.logger.debug(response)
    oppId = response
    if 'customFields' in values:
      cfIds = sellsyValues[sc.env]['custom_fields']
      for cfName, cfValue in values['customFields'].items():
        sc.updateCustomField('opportunity', oppId, cfIds[cfName], cfValue)

    opp = SellsyOpportunity(oppId)
    opp.load(sc)
    return opp

  def load(self, connector):
    values = connector.getOpportunityValues(self.id)
    self.loadWithValues(values)

  def getClient(self, connector):
    if self.client is None and self.clientId is not None:
      self.client = SellsyClient(self.clientId)
      self.client.load(connector)
    return self.client

  def loadWithValues(self, opp):
    parisTZ = pytz.timezone('Europe/Paris')
    if opp['relationType'] == 'client':
      self.clientId = opp['linkedid']
    else:
      self.prospectId = opp['linkedid']
    self.reference = opp['ident']
    self.name = opp['name']
    self.funnelId = opp['funnelid']
    self.creationDate = parisTZ.localize(datetime.fromisoformat(opp['created']))
    self.status = opp['statusLabel']
    self.stepId = int(opp['stepid'])
    self.stepStart = parisTZ.localize(datetime.fromisoformat(opp['stepEnterDate']))
    self.steps = {opp['stepid']: self.stepStart}

    for fieldId, field in opp['customfields'].items():
      if ('code' in field):
        code = field['code']
        if (code == 'rio'):
          self.rio = field['textval']
        if (code == 'forfait'):
          # plan should always be known
          # BUT there's a bug in Sellsy in DEV env where custom field 'forfait' is unknown and unsettable. O joy.
          if self.env == 'DEV' and 'formatted_value' in field:
            self.plan = field['formatted_value']
          elif self.env == 'PROD' and 'formatted_value' in field:
            self.plan = field['formatted_value']
        if (code == 'nsce'):
          self.nsce = field['textval']
        if (code == 'numerotelecoop'):
          self.msisdn = field['textval']
        if (code == 'refbazile'):
          self.bazileNum = field['textval']
        if (code == 'achatsimphysique'):
          if (isinstance(field["boolval"], bool)):
            self.achatSimPhysique = field["boolval"]
          else:
            self.achatSimPhysique = (field['boolval'] == 'Y')
        if (code == 'date-activation-sim-souhaitee' and 'formatted_ymd' in field and field['formatted_ymd'] != ''):
          self.dateActivationSimAsked = datetime.strptime(field['formatted_ymd'], '%Y-%m-%d').astimezone(parisTZ)
        if (code == 'offre-telecommown' and 'formatted_ymd' in field and field['formatted_ymd'] != ''):
          self.optinTeleCommown = datetime.strptime(field['formatted_ymd'], '%Y-%m-%d').astimezone(parisTZ)
        if (code == 'telecommown-date-debut' and 'formatted_ymd' in field and field['formatted_ymd'] != ''):
          self.telecommownStart = datetime.strptime(field['formatted_ymd'], '%Y-%m-%d').astimezone(parisTZ)
        if (code == 'telecommown-date-fin' and 'formatted_ymd' in field and field['formatted_ymd'] != ''):
          self.telecommownEnd = datetime.strptime(field['formatted_ymd'], '%Y-%m-%d').astimezone(parisTZ)
        if (code == 'telecommown-origine'):
          self.telecommownOrigin = field['formatted_value']
        if (code == 'abo-telecommown'):
          if (isinstance(field["boolval"], bool)):
            self.telecommownAbo = field['boolval']
          else:
            self.telecommownAbo = (field['boolval'] == 'Y')
        if (code == 'code-promo'):
          self.promoCode = field['textval']
        if (code == 'parrainage-code-parrain'):
          self.refereeCode = field['textval']
        if (code == 'pack-depannage'):
          self.packDepannage = int(field['numericval'])
        if (code == 'pro-nb-sims'):
          self.proNbSims = int(field['numericval'])
        if (code == 'pro-nb-porta'):
          self.proNbPorta = int(field['numericval'])
        if (code == 'pro-date-engagement' and 'formatted_ymd' in field and field['formatted_ymd'] != ''):
          self.proDateEngagement = datetime.strptime(field['formatted_ymd'], '%Y-%m-%d').astimezone(parisTZ)
        if (code == 'pro-estim-conso'):
          self.proEstimConso = field['textval']
        if (code == 'pro-comment'):
          self.proComment = field['textval']
        if (code == 'pro-nom-utilisateur'):
          self.proNomUtilisateur = field['textval']
        if (code == 'pro-mail-utilisateur'):
          self.proMailUtilisateur = field['textval']
        if (code == 'pro-palier-suspension'):
          try:
            self.proPalierSuspension = int(field['formatted_value'])
          except ValueError:
            self.proPalierSuspension = 150
        if (code == 'pro-appels-internationaux'):
          self.proAppelsInternationaux = field['formatted_value']
        if (code == 'pro-donnees-mobiles'):
          self.proDonneesMobiles = field['formatted_value']
        if (code == 'pro-achats-contenu'):
          self.proAchatContenu = field['boolval']
        if (code == 'pro-achats-surtaxes'):
          self.proAchatsSurtaxes = field['boolval']

    if self.plan in self.plans:
      self.planItem = self.plans[self.plan]

  def updateStep(self, stepId, connector):
    connector.api(method="Opportunities.updateStep", params={'oid': self.id, 'stepid': stepId})
    self.steps[stepId] = datetime.now().astimezone(pytz.timezone('Europe/Paris'))

  def updateStatus(self, status, connector):
    connector.api(method='Opportunities.updateStatus', params={'id': self.id, 'status': status})
    self.status = status

  def isPorta(self):
    return (self.rio is not None and self.rio != 'N/A')

  def isOldBazileLine(self):
    return (self.rio is not None and self.rio[0:2] == '56')

  def getPlanItem(self):
    return self.planItem

  def getSimStateFromStep(self, sellsyConnector):
    sc = sellsyConnector
    state = None
    if self.stepId in [sc.stepNew, sc.stepSimToSend, sc.stepSimToSendTransition]:
      state = 'new'
    elif self.stepId in [sc.stepSimSent, sc.stepSimReceived]:
      state = 'sent'
    elif self.stepId in [sc.stepSimPendingPorta, sc.stepSimPendingNew]:
      state = 'porta'
    elif self.stepId in [sc.stepSimActivated]:
      state = 'active'
    elif self.stepId in [sc.stepSimSuspended]:
      state = 'suspended'
    elif self.stepId in [sc.stepSimTerminated]:
      state = 'terminated'
    return state

class SellsyMemberOpportunity:
  def __init__(self, id):
    env = os.getenv('ENV', 'LOCAL')
    self.env = 'PROD' if env == 'PROD' else 'DEV'

    self.id = id
    self.clientId = None
    self.client = None
    self.prospectId = None
    self.funnelId = None
    self.creationDate = None
    self.stepId = None
    self.stepStart = None
    self.steps = None
    self.status = None
    self.nbShares = None
    self.sharesAmount = None
    self.paymentDate = None
    self.acceptedDate = None

  @property
  def stepName(self):
    return step_name_from_id(self.stepId)

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
    parisTZ = pytz.timezone('Europe/Paris')
    if opp['relationType'] == 'client':
      self.clientId = opp['linkedid']
    else:
      self.prospectId = opp['linkedid']
    self.funnelId = opp['funnelid']
    self.creationDate = parisTZ.localize(datetime.fromisoformat(opp['created']))
    self.status = opp['statusLabel']
    self.stepId = int(opp['stepid'])
    self.stepStart = parisTZ.localize(datetime.fromisoformat(opp['stepEnterDate']))
    self.steps = {opp['stepid']: self.stepStart}

    for fieldId, field in opp['customfields'].items():
      if ('code' in field):
        code = field['code']
        if code == 'partssocialessouhaite':
          self.nbShares = field['numericval']
        elif code == 'montantparts':
          self.sharesAmount = field['numericval']
        elif code == 'dateversementsocietariat' and 'formatted_ymd' in field and field['formatted_ymd'] != '':
          self.paymentDate = parisTZ.localize(datetime.strptime(field['formatted_ymd'], '%Y-%m-%d'))
        elif code == 'dateacceptationsocietariat' and 'formatted_ymd' in field and field['formatted_ymd'] != '':
          self.acceptedDate = parisTZ.localize(datetime.strptime(field['formatted_ymd'], '%Y-%m-%d'))

  def updateStep(self, stepId, connector):
    connector.api(method="Opportunities.updateStep", params={'oid': self.id, 'stepid': stepId})

  def updateStatus(self, status, connector):
    connector.api(method='Opportunities.updateStatus', params={'id': self.id, 'status': status})

  @classmethod
  def getOpportunities(cls, sellsyConnector, logger,
                       startDate=None, search=None, limit=None, searchParams=None, paymentMedium=None):
    result = []
    sc = sellsyConnector
    params = {
      'pagination': {
        'nbperpage': 1000,
        'pagenum': 1
      },
      'search': {
        'funnelid': sc.funnelIdMembership
      }
    }
    if startDate is not None:
      params['search']['periodecreated_start'] = startDate.timestamp()
    if searchParams is not None:
      for k, v in searchParams.items():
        params['search'][k] = v

    opportunities = sc.api(method='Opportunities.getList', params=params)
    infos = opportunities["infos"]
    nbPages = infos["nbpages"]
    currentPage = 1
    while (currentPage <= nbPages):
      logger.info("Processing page {}/{}".format(currentPage, nbPages))
      for id, opp in opportunities['result'].items():
        o = SellsyMemberOpportunity(id)
        o.loadWithValues(opp)
        result.append(o)
        if limit is not None and limit <= len(result):
          return result

      currentPage += 1
      if (infos["pagenum"] <= nbPages):
        params['pagination']['pagenum'] = currentPage
        opportunities = sc.api(method="Opportunities.getList", params=params)
        infos = opportunities["infos"]

    return result


class SellsyInvoice:
  def __init__(self, id):
    env = os.getenv('ENV', 'LOCAL')
    self.env = 'PROD' if env == 'PROD' else 'DEV'

    self.id = id
    self.reference = None
    self.sellsyStatus = None
    self.status = None
    self.amountHT = None
    self.tva = None
    self.amountTTC = None
    self.amountDue = None
    self.paymentDate = None
    self.clientRef = None
    self.subject = None
    self.creationDate = None

    self.rows = None

  def __str__(self):
    display = f"Invoice #{self.id} - {self.reference} {self.sellsyStatus}"
    display += f" : {round(self.amountTTC, 2)} € TTC ({round(self.amountHT, 2)} € HT) | {self.subject}"
    return display

  def load(self, sellsyConnector):
    values = sellsyConnector.getInvoiceValues(self.id)
    self.loadWithValues(values)

  def loadWithValues(self, values):
    parisTZ = pytz.timezone('Europe/Paris')
    self.reference = values['ident']
    self.sellsyStatus = values['status']
    self.status = values['step_id']
    self.amountHT = Decimal(values['totalAmountTaxesFree'])
    self.tva = Decimal(values['taxesAmountSum'])
    self.amountTTC = Decimal(values['totalAmount'])
    self.amountDue = Decimal(values['dueAmount'])
    self.paymentDate = parisTZ.localize(datetime.fromisoformat(values['payDateCustom']))
    self.clientRef = values['thirdident']
    self.subject = values['subject']
    self.payMediums = []
    if values['payMediumsText'] is not None and values['payMediumsText'] != '':
      self.payMediums = [v.decode('utf-8')
                         for k, v in phpserialize.loads(values['payMediumsText'].encode('utf-8')).items()]

    self.creationDate = parisTZ.localize(datetime.fromisoformat(values['created']))

    if 'rows' in values:
      self.rows = values['rows']

  def createPayment(self, paymentDate, amount, sellsyConnector):
    return sellsyConnector.createPayment(self.id, paymentDate, amount)

  def deletePayment(self, paymentId, sellsyConnector):
    sellsyConnector.deletePayment(paymentId, self.id)

  @classmethod
  def getInvoices(cls, sellsyConnector, logger,
                  startDate=None, search=None, limit=None, searchParams=None, paymentMedium=None):
    result = []
    params = {
      'doctype': 'invoice',
      'pagination': {
        'nbperpage': 1000,
        'pagenum': 1
      },
      'search': {
      }
    }
    if startDate is not None:
      params['search']['periodecreationDate_start'] = startDate.timestamp()
    if searchParams is not None:
      for k, v in searchParams.items():
        params['search'][k] = v

    invoices = sellsyConnector.api(method='Document.getList', params=params)
    infos = invoices["infos"]
    nbPages = infos["nbpages"]
    currentPage = 1
    while (currentPage <= nbPages):
      logger.info("Processing page {}/{}".format(currentPage, nbPages))
      for id, invoice in invoices['result'].items():
        i = SellsyInvoice(id)
        i.loadWithValues(invoice)
        if paymentMedium is None or (paymentMedium is not None and paymentMedium in i.payMediums):
          result.append(i)
        if limit is not None and limit <= len(result):
          return result

      currentPage += 1
      if (infos["pagenum"] <= nbPages):
        params['pagination']['pagenum'] = currentPage
        invoices = sellsyConnector.api(method="Document.getList", params=params)
        infos = invoices["infos"]

    return result
