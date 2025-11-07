"""GTFS ingestion stub.

Plan:
1) Read GTFS zip (routes, trips, stop_times, stops).
2) Build route frequency and map to OSM edges (optional, later).
3) Store normalized GTFS tables in Postgres and derive metrics per ward.
"""

from pathlib import Path
import zipfile
import io
import pandas as pd
from sqlalchemy import create_engine


def ingest_gtfs(gtfs_zip: Path, dsn: str, schema: str = "public") -> None:
    engine = create_engine(dsn, future=True)

    with zipfile.ZipFile(gtfs_zip, "r") as z:
        for name in [
            "agency.txt",
            "routes.txt",
            "trips.txt",
            "stop_times.txt",
            "stops.txt",
            "calendar.txt",
        ]:
            if name in z.namelist():
                with z.open(name) as f:
                    df = pd.read_csv(io.BytesIO(f.read()))
                    table = name.replace(".txt", "")
                    df.to_sql(
                        table, engine, if_exists="replace", index=False, schema=schema
                    )
