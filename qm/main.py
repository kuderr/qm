from typing import Optional, List
from datetime import date, datetime

from fastapi import FastAPI, Header, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from tortoise.contrib.fastapi import register_tortoise

from core.settings import settings
from core.utils import EventsProcessor

app = FastAPI()


class Status(BaseModel):
    message: str


@app.post('/calendar-webhook', response_model=Status)
async def some_event_triggered(background_tasks: BackgroundTasks,
                               x_goog_resource_uri: Optional[str] = Header(None)):

    calendar_id = x_goog_resource_uri.split('/')[6]
    calendar_id = calendar_id.replace('%40', '@')

    proc = EventsProcessor()
    # await proc(calendar_id)

    background_tasks.add_task(proc.process, calendar_id)

    return Status(message="Events patched")


register_tortoise(
    app,
    db_url=settings.db_url,
    modules={"models": ["core.models"]},
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
