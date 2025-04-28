import asyncio
import signal
import json
import inflection
import traceback
import inspect
from nats.aio.client import Client as NATS

class TcNatsConnector():
    def __init__(self, nCli):
        self._nCli = nCli

    async def publish(self, subject: str, data: dict):
        payload = json.dumps(data).encode("utf-8")
        await self._nCli.publish(subject, payload)

    async def request(self, subject: str, data: dict, timeout: int =10):
        payload = json.dumps(data).encode("utf-8")
        response = await self._nCli.request(subject, payload, timeout=timeout)
        result = json.loads(response.data.decode())
        return result

class TcNatsHandler:
    """Generic handler for nats worker
    """
    def __init__(self, data, reply, nCli, connectors, logger):
        self.data = data
        self.reply = reply
        self.response = {"status": "OK"}
        self.nCli = nCli
        self.connectors = connectors
        self.logger = logger

        self.handler = None

    async def handle(self, method):
        self.logger.debug(f"Handler is calling {self.__class__}#{method}")
        try:
            self.response["value"] = getattr(self, method)(**self.data)
        except Exception as excp:
            tbk = traceback.format_exc()
            errorMessage = f"{excp}\n{tbk}"
            self.logger.warning(errorMessage)
            self.response["status"] = "KO"
            self.response["error"] = str(excp)
        if self.reply:
            await self.nCli.publish(self.reply, self.response)

    def listServices(self):
        services = []
        for handler in self.__class__.getHandlers().values():
            rootHandler = handler.__base__.__name__
            topic = inflection.dasherize(inflection.underscore(handler.__name__))
            prefix = f"{rootHandler}.{topic}"
            if rootHandler == "TcNatsWorker":
                rootHandler = handler.__name__
                prefix = f"{rootHandler}"
            for method in [attr for attr in handler.__dict__ if callable(getattr(handler, attr))]:
                if method.startswith("__"):
                    continue
                service = inflection.dasherize(inflection.underscore(method))
                services.append(f"{prefix}.{service}")
        return services

    def getDoc(self, method):
        func = getattr(
            self,
            inflection.camelize(
                inflection.underscore(method), uppercase_first_letter=False
            ),
        )
        sig = inspect.signature(func)
        params = [
            f'"{argName}": {arg.annotation.__name__}'
            for argName, arg in sig.parameters.items()
        ]
        rootHandler = self.__class__.__base__.__name__
        topic = inflection.dasherize(inflection.underscore(self.__class__.__name__))
        returnSig = sig.return_annotation.__name__ if sig.return_annotation else 'None'
        return f"{rootHandler}.{topic}.{method}: {{{','.join(params)}}} -> {returnSig}\n{func.__doc__}"

    @classmethod
    def getHandlers(cls):
        subclasses = {cls.__name__: cls}
        for subclass in cls.__subclasses__():
            subclasses[subclass.__name__] = subclass
            subclasses |= subclass.getHandlers()
        return subclasses

    @classmethod
    def getHandler(cls, handlerName):
        return cls.getHandlers()[handlerName]

    @classmethod
    async def process(cls, subject, rawData, reply, connectors, nCli, logger):
        splits = subject.split(".")
        topic = splits.pop(0)
        objectType = splits.pop(0)
        if len(splits) > 0:
            eventType = splits.pop(0)
        else:
            eventType = objectType
            objectType = topic
        data = json.loads(rawData)
        
        logger.debug(f"Received message on {topic} > {eventType} : {data}")
        handlerName = cls.getHandlerName(objectType)
        method = cls.getMethodName(eventType)
        handler = cls.getHandler(handlerName)(data, reply, nCli, connectors, logger)
        await handler.handle(method)

    @classmethod
    def getHandlerName(cls, objectType):
        # need to first switch to _ before camelCase … go figure
        return inflection.camelize(inflection.underscore(objectType))

    @classmethod
    def getMethodName(cls, eventType):
        # need to first switch to _ before camelCase … go figure
        return inflection.camelize(inflection.underscore(eventType), uppercase_first_letter=False)

async def worker(natsUrl, topic, queue, handler, logger, connectors={}, cred=None):
    nCli = NATS()

    async def stop():
        await asyncio.sleep(1)
        asyncio.get_running_loop().stop()

    def signalHandler():
        if nCli.is_closed:
            return
        print("Disconnecting...")
        asyncio.create_task(nCli.close())
        asyncio.create_task(stop())

    for sig in ("SIGINT", "SIGTERM"):
        asyncio.get_running_loop().add_signal_handler(
            getattr(signal, sig), signalHandler
        )

    async def disconnectedCb():
        print("Got disconnected...")

    async def reconnectedCb():
        print("Got reconnected...")

    await nCli.connect(
        natsUrl,
        user_credentials=cred,
        reconnected_cb=reconnectedCb,
        disconnected_cb=disconnectedCb,
        max_reconnect_attempts=-1,
    )

    async def msgHandler(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        logger.info(f"Received message {subject} {reply} - {data}")
        await handler(subject, data, reply, connectors, TcNatsConnector(nCli), logger)

    logger.info("Awaiting messages")
    await nCli.subscribe(topic, queue, msgHandler)


def launchWorker(natsUrl, topic, queue, handler, logger, connectors={}, cred=None):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        worker(natsUrl, topic, queue, handler, logger, connectors, cred)
    )
    loop.run_forever()
    loop.close()


async def publish(getNCli, channel, message):
    nCli = await getNCli()

    await nCli.publish(subject=channel, data=message)


async def request(getNCli, channel, message):
    nCli = await getNCli()

    response = await nCli.request(subject=channel, data=message)

    print(response)


async def testHandler(subject: str, dataRaw: str, reply: str, connectors: dict, nCli: NATS, logger):
    splits = subject.split(".")
    topic = splits.pop(0)
    eventType = splits.pop(0)
    data = json.loads(dataRaw)

    logger.info(f"Received message on {topic} > {eventType} : {data}")

    if reply:
        await nCli.publish(reply, data)
    

# Commands
commands = {
    "publish": lambda runner: asyncio.run(
        publish(
            runner.getNatsConnection, runner.getArg("channel"), runner.getArg("message")
        )
    ),
    "request": lambda runner: asyncio.run(
        request(
            runner.getNatsConnection, runner.getArg("channel"), runner.getArg("message")
        )
    ),
    "run-test": lambda runner: launchWorker(
        runner.config["Nats"]["url"],
        "test.>",
        "workers",
        testHandler,
        runner.logger,
        connectors={},
        cred=runner.config["Nats"]["cred"] if "cred" in runner.config["Nats"] else None,
    ),
}


def execute(runner, command):
    if command in commands:
        commands[command](runner)
