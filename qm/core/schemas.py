from datetime import datetime
import typing

from pydantic import BaseModel, BaseSettings, Field


class Calendar(BaseModel):
    """
    Calendar body for response
    """

    id: int = Field(..., title="ID")
    google_id: str = Field(..., title="Calendar ID in google")
    webhook_channel: typing.Optional[str] = Field(
        title="ID of webhook channel")


class Event(BaseModel):
    """
    Event body for response
    """

    id: int = Field(..., title="ID")
    google_id: str = Field(..., title="Event ID in google")
    open_at: datetime = Field(..., title="Start datetime")
    created: bool = Field(..., title="Created flag")
    opened: bool = Field(..., title="Opened flag")
    calendar_id: str = Field(..., title="ID of parent calendar")


class Settings(BaseSettings):
    google_script_id: str = Field(..., env='SCRIPT_ID')

    testing: bool = Field(env='TESTING', default=True)

    db_user: str = Field(..., env='QM_DB_USER')
    db_password: str = Field(..., env='QM_DB_PASS')
    db_name: str = Field(..., env='QM_DB_NAME')
    db_host: str = Field(env='QM_DB_HOST', default='localhost')

    db_url: typing.Optional[str] = None

    webhook_url: str = Field(..., env='QM_WEBHOOK_URL')

    def __init__(self, **data):
        super().__init__(**data)

        if self.db_url:
            return

        if self.testing:
            self.db_url = f"sqlite:////tmp/{self.db_name}.db"
        else:
            self.db_url = (
                "postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}".format(**self.dict()))

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
