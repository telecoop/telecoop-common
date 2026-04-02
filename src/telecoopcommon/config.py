import configparser
import json
import os


class TcConfig(dict):
    """Works exactly like a dict but provides ways to fill it from files
    or special dictionaries.
    Inspired from Flask config.
    """

    def __init__(self):
        super().__init__({})
        fileDir = os.path.abspath(os.curdir)
        config = configparser.ConfigParser()
        env = os.getenv("ENV", "LOCAL")
        confFile = "conf.cfg"
        if env in ["DOCKER", "PROD", "LOCAL_PROD"]:
            confFile = "/etc/telecoop/conf.cfg"
        elif env is None or env == "LOCAL":
            confFile = os.path.join(fileDir, "conf/conf.cfg")
        elif env == "DEV":
            confFile = os.path.join(fileDir, "conf/conf-dev.cfg")

        if not os.path.isfile(confFile):
            raise IOError("{} : file not found".format(confFile))

        config.read(confFile)
        for key, value in config.items():
            self[key] = value

        # override with prefixed env
        self.from_prefixed_env()

    def from_prefixed_env(self) -> bool:
        """Load any environment variables that start with ``TC_``,
        dropping the prefix from the env key for the config key. Values
        are passed through a loading function to attempt to convert them
        to more specific types than strings.

        Keys are loaded in :func:`sorted` order.

        The default loading function attempts to parse values as any
        valid JSON type, including dicts and lists.

        Specific items in nested dicts can be set by separating the
        keys with double underscores (``__``). If an intermediate key
        doesn't exist, it will be initialized to an empty dict.
        Ex: TC_Bdd_host=localhost will result in config["Bdd"]["host"]=locahost

        """
        prefix = "TC_"

        for key in sorted(os.environ):
            print(key)
            if not key.startswith(prefix):
                continue

            value = os.environ[key]
            key = key.removeprefix(prefix)

            try:
                value = json.loads(value)
            except Exception:
                # Keep the value as a string if loading failed.
                pass

            if "__" not in key:
                # A non-nested key, set directly.
                self[key] = value
                continue

            # Traverse nested dictionaries with keys separated by "__".
            current = self
            *parts, tail = key.split("__")

            for part in parts:
                # If an intermediate dict does not exist, create it.
                if part not in current:
                    current[part] = {}

                current = current[part]

            current[tail] = str(value)

        return True
