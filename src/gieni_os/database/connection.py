"""
Gieni OS - Relational Database Connection & Session Factory
Supports SQLite for zero-config local development and PostgreSQL for production.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from gieni_os.config import DATABASE_URL as CFG_DATABASE_URL

# Default to local SQLite if DATABASE_URL not set
DATABASE_URL = os.getenv("DATABASE_URL", CFG_DATABASE_URL or "sqlite:///database/gieni_os.db")

# SQLite multithreading arg
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Engine kwargs with production connection pooling & pre-ping
engine_kwargs = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
    "pool_recycle": 1800,
}
if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    from gieni_os.database.models import Base
    # Ensure database dir exists for sqlite
    if DATABASE_URL.startswith("sqlite:///"):
        path = DATABASE_URL.replace("sqlite:///", "")
        dir_name = os.path.dirname(path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
    Base.metadata.create_all(bind=engine)
