from datetime import datetime
import uuid
from typing import AsyncGenerator, Dict, Any

from ..decorators import token_check
from .mixins import GoogleMixin
from ..settings import settings


class GCalendar(GoogleMixin):
    API_URL = 'https://www.googleapis.com/calendar/v3'
    QM_WEBHOOK_URL = settings.webhook_url

    # AsyncGenerator[YieldType, SendType]
    @token_check('gen')
    async def get_editors(self, calendar_id: str) -> AsyncGenerator[str, None]:
        page_token = ''

        while page_token != False:
            resp = await self._httpsession.get(f'{self.API_URL}/calendars/{calendar_id}/acl?pageToken={page_token}',
                                               headers=self._headers,
                                               ssl=False)
            async with resp:
                resp_json = await resp.json()

            acls = resp_json.get('items', [])
            page_token = resp_json.get('nextPageToken', False)

            for acl in acls:
                if acl['role'] == 'writer':
                    yield acl['scope']['value']

    @token_check('gen')
    async def get_my_calendars(self) -> AsyncGenerator[Dict[str, Any], None]:
        page_token = ''

        while page_token != False:
            resp = await self._httpsession.get(f'{self.API_URL}/users/me/calendarList?pageToken={page_token}',
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

    @token_check('gen')
    async def get_events(self, calendar_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        page_token = ''

        params = {
            "timeMin": datetime.utcnow().isoformat() + 'Z',  # 'Z' indicates UTC time
            "singleEvents": 'true',
            "orderBy": "startTime"
        }

        while page_token != False:
            resp = await self._httpsession.get(f'{self.API_URL}/calendars/{calendar_id}/events?pageToken={page_token}',
                                               headers=self._headers, params=params,
                                               ssl=False)
            async with resp:
                resp_json = await resp.json()

            events = resp_json.get('items', [])
            page_token = resp_json.get('nextPageToken', False)

            for event in events:
                yield event

    @token_check()
    async def add_attachment(self, calendar_id: str, event_id: str, form_url: str, spreadsheet_url: str) -> None:
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

        resp = await self._httpsession.patch(f'{self.API_URL}/calendars/{calendar_id}/events/{event_id}',
                                             headers=self._headers, json=changes, params=params,
                                             ssl=False)
        resp.close()

    @token_check()
    async def event_watch(self, calendar_id: str) -> Dict[str, str]:
        body = {
            'id': uuid.uuid4().hex,
            'type': "web_hook",
            'address': self.QM_WEBHOOK_URL
        }

        resp = await self._httpsession.post(f'{self.API_URL}/calendars/{calendar_id}/events/watch',
                                            json=body, headers=self._headers, ssl=False)
        async with resp:
            return await resp.json()

    @token_check()
    async def event_watch_stop(self, id: str, resource_id: str) -> None:
        body = {
            'id': id,
            'resourceId': resource_id
        }

        resp = await self._httpsession.post(f'{self.API_URL}/channels/stop',
                                            json=body, headers=self._headers, ssl=False)
        resp.close()
