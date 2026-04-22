import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI

from src.db.database import engine
from src.db.config import Base, get_settings
from src.routers.auth import router as auth_router
from src.routers.ingestion import router as ingestion_router
from src.routers.search import router as search_router
from src import models  # noqa: F401

settings = get_settings()
log_file_path = Path(settings.LOG_FILE_PATH)
log_file_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[
        RotatingFileHandler(
            log_file_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        ),
    ],
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Image Classifier API")
app.include_router(auth_router)
app.include_router(ingestion_router)
app.include_router(search_router)
