import asyncio
import time
from datetime import datetime

from tortoise import Tortoise

from core.settings import settings, create_logger
from core.utils import qm_context
from core.models import Calendar

logger = create_logger("DEBUG")


def wait_for_zero_sec():
    logger.info("Waiting for second 0")
    now = datetime.now()
    while now.second != 0:
        now = datetime.now()
        time.sleep(0.5)


async def init():
    logger.info("Initialization")
    await Tortoise.init(db_url=settings.db_url, modules={"models": ["core.models"]})


async def process_queues():
    logger.info("Processing queues")
    async with qm_context() as qm:
        await qm.open_queues()
        await asyncio.gather(
            *[qm.update_queues(calendar) async for calendar in Calendar.all()]
        )


if __name__ == "__main__":
    try:
        logger.info("Starting loop")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(init())

        while True:
            loop.create_task(process_queues())
            time.sleep(1)
            wait_for_zero_sec()
    finally:
        logger.info("Shutting down")
        loop.run_until_complete(Tortoise.close_connections())
        loop.close()
