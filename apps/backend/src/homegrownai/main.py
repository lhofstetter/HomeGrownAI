from contextlib import asynccontextmanager
from importlib.metadata import version, PackageNotFoundError

from fastapi import FastAPI, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse

from .schemas.settings import settings
from .api.routes.users import users_router

from .database.db import DB
from .database.schema import ensure_database_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database_schema()
    yield


app = FastAPI(
    title="HomeGrownAI API Backend",
    version=version("homegrownai"),
    lifespan=lifespan,
)
app.include_router(users_router)

@app.get("/")
async def root():
    return {
        "status": "ok",
        "version": app.version,
    }
