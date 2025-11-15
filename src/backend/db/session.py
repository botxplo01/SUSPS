from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load .env in local dev so scripts that import SessionLocal/engine
# (without going through src.backend.api) still see LOCAL_DATABASE_URL, etc.
try:  # pragma: no cover - optional
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


def _truthy(val: str | None) -> bool:
    return str(val).lower() in {"1", "true", "yes", "on"}


def _normalize_db_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and "+psycopg2://" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def _select_database_url() -> str:
    """Select the effective database URL based on environment.

    - When USE_LOCAL_DB=true and LOCAL_DATABASE_URL is set, prefer LOCAL_DATABASE_URL
      (local development).
    - Otherwise, fall back to DATABASE_URL (e.g. Render-managed Postgres).
    """

    if _truthy(os.getenv("USE_LOCAL_DB")) and os.getenv("LOCAL_DATABASE_URL"):
        return os.getenv("LOCAL_DATABASE_URL", "")
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL", "")
    return ""

_DATABASE_URL = _select_database_url()
if _DATABASE_URL:
    _DATABASE_URL = _normalize_db_url(_DATABASE_URL)
    # Keep the normalized URL in the env so other modules see the same value
    os.environ["DATABASE_URL"] = _DATABASE_URL

# Create the engine lazily; if DATABASE_URL is empty, this will error only when used
engine = create_engine(_DATABASE_URL or "postgresql+psycopg2://", future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
