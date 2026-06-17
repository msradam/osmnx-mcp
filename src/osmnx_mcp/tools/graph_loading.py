import osmnx as ox
from fastmcp import FastMCP
from typing import Callable


def register(mcp: FastMCP, get_graph: Callable) -> None:

    @mcp.tool
    def load_graph_from_point(
        lat: float,
        lng: float,
        dist_m: int = 1000,
        network_type: str = "drive",
        add_speeds: bool = True,
        add_travel_times: bool = True,
    ) -> dict:
        """
        Download and load an OSMnx street network centered at (lat, lng).

        dist_m: radius in meters (default 1000).
        network_type: 'drive', 'walk', 'bike', or 'all'.
        add_speeds / add_travel_times: enrich edges for travel-time routing.

        Returns a summary after loading. This replaces any previously loaded graph.
        """
        import osmnx_mcp.server as _server

        G = ox.graph_from_point((lat, lng), dist=dist_m, network_type=network_type)
        if add_speeds:
            G = ox.add_edge_speeds(G)
        if add_travel_times:
            G = ox.add_edge_travel_times(G)
        _server._graph = G
        return {
            "status": "loaded",
            "node_count": len(G.nodes),
            "edge_count": len(G.edges),
            "center": {"lat": lat, "lng": lng},
            "dist_m": dist_m,
            "network_type": network_type,
        }

    @mcp.tool
    def load_graph_from_place(
        place: str,
        network_type: str = "drive",
        add_speeds: bool = True,
        add_travel_times: bool = True,
    ) -> dict:
        """
        Download and load an OSMnx street network for a named place.

        place: geocodable name, e.g. 'Piedmont, California, USA'.
               Requires Nominatim to return a polygon boundary for that place —
               prefer load_graph_from_point for neighborhoods that lack one.
        network_type: 'drive', 'walk', 'bike', or 'all'.

        Returns a summary after loading. This replaces any previously loaded graph.
        """
        import osmnx_mcp.server as _server

        G = ox.graph_from_place(place, network_type=network_type)
        if add_speeds:
            G = ox.add_edge_speeds(G)
        if add_travel_times:
            G = ox.add_edge_travel_times(G)
        _server._graph = G
        return {
            "status": "loaded",
            "place": place,
            "node_count": len(G.nodes),
            "edge_count": len(G.edges),
            "network_type": network_type,
        }

    @mcp.tool
    def graph_info() -> dict:
        """
        Return metadata about the currently loaded graph, including available edge
        and node attributes. Always call this (or street_names / edge_attribute_values)
        to read data already in the graph — do NOT use features_from_* for data the
        graph already contains.
        """
        try:
            G = get_graph()
        except RuntimeError:
            return {
                "loaded": False,
                "message": "No graph loaded. Call load_graph_from_point first.",
            }
        bbox = {
            "north": max(d["y"] for _, d in G.nodes(data=True)),
            "south": min(d["y"] for _, d in G.nodes(data=True)),
            "east": max(d["x"] for _, d in G.nodes(data=True)),
            "west": min(d["x"] for _, d in G.nodes(data=True)),
        }
        edge_attrs = sorted({k for _, _, d in G.edges(data=True) for k in d})
        node_attrs = sorted({k for _, d in G.nodes(data=True) for k in d})
        return {
            "loaded": True,
            "node_count": len(G.nodes),
            "edge_count": len(G.edges),
            "crs": str(G.graph.get("crs", "epsg:4326")),
            "bbox": bbox,
            "edge_attributes": edge_attrs,
            "node_attributes": node_attrs,
        }

    @mcp.tool
    def street_names() -> dict:
        """
        Return all unique street names in the loaded graph.

        Reads the 'name' attribute directly from graph edges — instant, no network call.
        """
        G = get_graph()
        names: set[str] = set()
        for _, _, data in G.edges(data=True):
            val = data.get("name")
            if val is None:
                continue
            if isinstance(val, list):
                names.update(str(v) for v in val if v)
            else:
                names.add(str(val))
        return {"street_names": sorted(names), "count": len(names)}

    @mcp.tool
    def edge_attribute_values(attribute: str) -> dict:
        """
        Return all unique values for a named edge attribute in the loaded graph.

        Reads directly from graph edges — instant, no network call.
        Use graph_info() first to see which attributes are available.
        """
        G = get_graph()
        values: set[str] = set()
        for _, _, data in G.edges(data=True):
            val = data.get(attribute)
            if val is None:
                continue
            if isinstance(val, list):
                values.update(str(v) for v in val if v is not None)
            else:
                values.add(str(val))
        return {"attribute": attribute, "values": sorted(values), "count": len(values)}
