import osmnx as ox
from fastmcp import FastMCP
from typing import Callable


def register(mcp: FastMCP, get_graph: Callable) -> None:

    @mcp.resource("graph://metadata")
    def metadata() -> dict:
        """Graph metadata: node count, edge count, CRS, bbox, network_type, available attributes."""
        G = get_graph()
        nodes, _ = ox.graph_to_gdfs(G)
        return {
            "node_count": len(G.nodes),
            "edge_count": len(G.edges),
            "crs": str(G.graph.get("crs", "EPSG:4326")),
            "network_type": G.graph.get("network_type", "unknown"),
            "bbox": {
                "north": float(nodes.geometry.y.max()),
                "south": float(nodes.geometry.y.min()),
                "east": float(nodes.geometry.x.max()),
                "west": float(nodes.geometry.x.min()),
            },
            "edge_attributes": sorted({k for _, _, d in G.edges(data=True) for k in d}),
            "node_attributes": sorted({k for _, d in G.nodes(data=True) for k in d}),
        }

    @mcp.resource("graph://nodes/{node_id}")
    def node(node_id: int) -> dict:
        """Data for a single graph node by OSM node id."""
        G = get_graph()
        if node_id not in G.nodes:
            raise ValueError(f"Node {node_id} not in graph")
        data = dict(G.nodes[node_id])
        return {"node_id": node_id, **data}

    @mcp.resource("graph://edges/{u}/{v}/{key}")
    def edge(u: int, v: int, key: int = 0) -> dict:
        """Data for a single graph edge by (u, v, key). Geometry excluded."""
        G = get_graph()
        if not G.has_edge(u, v, key):
            raise ValueError(f"Edge ({u}, {v}, {key}) not in graph")
        data = dict(G[u][v][key])
        data.pop("geometry", None)
        return {"u": u, "v": v, "key": key, **data}
