import pickle
import os
from functools import wraps
from datetime import datetime

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from aiohttp import ClientSession
import ujson


class GoogleMixin:
    __slots__ = ('_creds_path', '_token_path', '_scopes', '_creds', '_headers')

    def __init__(self, creds_path: str, token_path: str, scopes: str or list):
        self._creds_path = creds_path
        self._token_path = token_path
        self._scopes = scopes
        self._creds = None

        self._headers = {
            "Authorization": ""
        }

        self.refresh_token()

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

    # TODO: make decorators work in API classes
    def token_check(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if datetime.utcnow() >= self._creds.expiry:
                self.refresh_token()

            return await func(self, *args, **kwargs)

        return wrapper

    def httpsession_check(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not kwargs.get('session'):
                kwargs['session'] = ClientSession(json_serialize=ujson.dumps)

            return await func(*args, **kwargs)
        return wrapper
