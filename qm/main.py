from typing import Optional

import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks
from fastapi import Header

from tortoise.contrib.fastapi import register_tortoise

from core.settings import settings
from core.utils import QueuesManager


app = FastAPI()


class Status(BaseModel):
    message: str


@app.post('/calendar-webhook', response_model=Status, status_code=202)
async def some_event_triggered(background_tasks: BackgroundTasks,
                               x_goog_resource_uri: Optional[str] = Header(None)):

    calendar_id = x_goog_resource_uri.split('/')[6]
    calendar_id = calendar_id.replace('%40', '@')

    qm = QueuesManager()
    background_tasks.add_task(qm.update_queues, calendar_id)

    return Status(message="Events patched")


register_tortoise(
    app,
    db_url=settings.db_url,
    generate_schemas=True,
    modules={"models": ["core.models"]},
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
