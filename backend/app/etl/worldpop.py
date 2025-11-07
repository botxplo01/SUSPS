"""WorldPop ingestion stub.

Plan:
1) Download WorldPop GeoTIFF for the target country/city and year.
2) Load ward polygons from urban_areas (PostGIS) or GeoPackage.
3) Compute zonal statistics (sum/mean) per ward.
4) Load aggregated results into demographics table.

Notes:
- Prefer EPSG:4326 for alignment.
- Use rasterio + rasterstats or rioxarray + geopandas.
- Keep a data catalog entry with source URL and version.
"""

from pathlib import Path


def ingest_worldpop(
    tif_path: Path, year: int, dsn: str, table: str = "demographics"
) -> None:
    """Ingest WorldPop raster into PostGIS aggregated by ward.

    Args:
        tif_path: Path to the WorldPop GeoTIFF (population per pixel).
        year: Census/year to attribute results to.
        dsn: SQLAlchemy/psycopg2 DSN string for Postgres (e.g., postgresql+psycopg2://...).
        table: Target table name (default: demographics).
    """
    # Imports inside function to avoid heavy deps during basic app startup
    import geopandas as gpd
    import rasterio
    import numpy as np
    from sqlalchemy import create_engine

    engine = create_engine(dsn, future=True)

    # Load ward polygons
    wards = gpd.read_postgis(
        "SELECT area_id, name, geometry FROM urban_areas",
        con=engine,
        geom_col="geometry",
    )

    # Open raster and compute zonal stats (simple example: average using sample points)
    with rasterio.open(tif_path) as src:
        # Reproject wards to raster CRS if needed
        if wards.crs is None:
            wards.set_crs(4326, inplace=True)
        if wards.crs.to_string() != src.crs.to_string():
            wards = wards.to_crs(src.crs)

        # Sample raster at ward centroids as a placeholder (replace with proper zonal stats)
        centroids = wards.geometry.centroid
        samples = np.array(
            [
                x[0] if x is not None else None
                for x in src.sample([(g.x, g.y) for g in centroids])
            ]
        )

    # Build a small frame and write to demographics
    df = wards[["area_id", "name"]].copy()
    df["population"] = np.nan_to_num(samples, nan=0).astype(int)
    df["region_name"] = df["name"]
    df["census_year"] = year

    df[["region_name", "population", "census_year", "area_id"]].to_sql(
        table, con=engine, if_exists="append", index=False
    )
