import asyncio
import signal
import json
from nats.aio.client import Client as NATS


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
        await handler(subject, data, reply, connectors, nCli, logger)

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

    await nCli.publish(channel, json.dumps(json.loads(message)).encode("utf-8"))


# Commands
commands = {
    "publish": lambda runner: asyncio.run(
        publish(
            runner.getNatsConnection, runner.getArg("channel"), runner.getArg("message")
        )
    )
}


def execute(runner, command):
    if command in commands:
        commands[command](runner)
