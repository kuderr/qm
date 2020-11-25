from datetime import datetime
import asyncio
import logging
from typing import Dict, List, Any
from contextlib import asynccontextmanager


from .models import Calendar, Event
from .google import GCalendar, GScript
from .settings import settings

logger = logging.getLogger("qm")


@asynccontextmanager
async def qm_context():
    qm = QueuesManager()
    try:
        yield qm
    finally:
        await qm.clear()


class QueuesManager:
    __slots__ = (
        "_calendar_service",
        "_scripts_service",
        "_calendar",
        "_events",
        "_new_events",
        "_deleted_events",
        "_old_events",
    )

    def __init__(self):
        self._calendar_service = GCalendar(
            creds_path=settings.google_creds_path,
            scopes=settings.google_calendar_scopes,
        )

        self._scripts_service = GScript(
            creds_path=settings.google_creds_path, scopes=settings.google_script_scopes
        )

        self._calendar: Calendar
        self._events: Dict[str, Dict[str, Any]]

        self._new_events: List[str]
        self._deleted_events: List[str]
        self._old_events: List[str]

    async def clear(self):
        await self._calendar_service._httpsession.close()
        await self._scripts_service._httpsession.close()

    async def open_queues(self):
        now = datetime.now().replace(second=0, microsecond=0).timestamp()
        events = await Event.filter(open_at_ts=now, opened=False)
        await asyncio.gather(*[self.open_form(event) for event in events])

    async def open_form(self, event: Event):
        logger.info(f"Opening queue for {event.google_id}")
        await self._scripts_service.open_form(event.form_id)
        event.opened = True
        await event.save()

    async def update_queues(self, calendar: Calendar) -> None:
        self._calendar = calendar

        events_gen = self._calendar_service.get_events(self._calendar.google_id)
        self._events = {event["id"]: event async for event in events_gen}

        # Create sets of ids
        db_events = {event.google_id async for event in self._calendar.events}
        calendar_events = set(self._events.keys())

        # sets operations
        self._new_events = calendar_events - db_events
        self._deleted_events = db_events - calendar_events
        self._old_events = calendar_events & db_events

        # FANOUT
        await asyncio.gather(
            asyncio.gather(
                *[self.process_new(event_id) for event_id in self._new_events]
            ),
            asyncio.gather(
                *[self.process_deleted(event_id) for event_id in self._deleted_events]
            ),
            asyncio.gather(
                *[self.process_old(event_id) for event_id in self._old_events]
            ),
        )

    async def process_new(self, event_id: str) -> None:
        event = self._events[event_id]
        event_name = event["summary"]

        logger.info(f"Creating queue for Event {event_id}: {event_name}")

        open_at_ts = self.parse_datetime(event["start"]["dateTime"])
        form_id = await self.create_queue(event_id, event_name)

        await Event.create(
            google_id=event_id,
            open_at_ts=open_at_ts,
            created=True,
            calendar_id=self._calendar.id,
            form_id=form_id,
        )

    async def process_deleted(self, event_id: str) -> None:
        logger.info(f"Deleting Event {event_id}")
        await Event.get(google_id=event_id).delete()

    async def process_old(self, event_id: str) -> None:
        event = self._events[event_id]

        updated_at = self.parse_datetime(event["updated"])
        if datetime.now().date() != datetime.fromtimestamp(updated_at).date():
            return

        db_event = await Event.get(google_id=event_id)
        if db_event.opened:
            return

        event_start = self.parse_datetime(event["start"]["dateTime"])
        if db_event.open_at_ts != event_start:
            logger.info(f"Updating queue for Event {event_id}")
            db_event.open_at_ts = event_start
            await db_event.save()

    async def create_queue(self, event_id: str, event_name: str) -> None:
        editors = self._calendar_service.get_editors(self._calendar.id)
        editors = [editor async for editor in editors]

        res = await self._scripts_service.create_form(event_name, editors, "Имя")
        form_url = res["formUrl"]
        form_id = res["formId"]
        spreadsheet_url = res["spreadsheetUrl"]

        await self._calendar_service.add_attachment(
            self._calendar.google_id, event_id, form_url, spreadsheet_url
        )

        return form_id

    @staticmethod
    def parse_datetime(date_time: str) -> int:
        return int(datetime.fromisoformat(date_time.replace("Z", "+00:00")).timestamp())
