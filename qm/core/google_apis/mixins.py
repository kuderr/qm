import pickle
import os
from typing import List, Union
import asyncio

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from aiohttp import ClientSession
import ujson

from ..settings import settings


class GoogleMixin:
    __slots__ = ('_creds_path', '_token_path', '_scopes',
                 '_creds', '_headers', '_httpsession')

    def __init__(self, creds_path: str, scopes: Union[str, List[str]]):
        self._creds_path = creds_path

        self._token_path = '{folder}{class_name}.pickle'.format(folder=settings.google_tokens_folder,
                                                                class_name=type(self).__name__)
        self._scopes = scopes
        self._creds = None

        self._httpsession = ClientSession(json_serialize=ujson.dumps)

        self._headers = {
            "Authorization": ""
        }

    def __del__(self):
        asyncio.create_task(self._httpsession.close())

    def refresh_token(self) -> None:
        creds = None

        if os.path.exists(self._token_path):
            with open(self._token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._creds_path, self._scopes)
                creds = flow.run_local_server(port=0)

            with open(self._token_path, 'wb') as token:
                pickle.dump(creds, token)

        self._creds = creds
        self._headers["Authorization"] = f"Bearer {creds.token}"
