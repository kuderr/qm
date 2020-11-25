from datetime import datetime
import pickle
import os
import logging
from typing import List, Union, AsyncGenerator, Dict, Any

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from aiohttp import ClientSession
import ujson

from .decorators import token_check
from .decorators import COROUTINE, GENERATOR
from .settings import settings

logger = logging.getLogger("qm")


class GoogleBase:
    __slots__ = (
        "_creds_path",
        "_token_path",
        "_scopes",
        "_creds",
        "_headers",
        "_httpsession",
    )

    def __init__(self, creds_path: str, scopes: Union[str, List[str]]):
        self._creds_path = creds_path

        self._token_path = "{folder}{class_name}.pickle".format(
            folder=settings.google_tokens_folder, class_name=type(self).__name__
        )
        self._scopes = scopes
        self._creds = None

        self._httpsession = ClientSession(json_serialize=ujson.dumps)

        self._headers = {"Authorization": ""}

    def refresh_token(self) -> None:
        creds = None

        if os.path.exists(self._token_path):
            with open(self._token_path, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._creds_path, self._scopes
                )
                creds = flow.run_local_server(port=0)

            with open(self._token_path, "wb") as token:
                pickle.dump(creds, token)

        self._creds = creds
        self._headers["Authorization"] = f"Bearer {creds.token}"


class GCalendar(GoogleBase):
    API_URL = "https://www.googleapis.com/calendar/v3"

    # AsyncGenerator[YieldType, SendType]
    @token_check(GENERATOR)
    async def get_editors(self, calendar_id: str) -> AsyncGenerator[str, None]:
        page_token = ""

        while page_token != False:
            resp = await self._httpsession.get(
                f"{self.API_URL}/calendars/{calendar_id}/acl?pageToken={page_token}",
                headers=self._headers,
                ssl=False,
            )
            async with resp:
                resp_json = await resp.json()
                logger.debug(f"get_editors response: {resp_json}")

            acls = resp_json.get("items", [])
            page_token = resp_json.get("nextPageToken", False)

            for acl in acls:
                if acl["role"] == "writer":
                    yield acl["scope"]["value"]

    @token_check(GENERATOR)
    async def get_events(
        self, calendar_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        page_token = ""

        params = {
            "timeMin": datetime.utcnow().isoformat() + "Z",  # 'Z' indicates UTC time
            "singleEvents": "true",
            "orderBy": "startTime",
        }

        while page_token != False:
            resp = await self._httpsession.get(
                f"{self.API_URL}/calendars/{calendar_id}/events?pageToken={page_token}",
                headers=self._headers,
                params=params,
                ssl=False,
            )
            async with resp:
                resp_json = await resp.json()
                logger.debug(f"get_events response: {resp_json}")

            events = resp_json.get("items", [])
            page_token = resp_json.get("nextPageToken", False)

            for event in events:
                yield event

    @token_check(COROUTINE)
    async def add_attachment(
        self, calendar_id: str, event_id: str, form_url: str, spreadsheet_url: str
    ) -> None:
        changes = {
            "attachments": [
                {"fileUrl": form_url, "title": "Форма"},
                {"fileUrl": spreadsheet_url, "title": "Таблица"},
            ]
        }

        params = {"supportsAttachments": "true"}

        resp = await self._httpsession.patch(
            f"{self.API_URL}/calendars/{calendar_id}/events/{event_id}",
            headers=self._headers,
            json=changes,
            params=params,
            ssl=False,
        )
        async with resp:
            resp_json = await resp.json()
            logger.debug(f"add_attachment response: {resp_json}")


class GScript(GoogleBase):
    API_URL = "https://script.googleapis.com/v1"
    SCRIPT_ID = settings.google_script_id

    @token_check(COROUTINE)
    async def create_form(
        self, event_name: str, editors: list, question: str
    ) -> Dict[str, str]:
        body = {"function": "createForm", "parameters": [event_name, editors, question]}

        resp_json = await self.run_script(body)
        logger.debug(f"create_form response: {resp_json}")

        return resp_json["response"].get("result")

    @token_check(COROUTINE)
    async def open_form(self, form_id: str) -> None:
        body = {"function": "openForm", "parameters": [form_id]}

        resp_json = await self.run_script(body)
        logger.debug(f"open_form response: {resp_json}")

    @token_check(COROUTINE)
    async def run_script(self, body: Dict[str, Any]) -> None:
        resp = await self._httpsession.post(
            f"{self.API_URL}/scripts/{self.SCRIPT_ID}:run",
            headers=self._headers,
            json=body,
            ssl=False,
        )
        async with resp:
            return await resp.json()
