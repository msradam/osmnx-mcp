import osmnx as ox
from fastmcp import FastMCP
from typing import Callable


def _gdf_to_records(gdf) -> list[dict]:
    """Convert a GeoDataFrame to a list of dicts with geometry serialized to WKT."""
    records = []
    for idx, row in gdf.iterrows():
        record = {}
        for col, val in row.items():
            if col == "geometry":
                record["geometry_wkt"] = val.wkt if val is not None else None
            elif hasattr(val, "item"):
                record[col] = val.item()
            else:
                record[col] = val
        record["osm_id"] = str(idx)
        records.append(record)
    return records


def register(mcp: FastMCP, get_graph: Callable) -> None:

    @mcp.tool
    def features_from_point(
        lng: float, lat: float, dist_m: float, tags: dict
    ) -> list[dict]:
        """
        Fetch OSM features within dist_m of coordinate (lng, lat) matching tags.

        SLOW: hits the Overpass API live (seconds to minutes). Only use for features
        NOT already in the loaded graph — e.g. buildings, parks, amenities, transit stops.
        For street names, highway types, or other graph edge/node attributes, use
        street_names() or edge_attribute_values() instead.

        tags: dict of OSM tag filters, e.g. {"amenity": "cafe"} or {"building": True}.
        Returns list of feature dicts; geometry serialized to WKT.
        """
        gdf = ox.features_from_point((lat, lng), tags=tags, dist=dist_m)
        return _gdf_to_records(gdf)

    @mcp.tool
    def features_from_bbox(
        north: float, south: float, east: float, west: float, tags: dict
    ) -> list[dict]:
        """
        Fetch OSM features within a bounding box matching tags.

        SLOW: hits the Overpass API live (seconds to minutes). Only use for features
        NOT already in the loaded graph — e.g. buildings, parks, amenities, transit stops.
        For street names, highway types, or other graph edge/node attributes, use
        street_names() or edge_attribute_values() instead.

        tags: dict of OSM tag filters, e.g. {"amenity": True} or {"highway": "bus_stop"}.
        Returns list of feature dicts; geometry serialized to WKT.
        """
        gdf = ox.features_from_bbox(bbox=(north, south, east, west), tags=tags)
        return _gdf_to_records(gdf)

    @mcp.tool
    def features_from_place(place: str, tags: dict) -> list[dict]:
        """
        Fetch OSM features within a named place matching tags.

        SLOW: hits the Overpass API live (seconds to minutes). Only use for features
        NOT already in the loaded graph — e.g. buildings, parks, amenities, transit stops.
        For street names, highway types, or other graph edge/node attributes, use
        street_names() or edge_attribute_values() instead.

        place: geocodable place name string, e.g. "Piedmont, California, USA".
        tags: dict of OSM tag filters, e.g. {"leisure": "park"}.
        Returns list of feature dicts; geometry serialized to WKT.
        """
        gdf = ox.features_from_place(place, tags=tags)
        return _gdf_to_records(gdf)
