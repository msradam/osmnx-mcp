import osmnx as ox
from fastmcp import FastMCP
from typing import Callable


def register(mcp: FastMCP, get_graph: Callable) -> None:

    @mcp.tool
    def nearest_nodes(lng: float, lat: float) -> dict:
        """Find the nearest graph node to a coordinate (lng, lat order). Returns node id and its data."""
        G = get_graph()
        node_id = ox.nearest_nodes(G, lng, lat)
        data = dict(G.nodes[node_id])
        return {"node_id": int(node_id), "data": data}

    @mcp.tool
    def shortest_path(
        orig_lng: float,
        orig_lat: float,
        dest_lng: float,
        dest_lat: float,
        weight: str = "length",
    ) -> dict:
        """
        Solve the shortest path between two coordinates (lng, lat order).

        weight: 'length' for distance in meters, 'travel_time' for time in seconds
        (requires add_edge_travel_times to have been called first).

        Returns node sequence, total length in meters, and travel time in seconds if available.
        """
        G = get_graph()
        orig = ox.nearest_nodes(G, orig_lng, orig_lat)
        dest = ox.nearest_nodes(G, dest_lng, dest_lat)
        path = ox.shortest_path(G, orig, dest, weight=weight)
        if path is None:
            return {"path": None, "node_count": 0, "length_m": None, "travel_time_s": None}
        length = sum(G[u][v][0].get("length", 0) for u, v in zip(path[:-1], path[1:]))
        travel_time = sum(G[u][v][0].get("travel_time", 0) for u, v in zip(path[:-1], path[1:]))
        return {
            "path": [int(n) for n in path],
            "node_count": len(path),
            "length_m": round(length, 1),
            "travel_time_s": round(travel_time, 1) if travel_time else None,
        }

    @mcp.tool
    def k_shortest_paths(
        orig_lng: float,
        orig_lat: float,
        dest_lng: float,
        dest_lat: float,
        k: int = 3,
        weight: str = "length",
    ) -> list[dict]:
        """
        Solve k shortest paths between two coordinates (lng, lat order).

        weight: 'length' for distance, 'travel_time' for time.
        Returns a list of dicts each with 'path' (node sequence) and 'length_m'.
        """
        G = get_graph()
        orig = ox.nearest_nodes(G, orig_lng, orig_lat)
        dest = ox.nearest_nodes(G, dest_lng, dest_lat)
        paths = list(ox.k_shortest_paths(G, orig, dest, k, weight=weight))
        results = []
        for path in paths:
            length = sum(G[u][v][0].get("length", 0) for u, v in zip(path[:-1], path[1:]))
            results.append({"path": [int(n) for n in path], "length_m": round(length, 1)})
        return results

    @mcp.tool
    def nearest_edges(lng: float, lat: float) -> dict:
        """
        Find the nearest graph edge to a coordinate (lng, lat order).
        Returns (u, v, key) identifiers and edge attribute data (geometry excluded).
        """
        G = get_graph()
        u, v, key = ox.nearest_edges(G, lng, lat)
        data = dict(G[u][v][key])
        data.pop("geometry", None)
        return {"u": int(u), "v": int(v), "key": int(key), "data": data}
