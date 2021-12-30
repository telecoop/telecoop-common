#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, json, pytz
from datetime import datetime, date

from telecoopcommon.sellsy import TcSellsyConnector, SellsyOpportunity, SellsyClient, sellsyValues
from telecoopcommon.telecoop import Connector as TcConnector
from telecoopcommon.cursor import TcCursor

# Script utils
import argparse, configparser

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
                        'update-client',
                        'update-cf',
                        'get-tc-token',
                        'get-code', 'create-code',
                        'get-sponsorship-code',
                        'link-to-referee',
                        'applied-to-referee',
                        'get-updated-opportunities'
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

  def getCursor(self):
    self.logger.debug('connecting to {}'.format(' '.join(self.dbConnStr)))
    conn = psycopg2.connect(' '.join(self.dbConnStr))
    conn.set_session(autocommit=True)
    cursor = conn.cursor()
    tcCursor = TcCursor(cursor, self.logger)
    return tcCursor

  def getBazileConnector(self):
    if (self.connector is None):
      self.connector = bazileAPI.Connector(self.config['BazileAPI'], self.logger)
    return self.connector

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

    if (command == 'get-client'):
      id = self.getArg('Client id')
      client = self.getSellsyConnector().getClient(id)
      print(client)

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
      connector = self.getSellsyConnector()
      stepId = sellsyValues[self.env][step]
      opps = connector.getOpportunitiesInStep(connector.funnelIdVdc, stepId)
      print(len(opps))

    if (command == 'get-client-opportunities'):
      clientId = self.getArg('Client id')
      opps = self.getSellsyConnector().getClientOpportunities(clientId)
      print(opps)

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
