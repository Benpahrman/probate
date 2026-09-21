import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

db_url = settings.sync_database_url

if "sqlite" in db_url:
    # Ensure database folder exists if relative path is specified
    clean_path = db_url.replace("sqlite:///", "")
    if "/" in clean_path or "\\" in clean_path:
        dir_name = os.path.dirname(clean_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
else:
    engine = create_engine(
        db_url,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
