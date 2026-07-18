import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from restaurant_rec.api.routes import router
from restaurant_rec.config import get_settings
from restaurant_rec.data.cache import store

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s", settings.app_name)
    logger.info("LLM model: %s", settings.llm_model)
    logger.info("Dataset: %s", settings.hf_dataset_name)
    store.load()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(router)
