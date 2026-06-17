import networkx as nx
from fastmcp import FastMCP
from osmnx_mcp.tools import routing, stats, spatial, features, enrichment
from osmnx_mcp.resources import graph as graph_resources

_graph: nx.MultiDiGraph | None = None


def get_graph() -> nx.MultiDiGraph:
    if _graph is None:
        raise RuntimeError("No graph mounted. Call mount(G) first.")
    return _graph


def mount(G: nx.MultiDiGraph, name: str = "osmnx-mcp") -> FastMCP:
    global _graph
    _graph = G
    mcp = FastMCP(name, list_page_size=100)
    routing.register(mcp, get_graph)
    stats.register(mcp, get_graph)
    spatial.register(mcp, get_graph)
    features.register(mcp, get_graph)
    enrichment.register(mcp, get_graph)
    graph_resources.register(mcp, get_graph)
    return mcp
