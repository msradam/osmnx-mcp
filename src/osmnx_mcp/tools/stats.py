import osmnx as ox
from fastmcp import FastMCP
from typing import Callable


def _serialize_stats(result: dict) -> dict:
    out = {}
    for k, v in result.items():
        if hasattr(v, "item"):
            out[k] = v.item()
        elif isinstance(v, dict):
            out[k] = {
                str(kk): vv.item() if hasattr(vv, "item") else vv
                for kk, vv in v.items()
            }
        else:
            out[k] = v
    return out


def register(mcp: FastMCP, get_graph: Callable) -> None:

    @mcp.tool
    def basic_stats(area_km2: float | None = None) -> dict:
        """
        Compute basic street network statistics for the mounted graph.

        area_km2: optional study area in square kilometers for density metrics.
        Returns counts, lengths, and density stats as a flat dict.
        """
        G = get_graph()
        area_m2 = area_km2 * 1_000_000 if area_km2 is not None else None
        result = ox.stats.basic_stats(G, area=area_m2)
        return _serialize_stats(result)

    @mcp.tool
    def orientation_entropy() -> dict:
        """
        Compute the orientation entropy of the street network.

        Adds edge bearings automatically if not already present.
        Returns entropy (nats). Higher values indicate more grid-like or disordered networks.
        """
        G = get_graph()
        sample_edges = list(G.edges(data=True))[:1]
        if not sample_edges or "bearing" not in sample_edges[0][2]:
            G = ox.add_edge_bearings(G)
            import osmnx_mcp.server as _server
            _server._graph = G
        entropy = ox.bearing.orientation_entropy(G)
        return {"orientation_entropy": float(entropy)}

    @mcp.tool
    def streets_per_node_avg() -> dict:
        """
        Compute the average number of streets per node (intersection degree) in the graph.

        Returns the mean streets-per-node count across all nodes.
        """
        G = get_graph()
        result = ox.stats.basic_stats(G)
        return {"streets_per_node_avg": float(result.get("streets_per_node_avg", 0))}

    @mcp.tool
    def streets_per_node_proportions() -> dict:
        """
        Compute the proportion of nodes with each street count (degree distribution).

        Returns a dict mapping street count to the fraction of nodes with that count.
        """
        G = get_graph()
        result = ox.stats.basic_stats(G)
        raw = result.get("streets_per_node_proportions", {})
        return {
            str(k): v.item() if hasattr(v, "item") else float(v)
            for k, v in raw.items()
        }
