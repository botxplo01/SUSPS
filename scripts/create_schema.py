# @author: Lameck David Musumpuka

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path to allow imports from 'src'
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.backend.db.base import Base
from src.backend.db.session import engine
import src.backend.db.tables  # noqa: F401 - ensure models are registered



def main() -> None:
    """Create all SUSPS tables on the configured DATABASE_URL.

    This uses the SQLAlchemy models in src/backend/db/tables.py so the schema
    matches the current code exactly, avoiding issues with SQL dumps.
    """

    Base.metadata.create_all(bind=engine)
    print("Created all SUSPS tables on the configured database.")


if __name__ == "__main__":
    main()

