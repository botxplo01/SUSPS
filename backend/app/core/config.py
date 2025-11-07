import os

# Database URL, e.g. postgresql+psycopg2://user:pass@host:5432/dbname
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/susps",
)

# Dash will be mounted at /dash/ by default
DASH_BASE_PATH: str = os.getenv("DASH_BASE_PATH", "/dash/").rstrip("/") + "/"
