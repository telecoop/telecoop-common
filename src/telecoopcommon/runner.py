import sys
import os
import importlib

from . import logs

# import phonenumbers
import traceback
from datetime import datetime, date

from .cursor import TcCursor

# Script utils
import argparse
import configparser

""" Exemple
modules = {
    "paymentProvider": {
        "name": "payment",
        "excluded": [],
        "main": False,
        "module": payment,
    },
    "factu": {
        "name": "facturation",
        "excluded": [],
        "main": True,
        "module": facturation,
    },
}

additionalCommands = ['test', 'my-special-command']
"""


def toCamelCase(text):
    s = text.split("-")
    return s[0] + "".join(t.capitalize() for t in s[1:])


def cmdline(modules, additionalCommands=[]):
    parser = argparse.ArgumentParser(description="TeleCoop Invoicing Manager")
    parser.add_argument(
        "--log-level",
        metavar="LOGLEVEL",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "CONFIG"],
        default="CONFIG",
        help="Log level of the script",
    )
    parser.add_argument(
        "--no-log", action="store_true", help="Log command to monitoring db"
    )

    parser.add_argument(
        "command",
        metavar="COMMAND",
        choices=[
            f"{p}:{c}" if moduleRef == "main" else f"{moduleRef}.{c}"
            for moduleRef, module in modules.items()
            for p in module["module"].__all__
            if p not in module["excluded"]
            for c in getattr(
                importlib.import_module(f".{p}", package=module["name"]), "commands"
            )
        ]
        + additionalCommands,
        help="command",
    )
    parser.add_argument(
        "arguments", metavar="ARGS", nargs="*", help="command arguments"
    )
    return parser.parse_args()


class TcRunner:
    def __init__(self, env, config, logger, args, modules):
        self.config = config
        self.logger = logger
        self.args = args
        self.noConfirm = None
        self.postgres = None
        self.modules = modules

        self.env = "PROD" if env == "PROD" else "DEV"

        self.dbConnStrs = {}

        for section in config.sections():
            if section[0:3] == "Bdd":
                connName = section[3:].lower() if section[3:] else "main"
                connStr = []
                for cnf in config.items(section):
                    connStr.append(f"{cnf[0]}={cnf[1]}")
                self.dbConnStrs[connName] = connStr

    def getArg(self, name, type="str", help=None):
        if len(self.args.arguments) == 0:
            message = f"{name} needed"
            if help is not None:
                message += f" {help}"
            self.logger.critical(message)
            sys.exit(1)
        valueStr = self.args.arguments.pop(0)
        if type == "date":
            try:
                value = date.fromisoformat(valueStr)
            except ValueError:
                self.logger.critical(f"{name} (YYYY-MM-DD) needed")
                sys.exit(1)
        elif type == "int":
            try:
                value = int(valueStr)
            except ValueError:
                self.logger.critical(f"{name} int needed")
                sys.exit(1)
        elif type == "datetime":
            try:
                value = datetime.fromisoformat(valueStr)
            except ValueError:
                self.logger.critical(f"{name} (YYYY-MM-DD HH-MI-SS) needed")
                sys.exit(1)
        elif type == "bool":
            value = valueStr == "true"
        else:
            value = valueStr
        return value

    def getCursor(self, db="main"):
        connStr = self.dbConnStrs[db]
        self.logger.debug(f"Connection to {' '.join(connStr)}")
        conn = self.postgres.connect(" ".join(connStr))
        conn.set_session(autocommit=True)
        cursor = conn.cursor()
        tcCursor = TcCursor(cursor, self.logger)
        tcCursor.execute("SET SESSION timezone = 'CET'")
        return tcCursor

    def confirm(self, question="Confirm ?"):
        if self.noConfirm is None:
            self.noConfirm = False
        answered = False
        confirmed = None
        if not self.noConfirm:
            while not answered:
                text = input(f"{question} [Y/n/a]: ")
                if text in ["Y", "", "n", "a"]:
                    answered = True
                    confirmed = not text == "n"
                    if text == "a":
                        self.noConfirm = True
        else:
            confirmed = True

        return confirmed

    def execWithLogs(self, command, func, noLog, *args, **kargs):
        cursorLogs = self.getCursor("logs")
        # checking if command is already running
        query = "SELECT count(*) FROM monitoring.service_log WHERE service_name = %s AND status = 'pending'"
        cursorLogs.execute(query, [command])
        (nbRunningServices,) = cursorLogs.fetchone()
        if nbRunningServices > 0:
            self.logger.warning("Invoicing process already running")
            return

        if not noLog:
            cursorLogs.execute(
                "INSERT INTO monitoring.service_log (service_name, status) VALUES (%s, 'pending') RETURNING id",
                [
                    command,
                ],
            )
            (logId,) = cursorLogs.fetchone()
        try:
            func(*args, **kargs)
        except Exception as excp:
            tbk = traceback.format_exc()
            errorMessage = f"{excp}\n{tbk}"
            query = """
              UPDATE monitoring.service_log
                 SET end_date = now(),
                     status = 'error',
                     error_message = %s
               WHERE id = %s
            """
            if not noLog:
                cursorLogs.execute(query, [errorMessage, logId])
            raise excp
        if not noLog:
            cursorLogs.execute(
                "UPDATE monitoring.service_log SET end_date = now(), status = 'OK' WHERE id = %s",
                [
                    logId,
                ],
            )

    def execute(self, arg, noLog=False):
        operands = arg.split(":")
        module = None
        command = None
        func = None
        args = []
        if len(operands) == 1:
            command = toCamelCase(operands[0])
            if hasattr(self, command):
                self.logger.info(f"Executing command {command}")
                func = getattr(self, command)
                args = []
                # func(self)
        elif len(operands) == 2:
            module, command = operands
            key = module
            if module not in self.modules:
                key = "main"

            moduleName = f"{self.modules[key]['name']}.{module}"
            mName = importlib.import_module(moduleName)
            self.logger.info(f"Executing command {moduleName}.{command}")
            func = getattr(mName, "execute")
            args = [self, command]

        self.execWithLogs(arg, func, noLog, *args)


def main(appName, runnerClass, modules, additionalCommands):
    args = cmdline(modules, additionalCommands)

    fileDir = os.path.dirname(os.path.realpath(__file__))
    root = fileDir
    os.chdir(root)

    env = os.getenv("ENV", "LOCAL")
    if env in ["DOCKER", "PROD", "TEST", "LOCAL_PROD"]:
        confFile = f"/etc/{appName}/conf.cfg"
    elif env is None or env == "LOCAL":
        confFile = os.path.join(fileDir, "../conf/conf.cfg")
    if not os.path.isfile(confFile):
        raise IOError(f"{confFile} : file not found")
    config = configparser.ConfigParser()
    config.read(confFile)

    logger = logs.initLogs(appName, config["Log"], args.log_level)

    runner = runnerClass(env, config, logger, args, modules)

    command = args.command

    runner.execute(command, args.no_log)
