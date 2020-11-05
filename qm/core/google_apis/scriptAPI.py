from typing import Dict

from aiohttp import ClientSession
import ujson

from .mixins import GoogleMixin
from ..settings import settings


class GScript(GoogleMixin):
    API_URL = "https://script.googleapis.com/v1"
    SCRIPT_ID = settings.google_script_id

    async def create_form(self, event_name: str, editors: list, question: str) -> Dict[str, str]:
        body = {
            "function": "createForm",
            "parameters": [event_name, editors, question]
        }

        result = await self.run_script(body)
        return result['response'].get('result')

    async def open_form(self, form_id: str) -> None:
        body = {
            "function": "openForm",
            "parameters": [form_id]
        }

        await self.run_script(body)

    async def run_script(self, body: dict, *, session: ClientSession = None) -> None:
        if session is None:
            session = ClientSession(json_serialize=ujson.dumps)

        async with session:
            resp = await session.post(f"{self.API_URL}/scripts/{self.SCRIPT_ID}:run",
                                      headers=self._headers, json=body,
                                      ssl=False)
            async with resp:
                return await resp.json()
