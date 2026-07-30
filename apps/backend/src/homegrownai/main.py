from importlib.metadata import version, PackageNotFoundError

from sqlalchemy import create_engine
from fastapi import FastAPI, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse

from .schemas.settings import settings

from .database.db import DB

app = FastAPI(title="HomeGrownAI API Backend", version=version("homegrownai"))

db = DB(
    db_driver=settings.db_driver,
    db_host=settings.db_host,
    db_name=settings.db_name,
    db_port=settings.db_port,
    db_password=settings.db_passwd,
    db_user=settings.db_user,
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "version": app.version,
    }
