from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(title="Credit Application Encoder")
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
app.include_router(router)
