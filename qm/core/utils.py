from sqlalchemy import select

from .database import database
from .models import events_table, calendars_table


async def get_all_calendars():
    query = (
        select(
            [
                calendars_table.c.id,
                calendars_table.c.google_id,
                calendars_table.c.webhook_channel,
            ]
        )
    )
    return await database.fetch_all(query)


async def get_all_events():
    query = (
        select(
            [
                events_table.c.id,
                events_table.c.google_id,
                events_table.c.open_at,
                events_table.c.created,
                events_table.c.opened,
                events_table.c.calendar_id
            ]
        )
    )
    return await database.fetch_all(query)
