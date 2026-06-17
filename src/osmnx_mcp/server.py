import networkx as nx
from fastmcp import FastMCP
from osmnx_mcp.tools import (
    routing,
    stats,
    spatial,
    features,
    enrichment,
    graph_loading,
    visualization,
)
from osmnx_mcp.resources import graph as graph_resources

_graphs: dict[str, nx.MultiDiGraph] = {}
_active: str | None = None


def get_graph(name: str | None = None) -> nx.MultiDiGraph:
    target = name or _active
    if target is None or target not in _graphs:
        raise RuntimeError(
            "No graph loaded. Call load_graph_from_point, load_graph_from_place, "
            "or load_graph_from_file first."
        )
    return _graphs[target]


def get_active_name() -> str | None:
    return _active


def set_graph(G: nx.MultiDiGraph, name: str) -> None:
    global _graphs, _active
    _graphs[name] = G
    _active = name


def drop_graph(name: str) -> None:
    global _graphs, _active
    _graphs.pop(name, None)
    if _active == name:
        _active = next(iter(_graphs), None)


def list_graph_names() -> list[str]:
    return list(_graphs.keys())


def create_server(name: str = "osmnx-mcp") -> FastMCP:
    """Create an MCP server with no graph pre-loaded."""
    mcp = FastMCP(name, list_page_size=100)
    graph_loading.register(mcp)
    routing.register(mcp, get_graph)
    stats.register(mcp, get_graph)
    spatial.register(mcp, get_graph)
    features.register(mcp, get_graph)
    enrichment.register(mcp, get_graph)
    visualization.register(mcp, get_graph)
    graph_resources.register(mcp)
    return mcp


def mount(
    G: nx.MultiDiGraph, name: str = "default", server_name: str = "osmnx-mcp"
) -> FastMCP:
    """Create an MCP server with G pre-loaded under the given name."""
    set_graph(G, name)
    return create_server(server_name)
