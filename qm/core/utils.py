from asyncio import events
from datetime import date, datetime
import asyncio
from typing import Dict, List, Any


from .models import Calendar, Event
from .google import GCalendar, GScript
from .settings import settings


class QueuesManager:
    __slots__ = ('_calendar_service', '_scripts_service', '_calendar', '_events',
                 '_new_events', '_deleted_events', '_old_events')

    def __init__(self):
        self._calendar_service = GCalendar(creds_path=settings.google_creds_path,
                                           scopes=settings.google_calendar_scopes)

        self._scripts_service = GScript(creds_path=settings.google_creds_path,
                                        scopes=settings.google_script_scopes)

        self._calendar: Calendar
        self._events: Dict[str, Dict[str, Any]]

        self._new_events: List[str]
        self._deleted_events: List[str]
        self._old_events: List[str]

    async def clear(self):
        await self._calendar_service._httpsession.close()
        await self._scripts_service._httpsession.close()

    async def open_queues(self):
        now = datetime.now().replace(second=0, microsecond=0)
        events = await Event.filter(open_at=now, opened=False)

        await asyncio.gather(*[self.open_form(event) for event in events])

    async def open_form(self, event: Event):
        await self._scripts_service.open_form(event.form_id)
        event.opened = True
        await event.save()

    async def update_queues(self, calendar_id: str) -> None:
        self._calendar = await Calendar.get(google_id=calendar_id)

        events_gen = self._calendar_service.get_events(calendar_id)
        self._events = {event['id']: event async for event in events_gen}

        # Create sets of ids
        db_events = {event.google_id async for event in self._calendar.events}
        calendar_events = set(self._events.keys())

        # sets operations
        self._new_events = calendar_events - db_events
        self._deleted_events = db_events - calendar_events
        self._old_events = calendar_events & db_events

        # FANOUT
        await asyncio.gather(
            asyncio.gather(*[self.process_new(event_id)
                             for event_id in self._new_events]),

            asyncio.gather(*[self.process_deleted(event_id)
                             for event_id in self._deleted_events]),

            asyncio.gather(*[self.process_old(event_id)
                             for event_id in self._old_events])
        )

    async def process_new(self, event_id: str) -> None:
        event = self._events[event_id]
        open_at = self.parse_datetime(event['start']['dateTime'])

        form_id = await self.create_queue(event_id, event['summary'])

        await Event.create(google_id=event_id, open_at=open_at, created=True,
                           calendar_id=self._calendar.id, form_id=form_id)

    async def process_deleted(self, event_id: str) -> None:
        await Event.get(google_id=event_id).delete()

    async def process_old(self, event_id: str) -> None:
        event = self._events[event_id]

        updated_at = self.parse_datetime(event['updated'])
        if datetime.now().date() != updated_at.date():
            return

        db_event = await Event.get(google_id=event_id)
        if db_event.opened:
            return

        db_event.open_at = self.parse_datetime(event['start']['dateTime'])
        await db_event.save()

    async def create_queue(self, event_id: str, event_name: str) -> None:
        editors = self._calendar_service.get_editors(self._calendar.id)
        editors = [editor async for editor in editors]

        res = await self._scripts_service.create_form(event_name, editors, 'Имя')
        form_url = res['formUrl']
        form_id = res['formId']
        spreadsheet_url = res['spreadsheetUrl']

        await self._calendar_service.add_attachment(self._calendar.google_id, event_id, form_url, spreadsheet_url)

        return form_id

    @staticmethod
    def parse_datetime(date_time: str, format: str = '%Y-%m-%dT%H:%M:%S+03:00') -> datetime:
        return datetime.strptime(date_time, format)
