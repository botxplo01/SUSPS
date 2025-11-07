"""OSM ingestion stub using OSMnx.

Plan:
1) Download PBF from Geofabrik or use OSMnx to fetch graph for the city.
2) Build edges/nodes tables (optional) and aggregate by ward.
3) Store road segments and attributes in PostGIS for traffic modeling.
"""


def ingest_osm_road_network(place_name: str, dsn: str) -> None:
    """Ingest OSM road network for a given place into PostGIS.

    Args:
        place_name: e.g., "Nairobi, Kenya".
        dsn: Postgres DSN (sqlalchemy/psycopg2 string).
    """
    import osmnx as ox
    from sqlalchemy import create_engine

    G = ox.graph_from_place(place_name, network_type="drive")
    gdf_edges = ox.graph_to_gdfs(G, nodes=False)

    engine = create_engine(dsn, future=True)
    gdf_edges.to_postgis("osm_edges", engine, if_exists="replace")
