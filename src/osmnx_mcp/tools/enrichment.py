import osmnx as ox
from fastmcp import FastMCP
from typing import Callable


def register(mcp: FastMCP, get_graph: Callable) -> None:

    @mcp.tool
    def add_edge_speeds() -> dict:
        """
        Impute speed values (kph) on all edges using OSM maxspeed tags and heuristics.

        Mutates the mounted graph in place. Call before add_edge_travel_times.
        Returns edge count updated.
        """
        G = get_graph()
        G = ox.add_edge_speeds(G)
        _update_graph(G)
        edge_count = sum(1 for _, _, d in G.edges(data=True) if "speed_kph" in d)
        return {"edges_updated": edge_count, "attribute": "speed_kph"}

    @mcp.tool
    def add_edge_travel_times() -> dict:
        """
        Compute travel time in seconds for each edge from length and speed_kph.

        Requires add_edge_speeds to have been called first.
        Mutates the mounted graph in place.
        Returns edge count updated.
        """
        G = get_graph()
        G = ox.add_edge_travel_times(G)
        _update_graph(G)
        edge_count = sum(1 for _, _, d in G.edges(data=True) if "travel_time" in d)
        return {"edges_updated": edge_count, "attribute": "travel_time"}

    @mcp.tool
    def add_edge_bearings() -> dict:
        """
        Add compass bearing (degrees) to each edge.

        Mutates the mounted graph in place.
        Returns edge count updated.
        """
        G = get_graph()
        G = ox.add_edge_bearings(G)
        _update_graph(G)
        edge_count = sum(1 for _, _, d in G.edges(data=True) if "bearing" in d)
        return {"edges_updated": edge_count, "attribute": "bearing"}

    @mcp.tool
    def add_edge_grades() -> dict:
        """
        Add elevation grade (rise/run) to each edge using node elevation data.

        Requires nodes to have an 'elevation' attribute (fetch separately via elevation API).
        Mutates the mounted graph in place. Returns edge count updated.
        """
        G = get_graph()
        G = ox.add_edge_grades(G)
        _update_graph(G)
        edge_count = sum(1 for _, _, d in G.edges(data=True) if "grade" in d)
        return {"edges_updated": edge_count, "attribute": "grade"}


def _update_graph(G) -> None:
    import osmnx_mcp.server as _server
    _server._graph = G
