from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _normalize_db_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and "+psycopg2://" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


_DATABASE_URL = os.getenv("DATABASE_URL", "")
if _DATABASE_URL:
    _DATABASE_URL = _normalize_db_url(_DATABASE_URL)

# Create the engine lazily; if DATABASE_URL is empty, this will error only when used
engine = create_engine(_DATABASE_URL or "postgresql+psycopg2://", future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
