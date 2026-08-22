from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI

from .api.routes.users import users_router
from .database.schema import ensure_database_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database_schema()
    yield


app = FastAPI(
    title="HomeGrownAI API Backend",
    version=version("homegrownai"),
    lifespan=lifespan,
    root_path="/api",
)
app.include_router(users_router)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "version": app.version,
    }
