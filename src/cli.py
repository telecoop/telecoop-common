#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from telecoopcommon.runner import TcRunner, main

serviceName = "telecoop-common"
defaultPackageName = "telecoopcommon"

"""
modules = {
    "default": defaultPackageName,
    "main": {
        "name": defaultPackageName,
        "excluded": [
            "bazile",
            "runner",
            "cursor",
            "telecoop",
            "logs",
        ],
        "module": telecoopcommon,
    }
}
"""


if __name__ == "__main__":
    main(serviceName, TcRunner, defaultPackageName, additionalCommands=[])
