from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.db.config import get_settings, Base

settings = get_settings()

engine = create_engine(settings.DATABASE_URI, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



