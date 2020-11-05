from datetime import date, datetime
import asyncio
from typing import Dict, List, Union

from aiohttp import ClientSession
import ujson

from .models import Calendar, Event
from .google_apis.calendarAPI import GCalendar
from .google_apis.scriptAPI import GScript

calendar_service = GCalendar(creds_path='creds/credentials.json',
                             token_path='creds/tokenCalendar.pickle',
                             scopes='https://www.googleapis.com/auth/calendar')

scripts_service = GScript(creds_path='creds/credentials.json',
                          token_path='creds/tokenScripts.pickle',
                          scopes=['https://www.googleapis.com/auth/script.projects',
                                  "https://www.googleapis.com/auth/forms",
                                  "https://www.googleapis.com/auth/spreadsheets",
                                  "https://www.googleapis.com/auth/drive"])


class EventsProcessor:
    def __init__(self):
        # TODO: create services instances per processor
        # Check tokens inside them
        self.calendar_service: GCalendar = calendar_service
        self.scripts_service: GScript = scripts_service

        # TODO: place httpSession in Google
        # now it is closing in methods
        # self.httpsession = ClientSession(json_serialize=ujson.dumps)

        self.calendar: Calendar
        self.events: Dict[str, Dict[str, Union[str, int, bool]]]

        self.new_events: List[str]
        self.deleted_events: List[str]
        self.old_events: List[str]

    # Would be amazing to use __call__,
    # but fastapi.BackgroundTasks throws error
    # TODO: try to make it __call__
    async def process(self, calendar_id: str) -> None:
        self.calendar = await Calendar.get(google_id=calendar_id)

        self.events = self.calendar_service.get_events(calendar_id)
        self.events = {event['id']: event async for event in self.events}

        # Create sets of ids
        db_events = {event.google_id async for event in self.calendar.events}
        calendar_events = set(self.events.keys())

        # sets operations
        self.new_events = calendar_events - db_events
        self.deleted_events = db_events - calendar_events
        self.old_events = calendar_events & db_events

        # FANOUT
        await asyncio.gather(
            asyncio.gather(*[self.process_new(event_id)
                             for event_id in self.new_events]),

            asyncio.gather(*[self.process_deleted(event_id)
                             for event_id in self.deleted_events]),

            asyncio.gather(*[self.process_old(event_id)
                             for event_id in self.old_events])
        )

    async def process_new(self, event_id: str) -> None:
        event = self.events[event_id]
        open_at = self.parse_datetime(event['start']['dateTime'])

        await self.create_queue(event_id, event['summary'])

        await Event.create(google_id=event_id, open_at=open_at, created=True,
                           calendar_id=self.calendar.id)

    async def process_deleted(self, event_id: str) -> None:
        await Event.get(google_id=event_id).delete()

    async def process_old(self, event_id: str) -> None:
        event = self.events[event_id]

        # TODO: might be bugs, make better
        if date.today().isoformat() != event['updated'].split('T')[0]:
            return

        db_event = await Event.get(google_id=event_id)

        if db_event.opened:
            return

        db_event.open_at = self.parse_datetime(event['start']['dateTime'])
        await db_event.save()

    async def create_queue(self, event_id: str, event_name: str) -> None:
        editors = self.calendar_service.get_editors(
            self.calendar.id)
        editors = [editor async for editor in editors]

        res = await self.scripts_service.create_form(event_name, editors, 'Имя')
        form_url = res['formUrl']
        spreadsheet_url = res['spreadsheetUrl']

        await self.calendar_service.add_attachment(self.calendar.id, event_id, form_url, spreadsheet_url)

    @staticmethod
    def parse_datetime(date_time: str, format: str = '%Y-%m-%dT%H:%M:%S+03:00') -> datetime:
        return datetime.strptime(date_time, format)
