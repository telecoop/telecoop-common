from datetime import date, datetime

def initOldTeleCommownClients(sellsyConnector, logger):
  clients = sellsyConnector.getClients()

  for _, client in clients.items():
    if client.telecommownAbo is not None and client.telecommownAbo:
      logger.info(f"Found client {client.reference} #{client.id}")
      opportunities = client.getOpportunities(sellsyConnector)
      opp = None
      for o in opportunities:
        if str(sellsyConnector.stepSimActivated) in o.steps:
          opp = o
          break
      if opp is not None:
        logger.info(f"Applying to opportunity #{opp.id}")
        sellsyConnector.updateCustomField('opportunity', opp.id, sellsyConnector.cfIdTeleCommownDateDebut, datetime(year=2022, month=1, day=1).timestamp())

# Création de champs personnalisés
def createCustomField(sellsyConnector):
  data = {
        'Admin': [
          'demande code messagerie',
          'demande code PIN',
          'demande code PUK',
          'envoi doc pro',
          'envoi RIB',
          'modif adresse mail',
          'modif adresse postale',
          'modif coordonnées bancaires',
          'pb code RIO',
          'pb pièce identité',
        ],
        'Communication': [
          'communication',
          'autre'
        ],
        'Facturation': [
          'achat de contenu',
          'dépassement HF',
          'rejet paiement',
          'suivi conso',
        ],
        'Info offre': [
          'BtoB',
          'FAI internet',
          'format carte SIM',
          'option appels wifi',
          'option multi SIM',
          'pack dépannage',
          'parrainage',
          'tarifs',
          'tarifs internationaux',
          'TeleCommown',
        ],
        'Info process': [
          'portabilité',
          'résiliation',
        ],
        'Partenariat & Média': [
          'Partenariat & Média',
          'autre'
        ],
        'RH': [
          'candidature',
          'autre'
        ],
        'Souscription': [
          'pack dépannage',
          'pb code RIO',
          'pb enregistrement SIM',
          'pb lien souscription',
          'pb mandat',
          'pb paiement CB',
          'retard réception SIM',
          'TeleCommown',
        ],
        'Technique': [
          'pb carte SIM',
          'pb couverture',
          'pb portabilité',
          'pb réseau',
          'pb réseau suite activation',
        ],
        'Vie du contrat': [
          'blocage option SVA',
          'blocage option WHA',
          'désactivation data',
          'désactivation international',
          'désactivation messagerie',
          'perte téléphone ou SIM',
          'résiliation',
          'rétractation',
          'vol téléphone',
        ],
        'Vie numérique': [
          'espace personnel',
          'messagerie',
          'pb accès espace personnel',
          'pb config data',
          'suivi conso',
          'transfert contacts',
        ]
      }
  for name, fields in data.items():
    params = {
      'type': 'checkbox',
      'name': name,
      'code': name.lower().replace(' ', '-'),
      'useOn': ['useOn_ticket'],
      'preferences': {
        'isRequired': 'N',
      },
      'preferenceslist': []
    }
    for f in fields:
      params['preferenceslist'].append({
        'value': f
      })
    sellsyConnector.api(method="CustomFields.create", params=params)
