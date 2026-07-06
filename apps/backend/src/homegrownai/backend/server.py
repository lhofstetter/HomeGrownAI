from importlib.metadata import version, PackageNotFoundError

from sqlalchemy import create_engine
from fastapi import FastAPI, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse

from homegrownai.backend.classes.settings import settings

from .classes.db import DB

app = FastAPI(
    title="HomeGrownAI API Backend",
    version= version("homegrownai")
)

db = DB(settings.db_url, settings.db_user, settings.db_passwd)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def root():
    return {
        "status": "ok",
        "version": app.version,
    }


