# @author: Lameck David Musumpuka

from __future__ import annotations

# Database engine and session factory configuration for the SUSPS backend.
#
# This module selects the effective DATABASE_URL based on environment
# variables (local vs Render) and exposes a shared SQLAlchemy engine and
# SessionLocal factory used across API handlers and seeding scripts.

import os
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
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
    """Normalise DATABASE_URL for SQLAlchemy/psycopg2.

    - Upgrade "postgres://" URLs to "postgresql+psycopg2://".
    - Ensure Render-managed Postgres URLs always include "sslmode=require" so
      connections satisfy the platform's TLS requirement even if the env var is
      missing that query parameter.
    """

    # Normalise scheme for SQLAlchemy's psycopg2 dialect
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+psycopg2://" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

    # For Render-managed Postgres (hosts ending with render.com), append
    # sslmode=require when it is not already present. This keeps DATABASE_URL
    # values copy-pasted from the dashboard working even if the parameter is
    # omitted or stripped.
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if host.endswith("render.com"):
            qs_items = parse_qsl(parsed.query, keep_blank_values=True)
            has_sslmode = any(k.lower() == "sslmode" for k, _ in qs_items)
            if not has_sslmode:
                qs_items.append(("sslmode", "require"))
                new_query = urlencode(qs_items)
                url = urlunparse(parsed._replace(query=new_query))
    except Exception:
        # If anything goes wrong during parsing, fall back to the best-effort URL
        return url

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

