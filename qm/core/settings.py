import typing
import logging

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    google_script_id: str = Field(..., env="GOOGLE_SCRIPT_ID")
    google_creds_path: str = Field(..., env="GOOGLE_CREDS_PATH")
    google_tokens_folder: str = Field(
        env="GOOGLE_TOKENS_FOLDER", default="/opt/qm_tokens/"
    )
    google_calendar_scopes: typing.Set[str] = Field(..., env="GOOGLE_CALENDAR_SCOPES")
    google_script_scopes: typing.Set[str] = Field(..., env="GOOGLE_SCRIPT_SCOPES")

    db_url: str = Field(..., "QM_DB_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings(_env_file="../.env")

TORTOISE_ORM = {
    "connections": {"default": settings.db_url},
    "apps": {
        "models": {
            "models": ["core.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


def create_logger(mode="INFO"):
    logs = {"INFO": logging.INFO, "DEBUG": logging.DEBUG}

    logger = logging.getLogger("qm")
    logger.setLevel(logs[mode])

    ch = logging.StreamHandler()
    ch.setLevel(logs[mode])

    formatter = logging.Formatter(
        "%(levelname)-8s  %(asctime)s    %(message)s", datefmt="%d-%m-%Y %I:%M:%S %p"
    )

    ch.setFormatter(formatter)

    logger.addHandler(ch)

    return logger
