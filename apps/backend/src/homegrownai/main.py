from contextlib import asynccontextmanager
from importlib.metadata import version
from platform import system
from sys import stderr

from fastapi import FastAPI
from loguru import logger

from homegrownai.ai.engine import InferenceEngine
from homegrownai.api.routes.files import files_router
from homegrownai.api.routes.users import users_router
from homegrownai.database.schema import ensure_database_schema

logger.remove()
logger.add(stderr, format="{time:MMMM D, YYYY > HH:mm:ss} | {extra} | {message}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database_schema()

    if "darwin" in system().lower():
        app.state.inference_engine = InferenceEngine("mlx-community/Qwen3.8-27B-4bit")
    else:
        app.state.inference_engine = InferenceEngine("RedHatAI/Qwen3.8-27B-INT4")

    logger.info("Application startup complete and AI engine initialized!")

    yield

    engine: InferenceEngine = app.state.inference_engine

    engine.shutdown()

    del app.state.inference_engine


app = FastAPI(
    title="HomeGrownAI API Backend",
    version=version("homegrownai"),
    lifespan=lifespan,
    root_path="/api",
)
app.include_router(users_router)
app.include_router(files_router)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "version": app.version,
    }
