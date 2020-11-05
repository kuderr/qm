from datetime import datetime
import os
import uuid
from typing import Generator, Dict, Union, List

from aiohttp import ClientSession
import ujson

from .mixins import GoogleMixin
from ..settings import settings


class GCalendar(GoogleMixin):
    API_URL = 'https://www.googleapis.com/calendar/v3'
    QM_WEBHOOK_URL = settings.webhook_url

    # Generator[YieldType, SendType, ReturnType]
    async def get_editors(self, calendar_id: str, *, session: ClientSession = None) -> Generator[str, None, None]:
        if session is None:
            session = ClientSession()

        page_token = ''

        async with session:
            while page_token != False:
                resp = await session.get(f'{self.API_URL}/calendars/{calendar_id}/acl?pageToken={page_token}',
                                         headers=self._headers,
                                         ssl=False)
                async with resp:
                    resp_json = await resp.json()

                acls = resp_json.get('items', [])
                page_token = resp_json.get('nextPageToken', False)

                for acl in acls:
                    if acl['role'] == 'writer':
                        yield acl['scope']['value']

    async def get_my_calendars(self, *, session: ClientSession = None) -> Generator[Dict[str, Union[str, bool, int]], None, None]:
        if session is None:
            session = ClientSession()

        page_token = ''

        async with session:
            while page_token != False:
                resp = await session.get(f'{self.API_URL}/users/me/calendarList?pageToken={page_token}',
                                         headers=self._headers,
                                         ssl=False)
                async with resp:
                    resp_json = await resp.json()

                calendars = resp_json.get('items', [])
                page_token = resp_json.get('nextPageToken', False)

                for calendar in calendars:
                    if calendar.get('primary'):
                        continue

                    if calendar['accessRole'] == 'owner':
                        yield calendar

    async def get_events(self, calendar_id: str, *, session: ClientSession = None) -> Generator[Dict[str, Union[str, bool, int]], None, None]:
        if session is None:
            session = ClientSession()

        page_token = ''

        params = {
            "timeMin": datetime.utcnow().isoformat() + 'Z',  # 'Z' indicates UTC time
            "singleEvents": 'true',
            "orderBy": "startTime"
        }

        async with session:
            while page_token != False:
                resp = await session.get(f'{self.API_URL}/calendars/{calendar_id}/events?pageToken={page_token}',
                                         headers=self._headers, params=params,
                                         ssl=False)
                async with resp:
                    resp_json = await resp.json()

                events = resp_json.get('items', [])
                page_token = resp_json.get('nextPageToken', False)

                for event in events:
                    yield event

    async def add_attachment(self, calendar_id: str, event_id: str, form_url: str, spreadsheet_url: str, *, session: ClientSession = None) -> None:
        if session is None:
            session = ClientSession(json_serialize=ujson.dumps)

        changes = {
            'attachments': [
                {
                    "fileUrl": form_url,
                    "title": "Форма"
                }, {
                    "fileUrl": spreadsheet_url,
                    "title": "Таблица"
                }
            ]
        }

        params = {'supportsAttachments': 'true'}

        async with session:
            resp = await session.patch(f'{self.API_URL}/calendars/{calendar_id}/events/{event_id}',
                                       headers=self._headers, json=changes, params=params,
                                       ssl=False)
            resp.close()

    async def event_watch(self, calendar_id: str, *, session: ClientSession = None) -> Dict[str, str]:
        if session is None:
            session = ClientSession(json_serialize=ujson.dumps)

        body = {
            'id': uuid.uuid4().hex,
            'type': "web_hook",
            'address': self.QM_WEBHOOK_URL
        }

        async with session:
            resp = await session.post(f'{self.API_URL}/calendars/{calendar_id}/events/watch',
                                      json=body, headers=self._headers, ssl=False)
            async with resp:
                return await resp.json()

    async def event_watch_stop(self, id: str, resource_id: str, *, session: ClientSession = None) -> None:
        if session is None:
            session = ClientSession(json_serialize=ujson.dumps)

        body = {
            'id': id,
            'resourceId': resource_id
        }

        async with session:
            resp = await session.post(f'{self.API_URL}/channels/stop',
                                      json=body, headers=self._headers, ssl=False)
            resp.close()
