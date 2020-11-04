import typing
from datetime import date, datetime

from fastapi import FastAPI
import uvicorn

from core.database import database
from core.schemas import Calendar, Event
from core.utils import get_all_calendars, get_all_events

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post('/calendar-webhook')
async def some_event_triggered():
    # TODO: write get_calendar func, if webhook is expired -- refresh it
    pass


@app.get('/events/',
         response_description="All events",
         response_model=typing.List[Event],
         )
async def get_events():
    # test route
    return await get_all_calendars()


@app.get('/calendars/',
         response_description="All calendars",
         response_model=typing.List[Calendar],
         )
async def get_calendars():
    # test route
    return await get_all_events()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
