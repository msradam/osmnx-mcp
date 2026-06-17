import osmnx as ox
import networkx as nx
from fastmcp import FastMCP
from typing import Callable


def register(mcp: FastMCP, get_graph: Callable) -> None:

    @mcp.tool
    def truncate_graph_bbox(
        north: float, south: float, east: float, west: float
    ) -> dict:
        """
        Truncate the mounted graph to nodes within a bounding box.

        Returns summary of resulting node and edge counts.
        """
        G = get_graph()
        # osmnx 2.x uses ox.truncate.truncate_graph_bbox(G, bbox=(north, south, east, west))
        try:
            G_trunc = ox.truncate.truncate_graph_bbox(G, bbox=(north, south, east, west))
        except TypeError:
            G_trunc = ox.truncate.truncate_graph_bbox(G, north, south, east, west)
        # update module-level graph
        _update_graph(G_trunc)
        return {"node_count": len(G_trunc.nodes), "edge_count": len(G_trunc.edges)}

    @mcp.tool
    def truncate_graph_dist(
        lng: float, lat: float, dist_m: float, weight: str = "length"
    ) -> dict:
        """
        Truncate the mounted graph to nodes within dist_m of coordinate (lng, lat).

        weight: edge attribute used to measure distance ('length' or 'travel_time').
        Returns summary of resulting node and edge counts.
        """
        G = get_graph()
        node = ox.nearest_nodes(G, lng, lat)
        G_trunc = ox.truncate.truncate_graph_dist(G, node, dist_m, weight=weight)
        _update_graph(G_trunc)
        return {"node_count": len(G_trunc.nodes), "edge_count": len(G_trunc.edges)}

    @mcp.tool
    def largest_component() -> dict:
        """
        Reduce the mounted graph to its largest weakly connected component.

        Returns node and edge counts of the retained component.
        """
        G = get_graph()
        G_lc = ox.truncate.largest_component(G, strongly=False)
        _update_graph(G_lc)
        return {"node_count": len(G_lc.nodes), "edge_count": len(G_lc.edges)}

    @mcp.tool
    def consolidate_intersections(tolerance: float = 10.0) -> dict:
        """
        Consolidate nearby intersection nodes within tolerance meters.

        tolerance: max distance in meters between nodes to merge.
        Returns node and edge counts after consolidation.
        """
        G = get_graph()
        G_cons = ox.consolidate_intersections(G, tolerance=tolerance)
        _update_graph(G_cons)
        return {"node_count": len(G_cons.nodes), "edge_count": len(G_cons.edges)}


def _update_graph(G: nx.MultiDiGraph) -> None:
    """Replace the module-level graph used by get_graph."""
    import osmnx_mcp.server as _server
    _server._graph = G
