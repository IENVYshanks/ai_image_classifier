from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.db.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URI, echo=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

conn = engine.connect()
result = conn.execute(text("SELECT 1"))


for row in result:
    print(row)
conn.close()
