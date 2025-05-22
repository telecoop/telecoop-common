""" Runner to be used as main entrypoint in TeleCoop backend projects

Put this in manage.py or equivalent :
```
[ … ]
from telecoopcommon.runner import TcRunner, main

[ … ]

serviceName = "my-service" # e.g. telecoop-common
defaultPackageName = "myservice" # e.g. telecoopcommon
# list of names dash style (e.g. test-cmd),
# implemented in Runner class with a camelcasified name (e.g. def testCmd(self))
additionalCommands = []

[ some code ]

if __name__ == "__main__":
    main(serviceName, Runner, defaultPackageName, additionalCommands)
```

And you need this in each of your packages' __init__.py
```
from os.path import dirname, basename, isfile, join
import glob

names = glob.glob(join(dirname(__file__), "*.py"))
modules = [
    basename(f)[:-3] for f in names if isfile(f) and not f.endswith("__init__.py")
]
```
"""
import sys
import os
import importlib
import glob

from . import logs

# import phonenumbers
import traceback
from datetime import datetime, date

from . import modules
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

names = glob.glob(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), '*'))
packages = [os.path.basename(f) for f in names if os.path.isdir(f) and not f.endswith('__pycache__')]


def toCamelCase(text):
    s = text.split("-")
    return s[0] + "".join(t.capitalize() for t in s[1:])


def cmdline(defaultPackageName, additionalCommands=[]):
    parser = argparse.ArgumentParser(description="TeleCoop Invoicing Manager")
    parser.add_argument(
        "--log-level",
        metavar="LOGLEVEL",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "CONFIG"],
        default="CONFIG",
        help="Log level of the script",
    )
    parser.add_argument(
        "--console-only", action="store_true", help="Log only to console"
    )
    parser.add_argument(
        "--no-log", action="store_true", help="Log command to monitoring db"
    )

    parser.add_argument(
        "command",
        metavar="COMMAND",
        choices=[
            f"{module}:{c}" if p == defaultPackageName else f"{p}:{module}:{c}"
            for p in packages
            for module in getattr(importlib.import_module(p), "modules") # {package}.modules defined in __init__.py
            if hasattr(importlib.import_module(f".{module}", p), "commands") # only if module exposes some commands
            for c in getattr(importlib.import_module(f".{module}", p), "commands")
            #for moduleRef, module in modules.items()
            #for p in module["module"].__all__
            #if p not in module["excluded"]
            #for c in getattr(
            #    importlib.import_module(f".{p}", package=module["name"]), "commands"
            #)
        ]
        + additionalCommands,
        help="command",
    )
    parser.add_argument(
        "arguments", metavar="ARGS", nargs="*", help="command arguments"
    )
    return parser.parse_args()


class TcRunner:
    def __init__(self, env, config, logger, args, defaultPackageName):
        self.config = config
        self.logger = logger
        self.args = args
        self.noConfirm = None
        self.postgres = None
        self.defaultPackageName = defaultPackageName
        #self.modules = modules

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
        if self.postgres.__version__[0] == "3":
            conn = self.postgres.connect(
                " ".join(connStr),
                cursor_factory=self.postgres.ClientCursor,
                autocommit=True,
            )
        else:
            conn = self.postgres.connect(" ".join(connStr))
            conn.set_session(autocommit=True)
        cursor = conn.cursor()
        tcCursor = TcCursor(cursor, self.logger)
        tcCursor.execute("SET SESSION timezone = 'Europe/Paris'")
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
            self.logger.warning(f"Command {command} is already running")
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
        else:
            if len(operands) == 2:
                package = self.defaultPackageName
            elif len(operands) == 3:
                package = operands.pop(0)
            moduleName, command = operands

            importName = f"{package}.{moduleName}"
            module = importlib.import_module(importName)
            self.logger.info(f"Executing command {package}.{moduleName}.{command}")
            func = getattr(module, "execute")
            args = [self, command]

        self.execWithLogs(arg, func, noLog, *args)


def main(appName, runnerClass, defaultPackageName, additionalCommands):
    args = cmdline(defaultPackageName, additionalCommands)

    fileDir = os.path.dirname(os.path.realpath(__file__))
    root = fileDir
    #os.chdir(root)

    env = os.getenv("ENV", "LOCAL")
    if env in ["DOCKER", "PROD", "TEST", "LOCAL_PROD"]:
        confFile = f"/etc/{appName}/conf.cfg"
    elif env is None or env in ["DEV", "LOCAL"]:
        confFile = os.path.join("conf/conf.cfg")
    if not os.path.isfile(confFile):
        raise IOError(f"{confFile} : file not found")
    config = configparser.ConfigParser()
    config.read(confFile)

    logger = logs.initLogs(appName, config["Log"], args.log_level, consoleOnly=args.console_only)

    runner = runnerClass(env, config, logger, args, defaultPackageName)

    command = args.command

    runner.execute(command, args.no_log)
