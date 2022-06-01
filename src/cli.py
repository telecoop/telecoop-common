#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import pytz
from datetime import datetime, date

from telecoopcommon.sellsy import TcSellsyConnector, SellsyOpportunity, sellsyValues, SellsyInvoice
from telecoopcommon.telecoop import Connector as TcConnector
from telecoopcommon.bazile import Connector as BazileConnector

# Script utils
import argparse
import configparser

def cmdline():
  parser = argparse.ArgumentParser(description='TeleCoop Common lib client')
  parser.add_argument('--log-level',
                      metavar='LOGLEVEL',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'CONFIG'],
                      default='CONFIG',
                      help='Log level of the script')
  parser.add_argument('command', metavar='COMMAND',
                      choices=[
                        'get-opportunity',
                        'get-client',
                        'get-client-from-ref',
                        'get-clients',
                        'get-opportunities-in-step',
                        'get-client-opportunities',
                        'get-invoice', 'get-invoices', 'update-invoice-status',
                        'update-client',
                        'update-cf',
                        'get-tc-token',
                        'get-code', 'create-code',
                        'get-sponsorship-code',
                        'link-to-referee',
                        'applied-to-referee',
                        'get-updated-opportunities',

                        'bazile-get-conso', 'bazile-get-simple-porta-history',

                        'script',
                      ],
                      help='command')
  parser.add_argument('arguments', metavar='ARGS',
                      nargs='*',
                      help='command arguments')
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

class Runner():
  def __init__(self, env, config, logger, args):
    self.env = env
    self.config = config
    self.logger = logger
    self.args = args

    if (env in ['DEV', 'LOCAL', 'DOCKER']):
      self.confSellsy = config['SellsyDev']
    elif (env == 'PROD'):
      self.confSellsy = config['SellsyProd']

    self.dbConnStr = []
    for cnf in config.items("Bdd"):
      self.dbConnStr.append('{item}={value}'.format(item=cnf[0], value=cnf[1]))

  def getBazileConnector(self):
    return BazileConnector(self.config['BazileAPI'], self.logger)

  def getSellsyConnector(self):
    return TcSellsyConnector(self.confSellsy, self.logger)

  def getTelecoopConnector(self):
    return TcConnector(self.config['TeleCoopApi'], self.logger)

  def getArg(self, name, type='str', help=None):
    if (len(self.args.arguments) == 0):
      message = f"{name} needed"
      if help is not None:
        message += f" {help}"
      self.logger.critical(message)
      sys.exit(1)
    valueStr = self.args.arguments.pop(0)
    if (type == 'date'):
      try:
        value = date.fromisoformat(valueStr)
      except ValueError:
        self.logger.critical(f"{name} (YYYY-MM-DD) needed")
        sys.exit(1)
    elif (type == 'datetime'):
      try:
        value = datetime.fromisoformat(valueStr)
      except ValueError:
        self.logger.critical(f"{name} (YYYY-MM-DD HH-MI-SS) needed")
        sys.exit(1)
    else:
      value = valueStr
    return value

  def run(self, command):
    if (command == 'get-opportunity'):
      id = self.getArg('Opportunity id')
      sellsyConnector = self.getSellsyConnector()
      o = SellsyOpportunity(id)
      o.load(sellsyConnector)
      print(o)
      print(f"{o.stepId} {o.getSimStateFromStep(sellsyConnector)}")
      print(o.getSimStateFromStep(sellsyConnector))

    if (command == 'get-client'):
      id = self.getArg('Client id')
      client = self.getSellsyConnector().getClient(id)
      print(client)
      print(client.member)
      print(client.phoneModel)
      print(client.meanDataUsage)
      print(client.meanMessagesSent)
      print(client.meanVoiceUsage)
      print(client.phoneState)
      print(client.phoneYear)
      print(isinstance(client.telecommownAbo, bool))

    if (command == 'get-client-from-ref'):
      ref = self.getArg('Client ref')
      client = self.getSellsyConnector().getClientFromRef(ref)
      print(client)

    if (command == 'get-clients'):
      clients = self.getSellsyConnector().getClients()
      print(len(clients))
      print(next(iter(clients.values())))

    if (command == 'get-opportunities-in-step'):
      step = self.getArg("Step")
      startDate = None
      if len(self.args.arguments) > 0:
        startDate = self.getArg("Start date", "datetime")
      limit = None
      if len(self.args.arguments) > 0:
        limit = int(self.getArg("Limit"))
      connector = self.getSellsyConnector()
      env = 'PROD' if self.env == 'PROD' else 'DEV'
      stepId = sellsyValues[env][step] if step != 'all' else step
      # searchParams = {'status': ['open', 'won', 'lost', 'late', 'closed']}
      searchParams = None
      opps = connector.getOpportunitiesInStep(connector.funnelIdVdc, stepId,
                                              limit=limit, startDate=startDate, searchParams=searchParams)
      print(len(opps))
      # for opp in opps:
      #   print(f"{opp.id} {opp.planItem}")

    if (command == 'get-client-opportunities'):
      clientId = self.getArg('Client id')
      opps = self.getSellsyConnector().getClientOpportunities(clientId)
      print(opps)

    if (command == 'get-invoice'):
      invoiceId = self.getArg('Invoice id')
      invoice = SellsyInvoice(invoiceId)
      invoice.load(self.getSellsyConnector())
      print(invoice)
      print(invoice.payMediums)

    if (command == 'get-invoices'):
      searchParams = None
      if len(self.args.arguments) > 0:
        invoiceStatus = self.getArg('Invoice status')
        searchParams = {'steps': [invoiceStatus, ]}
      invoices = SellsyInvoice.getInvoices(self.getSellsyConnector(), self.logger, startDate=datetime(
        2022, 1, 1), searchParams=searchParams, paymentMedium='prélèvement')
      print(invoices)

    if (command == 'update-invoice-status'):
      invoiceId = self.getArg('Invoice id')
      status = self.getArg('Status')
      self.getSellsyConnector().updateInvoiceStatus(invoiceId, status)

    if (command == 'update-client'):
      id = self.getArg('Client id')
      prop = self.getArg('Property')
      value = self.getArg('Property value')
      response = self.getSellsyConnector().updateClientProperty(id, prop, value)
      print(response)

    if (command == 'update-cf'):
      env = 'PROD' if self.env == 'PROD' else 'DEV'
      entity = self.getArg('entity')
      id = self.getArg('Entity id')
      customField = self.getArg('Custom field')
      cfid = sellsyValues[env]['custom_fields'][customField]
      value = self.getArg('Value')
      if (value == 'True'):
        value = True
      if (value == 'False'):
        value = False
      response = self.getSellsyConnector().updateCustomField(entity, id, cfid, value)
      print(response)

    if (command == 'get-tc-token'):
      response = self.getTelecoopConnector().getToken()
      print(response.text)

    if (command == 'get-code'):
      code = self.getArg('code')
      response = self.getTelecoopConnector().getCode(code)
      print(response.text)

    if (command == 'create-code'):
      type = self.getArg("code type")
      amount = self.getArg("code amount")
      value = None
      if len(self.args.arguments) > 0:
        value = self.getArg("value")
      response = self.getTelecoopConnector().createCode(value=value, type=type, amount=amount)
      print(response.text)

    if (command == 'get-sponsorship-code'):
      clientRef = self.getArg('Client ref')
      response = self.getTelecoopConnector().getSponsorshipCode(clientRef)
      print(response.text)

    if (command == 'link-to-referee'):
      referee = self.getArg('Referee')
      clientRef = self.getArg('Client ref')
      response = self.getTelecoopConnector().linkToReferee(referee, clientRef)
      print(response.text)

    if (command == 'applied-to-referee'):
      referee = self.getArg('Referee')
      clientRef = self.getArg('Client ref')
      response = self.getTelecoopConnector().appliedToReferee(referee, clientRef)
      print(response.text)

    if (command == 'get-updated-opportunities'):
      startDate = self.getArg("Start date", 'datetime')
      start = pytz.timezone('Europe/Paris').localize(startDate)
      sellsyConnector = self.getSellsyConnector()
      params = {
        'filters': {
          'updated_status': {
            'start': start.isoformat()
          }
        }
      }
      results = sellsyConnector.api2Post('/opportunities/search', params)
      print(json.dumps(results.json(), indent=2))

    if (command == 'bazile-get-conso'):
      accountId = self.getArg("Account id")
      month = self.getArg("Month", "date")
      bazileConnector = self.getBazileConnector()
      print(json.dumps(bazileConnector.getConso(accountId, month.strftime('%Y-%m')), indent=2))

    if (command == 'bazile-get-simple-porta-history'):
      nsce = self.getArg("NSCE")
      bazileConnector = self.getBazileConnector()
      print(json.dumps(bazileConnector.getSimplePortaHistory(nsce), indent=2, default=str))

    if (command == 'script'):
      import scripts
      scripts.initOldTeleCommownClients(self.getSellsyConnector(), self.logger)

def main():
  args = cmdline()

  logger = Logger()

  fileDir = os.path.dirname(os.path.realpath(__file__))
  # Parent directory of this file's directory
  root = os.path.dirname(os.path.dirname(fileDir))
  os.chdir(root)

  env = os.getenv('ENV', 'LOCAL')
  print(env)
  if (env in ['DOCKER', 'PROD', 'TEST']):
    confFile = '/etc/telecoop-common/conf.cfg'
  elif (env is None or env == 'LOCAL'):
    confFile = os.path.join(fileDir, '../conf/conf.cfg')
  if (not os.path.isfile(confFile)):
    raise IOError("{} : file not found".format(confFile))
  config = configparser.ConfigParser()
  config.read(confFile)

  runner = Runner(env, config, logger, args)

  command = args.command

  runner.run(command)


if __name__ == "__main__":
  main()
