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
        Return metadata about the currently loaded graph.
        Call this first to check whether a graph is available before using other tools.
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
        return {
            "loaded": True,
            "node_count": len(G.nodes),
            "edge_count": len(G.edges),
            "crs": str(G.graph.get("crs", "epsg:4326")),
            "bbox": bbox,
        }
