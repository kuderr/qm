from typing import Dict, Any

from ..decorators import token_check
from .mixins import GoogleMixin
from ..settings import settings


class GScript(GoogleMixin):
    API_URL = "https://script.googleapis.com/v1"
    SCRIPT_ID = settings.google_script_id

    @token_check()
    async def create_form(self, event_name: str, editors: list, question: str) -> Dict[str, str]:
        body = {
            "function": "createForm",
            "parameters": [event_name, editors, question]
        }

        result = await self.run_script(body)
        return result['response'].get('result')

    @token_check()
    async def open_form(self, form_id: str) -> None:
        body = {
            "function": "openForm",
            "parameters": [form_id]
        }

        await self.run_script(body)

    @token_check()
    async def run_script(self, body: Dict[str, Any]) -> None:
        resp = await self._httpsession.post(f"{self.API_URL}/scripts/{self.SCRIPT_ID}:run",
                                            headers=self._headers, json=body,
                                            ssl=False)
        async with resp:
            return await resp.json()
