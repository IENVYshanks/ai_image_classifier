from fastapi import FastAPI

from src.db.database import engine
from src.db.config import Base
from src.routers.auth import router as auth_router
from src.routers.images import router as images_router
from src import models  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Image Classifier API")
app.include_router(auth_router)
app.include_router(images_router)

