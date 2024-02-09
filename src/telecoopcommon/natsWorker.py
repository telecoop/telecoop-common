import asyncio
import signal
from nats.aio.client import Client as NATS


async def worker(natsUrl, topic, queue, handler, logger, connectors={}):
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

    print("Awaiting messages")
    await nCli.subscribe(topic, queue, msgHandler)


def launchWorker(natsUrl, topic, queue, handler, logger, connectors={}):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker(natsUrl, topic, queue, handler, logger, connectors))
    loop.run_forever()
    loop.close()
