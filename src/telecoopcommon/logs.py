# script utils
import logging
import logging.handlers
import os

import datetime as dt


class MillisecondFormatter(logging.Formatter):
    converter = dt.datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s


def getLogLevel(strLevel):
    logLevel = None
    if strLevel == "DEBUG":
        logLevel = logging.DEBUG
    elif strLevel == "INFO":
        logLevel = logging.INFO
    elif strLevel == "WARNING":
        logLevel = logging.WARNING
    elif strLevel == "ERROR":
        logLevel = logging.ERROR
    elif strLevel == "CRITICAL":
        logLevel = logging.CRITICAL

    return logLevel


def initLogs(appName, config, strDesiredLogLevel, consoleOnly=False):
    logLevel = None
    if strDesiredLogLevel == "CONFIG":
        logLevel = getLogLevel(config["log-level"])
    else:
        logLevel = getLogLevel(strDesiredLogLevel)

    logLevel = logLevel or logging.WARNING

    # create logger
    logger = logging.getLogger(appName)
    logger.setLevel(logLevel)

    if not consoleOnly:
        logfile = os.path.join(config["folder"], f"{appName}.log")
        ch = logging.handlers.TimedRotatingFileHandler(logfile, when="D", utc=True)
        ch.setLevel(logLevel)
        # create formatter
        formatter = MillisecondFormatter(
            "[%(asctime)s] %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S.%f"
        )
        # add formatter to ch
        ch.setFormatter(formatter)
        # add ch to logger only if it doesn't exist yet
        if not len(logger.handlers):
            logger.addHandler(ch)

    if config["console"] == "True" or consoleOnly:
        # create console handler and set level to debug
        chOther = logging.StreamHandler()
        chOther.setLevel(logLevel)
        # create formatter
        formatter = MillisecondFormatter(
            "[%(asctime)s] %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S.%f"
        )
        # add formatter to ch
        chOther.setFormatter(formatter)
        # add ch to logger only if it doesn't exist yet
        logger.addHandler(chOther)

    return logger
