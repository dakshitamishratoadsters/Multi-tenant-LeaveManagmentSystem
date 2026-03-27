from fastapi import FastAPI
from src.api.v1.router.routes import api_router

# add events
from src.db.events import user_events

app = FastAPI()

app.include_router(api_router)