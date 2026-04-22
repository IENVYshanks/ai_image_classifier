from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.db.config import get_settings

settings = get_settings()
print(settings.DATABASE_URI)

engine = create_engine(
    settings.DATABASE_URI,
    echo=True
)

# else:
#     print("Connection failed.")
# SessionLocal = sessionmaker(
#     autocommit=False,
#     autoflush=False,
#     bind=engine,
# )

try:
   with engine.connect() as connection:
       print("Connection successful!")
except Exception as e:
   print(f"Failed to connect: {e}")


# for row in result:
#     print(row)
# conn.close()
