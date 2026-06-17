import networkx as nx
from fastmcp import FastMCP
from osmnx_mcp.tools import routing, stats, spatial, features, enrichment, graph_loading
from osmnx_mcp.resources import graph as graph_resources

_graph: nx.MultiDiGraph | None = None


def get_graph() -> nx.MultiDiGraph:
    if _graph is None:
        raise RuntimeError(
            "No graph loaded. Call load_graph_from_point or load_graph_from_place first."
        )
    return _graph


def create_server(name: str = "osmnx-mcp") -> FastMCP:
    """Create an MCP server with no graph pre-loaded. Use load_graph_* tools to load one."""
    mcp = FastMCP(name, list_page_size=100)
    graph_loading.register(mcp, get_graph)
    routing.register(mcp, get_graph)
    stats.register(mcp, get_graph)
    spatial.register(mcp, get_graph)
    features.register(mcp, get_graph)
    enrichment.register(mcp, get_graph)
    graph_resources.register(mcp, get_graph)
    return mcp


def mount(G: nx.MultiDiGraph, name: str = "osmnx-mcp") -> FastMCP:
    """Create an MCP server with G pre-loaded."""
    global _graph
    _graph = G
    return create_server(name)
