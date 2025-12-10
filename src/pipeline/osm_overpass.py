# @author: Lameck David Musumpuka

"""Helpers for querying OpenStreetMap via the Overpass API.

Provides utilities to build Overpass QL queries, convert responses to GeoJSON,
and optionally persist snapshots for reuse by the pipeline.
"""

from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import requests


OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")

def _overpass_request(query: str, timeout: float = 30.0) -> Dict[str, Any]:
    """Execute an Overpass API query and return the JSON payload.

    This helper is intentionally small and relies only on the public Overpass
    endpoint by default. Callers are responsible for handling network errors.
    """

    q = query.strip()
    if not q:
        raise ValueError("Overpass query must not be empty")
    resp = requests.post(OVERPASS_URL, data={"data": q}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _elements_to_geojson(elements: Iterable[Dict[str, Any]], query: str) -> Dict[str, Any]:
    """Convert Overpass elements (with geom) into a GeoJSON FeatureCollection.

    - ways with a `geometry` array become LineString features.
    - nodes become Point features.
    Other element types are currently ignored to keep the converter simple and
    dependency-free. This is sufficient for road networks, buildings, and basic
    POIs as required by the SUSPS specification.
    """

    features: List[Dict[str, Any]] = []
    for el in elements:
        etype = el.get("type")
        eid = el.get("id")
        tags = el.get("tags", {}) or {}

        geom = None
        if etype == "way":
            coords = []
            # When `out geom;` is used, Overpass adds a `geometry` array with
            # lat/lon pairs along the way, which we can convert directly.
            for g in el.get("geometry", []) or []:
                lat = g.get("lat")
                lon = g.get("lon")
                if lat is None or lon is None:
                    continue
                coords.append([float(lon), float(lat)])
            if len(coords) >= 2:
                geom = {"type": "LineString", "coordinates": coords}
        elif etype == "node":
            lat = el.get("lat")
            lon = el.get("lon")
            if lat is not None and lon is not None:
                geom = {"type": "Point", "coordinates": [float(lon), float(lat)]}

        if geom is None:
            # Skip elements we cannot safely represent as GeoJSON with our
            # minimal converter.
            continue

        props = {"id": eid, "osm_type": etype}
        # Merge tags last so they can override generic keys if needed.
        if isinstance(tags, dict):
            props.update(tags)

        features.append(
            {
                "type": "Feature",
                "id": f"{etype}/{eid}",
                "properties": props,
                "geometry": geom,
            }
        )

    fc: Dict[str, Any] = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "generated_at": datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"),
            "query": query.strip(),
            "feature_count": len(features),
        },
    }
    return fc


def _bbox_from_center(lat: float, lon: float, delta: float = 0.25) -> Tuple[float, float, float, float]:
    """Compute a simple lat/lon bounding box around a center point.

    This is a lightweight helper for city-scale queries (tens of km). It does
    not account for ellipsoidal effects but is sufficient for the SUSPS demo.
    """

    south = lat - delta
    north = lat + delta
    west = lon - delta
    east = lon + delta
    return south, west, north, east


def build_bbox_query(
    south: float,
    west: float,
    north: float,
    east: float,
) -> str:
    """Build an Overpass QL query for roads, buildings, and land-use in a bbox.

    This focuses on highways, buildings, and landuse polygons, plus a set of
    traffic- and planning-relevant POIs.
    """

    return f"""
    [out:json][timeout:25];
    (
      way["highway"]({south},{west},{north},{east});
      way["building"]({south},{west},{north},{east});
      way["landuse"]({south},{west},{north},{east});
      node["amenity"]({south},{west},{north},{east});
    );
    out geom;
    """.strip()


def build_named_area_query(name: str) -> str:
    """Build an Overpass QL query for a named administrative area.

    This can be used to fetch features for cities like Nairobi or Lusaka
    without hardcoding a bounding box.
    """

    n = name.replace("\"", "\\\"")
    return f"""
    [out:json][timeout:25];
    area["name"="{n}"][admin_level];
    map_to_area -> .searchArea;
    (
      way["highway"](area.searchArea);
      way["building"](area.searchArea);
      way["landuse"](area.searchArea);
      node["amenity"](area.searchArea);
    );
    out geom;
    """.strip()


def build_polygon_query(coords: Sequence[Tuple[float, float]]) -> str:
    """Build an Overpass QL query using a custom polygon.

    The polygon is defined as an iterable of (lat, lon) coordinate pairs.
    """

    pts: List[str] = []
    for lat, lon in coords:
        pts.append(f"{lat} {lon}")
    poly = " ".join(pts)
    return f"""
    [out:json][timeout:25];
    (
      way["highway"](poly:"{poly}");
      way["building"](poly:"{poly}");
      way["landuse"](poly:"{poly}");
      node["amenity"](poly:"{poly}");
    );
    out geom;
    """.strip()


def fetch_osm_by_bbox(
    south: float,
    west: float,
    north: float,
    east: float,
    *,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """Fetch OSM features for the given bounding box and return GeoJSON.

    Callers should handle network exceptions from requests/Overpass.
    """

    query = build_bbox_query(south, west, north, east)
    data = _overpass_request(query, timeout=timeout)
    elements = data.get("elements", []) or []
    return _elements_to_geojson(elements, query)


def fetch_osm_for_city_bbox(
    lat: float,
    lon: float,
    *,
    delta: float = 0.25,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """Convenience wrapper fetching OSM data for a city-scale bbox.

    `delta` controls the half-height/width of the box in degrees.
    """

    south, west, north, east = _bbox_from_center(lat, lon, delta=delta)
    return fetch_osm_by_bbox(south, west, north, east, timeout=timeout)


def fetch_osm_by_named_area(name: str, *, timeout: float = 30.0) -> Dict[str, Any]:
    """Fetch OSM features for a named area and return GeoJSON."""

    query = build_named_area_query(name)
    data = _overpass_request(query, timeout=timeout)
    elements = data.get("elements", []) or []
    return _elements_to_geojson(elements, query)


def fetch_osm_by_polygon(
    coords: Sequence[Tuple[float, float]], *, timeout: float = 30.0
) -> Dict[str, Any]:
    """Fetch OSM features for an arbitrary polygon defined by (lat, lon) points."""

    if not coords:
        raise ValueError("Polygon coordinates must not be empty")
    query = build_polygon_query(coords)
    data = _overpass_request(query, timeout=timeout)
    elements = data.get("elements", []) or []
    return _elements_to_geojson(elements, query)


def save_geojson(data: Dict[str, Any], path: str | os.PathLike[str]) -> None:
    """Save a GeoJSON object to disk with UTF-8 encoding.

    This is a small helper so that ingest scripts can persist OSM snapshots
    under data/<CITY>/raw/ for reuse by the pipeline and frontend.
    """

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
