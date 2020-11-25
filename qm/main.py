import asyncio
import time
from datetime import datetime

from tortoise import Tortoise
import aioschedule

from core.settings import settings, create_logger
from core.utils import qm_context
from core.models import Calendar

logger = create_logger("DEBUG")


async def process_queues():
    logger.info("Processing queues")
    async with qm_context() as qm:
        await qm.open_queues()
        await asyncio.gather(
            *[qm.update_queues(calendar) async for calendar in Calendar.all()]
        )


async def init():
    logger.info("Initialization")
    await Tortoise.init(db_url=settings.db_url, modules={"models": ["core.models"]})
    aioschedule.every().minute.do(process_queues)

def wait_for_zero_sec():
    now = datetime.now()
    while now.second != 0:
        now = datetime.now()
        time.sleep(0.5)

if __name__ == "__main__":
    logger.info("Waiting for second 0")
    wait_for_zero_sec() 

    loop = asyncio.get_event_loop()
    loop.run_until_complete(init())
    loop.run_until_complete(process_queues())

    try:
        logger.info("Starting loop")
        while True:
            loop.run_until_complete(aioschedule.run_pending())
            time.sleep(0.1)
    finally:
        logger.info("Shutting down")
        loop.run_until_complete(Tortoise.close_connections())
