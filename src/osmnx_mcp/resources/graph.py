from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    import osmnx_mcp.server as _server

    @mcp.resource("graph://graphs")
    def all_graphs() -> dict:
        """List all loaded graphs with node/edge counts and which is active."""
        graphs = {}
        for name, G in _server._graphs.items():
            graphs[name] = {
                "node_count": len(G.nodes),
                "edge_count": len(G.edges),
                "network_type": G.graph.get("network_type", "unknown"),
                "active": name == _server._active,
            }
        return {"graphs": graphs, "active": _server._active}

    @mcp.resource("graph://{name}/metadata")
    def graph_metadata(name: str) -> dict:
        """Metadata for a named graph: counts, CRS, bbox, available attributes."""
        G = _server.get_graph(name)
        nodes_data = [
            (d["y"], d["x"]) for _, d in G.nodes(data=True) if "y" in d and "x" in d
        ]
        ys = [y for y, _ in nodes_data]
        xs = [x for _, x in nodes_data]
        return {
            "name": name,
            "node_count": len(G.nodes),
            "edge_count": len(G.edges),
            "crs": str(G.graph.get("crs", "EPSG:4326")),
            "network_type": G.graph.get("network_type", "unknown"),
            "bbox": {
                "north": max(ys) if ys else None,
                "south": min(ys) if ys else None,
                "east": max(xs) if xs else None,
                "west": min(xs) if xs else None,
            },
            "edge_attributes": sorted({k for _, _, d in G.edges(data=True) for k in d}),
            "node_attributes": sorted({k for _, d in G.nodes(data=True) for k in d}),
        }

    @mcp.resource("graph://{name}/edge-attributes")
    def edge_attribute_names(name: str) -> dict:
        """List available edge attribute names in a named graph."""
        G = _server.get_graph(name)
        attrs = sorted({k for _, _, d in G.edges(data=True) for k in d})
        return {"name": name, "edge_attributes": attrs}

    @mcp.resource("graph://{name}/edge-attributes/{attribute}")
    def edge_attribute_values(name: str, attribute: str) -> dict:
        """Unique values for a named edge attribute — instant, no network call."""
        G = _server.get_graph(name)
        values: set[str] = set()
        for _, _, data in G.edges(data=True):
            val = data.get(attribute)
            if val is None:
                continue
            if isinstance(val, list):
                values.update(str(v) for v in val if v is not None)
            else:
                values.add(str(val))
        return {
            "name": name,
            "attribute": attribute,
            "values": sorted(values),
            "count": len(values),
        }

    @mcp.resource("graph://{name}/nodes/{node_id}")
    def node_data(name: str, node_id: int) -> dict:
        """Data for a single node by OSM node id."""
        G = _server.get_graph(name)
        if node_id not in G.nodes:
            raise ValueError(f"Node {node_id} not in graph '{name}'")
        return {"node_id": node_id, **dict(G.nodes[node_id])}

    @mcp.resource("graph://{name}/edges/{u}/{v}/{key}")
    def edge_data(name: str, u: int, v: int, key: int = 0) -> dict:
        """Data for a single edge by (u, v, key). Geometry excluded."""
        G = _server.get_graph(name)
        if not G.has_edge(u, v, key):
            raise ValueError(f"Edge ({u}, {v}, {key}) not in graph '{name}'")
        data = dict(G[u][v][key])
        data.pop("geometry", None)
        return {"u": u, "v": v, "key": key, **data}

    # Active-graph shortcuts for convenience
    @mcp.resource("graph://metadata")
    def active_metadata() -> dict:
        """Metadata for the currently active graph."""
        name = _server._active
        if name is None:
            return {"loaded": False, "message": "No graph loaded."}
        return graph_metadata(name)
