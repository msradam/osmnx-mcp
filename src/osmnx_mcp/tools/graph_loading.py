import asyncio
import math
import osmnx as ox
from fastmcp import FastMCP, Context


def register(mcp: FastMCP) -> None:
    import osmnx_mcp.server as _server

    @mcp.tool
    async def load_graph_from_point(
        lat: float,
        lng: float,
        dist_m: int = 1000,
        name: str = "default",
        network_type: str = "drive",
        add_speeds: bool = True,
        add_travel_times: bool = True,
        ctx: Context = None,
    ) -> dict:
        """
        Download and load an OSMnx street network centered at (lat, lng).

        dist_m: radius in meters (default 1000; city-scale use ~5000+).
        name: graph name for multi-graph sessions (default 'default').
        network_type: 'drive', 'walk', 'bike', or 'all'.
        add_speeds / add_travel_times: enrich edges for travel-time routing.

        Reports progress. Replaces any existing graph with the same name.
        """
        if ctx:
            await ctx.info(
                f"Downloading {network_type} network at ({lat}, {lng}), dist={dist_m}m..."
            )
            await ctx.report_progress(0, 4)

        G = await asyncio.to_thread(
            ox.graph_from_point, (lat, lng), dist=dist_m, network_type=network_type
        )
        if ctx:
            await ctx.info(f"Loaded {len(G.nodes)} nodes, {len(G.edges)} edges.")
            await ctx.report_progress(1, 4)

        if add_speeds:
            if ctx:
                await ctx.info("Imputing edge speeds...")
                await ctx.report_progress(2, 4)
            G = await asyncio.to_thread(ox.add_edge_speeds, G)

        if add_travel_times:
            if ctx:
                await ctx.info("Computing travel times...")
                await ctx.report_progress(3, 4)
            G = await asyncio.to_thread(ox.add_edge_travel_times, G)

        _server.set_graph(G, name)
        if ctx:
            await ctx.report_progress(4, 4)

        return {
            "status": "loaded",
            "name": name,
            "node_count": len(G.nodes),
            "edge_count": len(G.edges),
            "center": {"lat": lat, "lng": lng},
            "dist_m": dist_m,
            "network_type": network_type,
        }

    @mcp.tool
    async def load_graph_from_place(
        place: str,
        name: str = "default",
        network_type: str = "drive",
        add_speeds: bool = True,
        add_travel_times: bool = True,
        ctx: Context = None,
    ) -> dict:
        """
        Download and load an OSMnx street network for a named place.

        place: geocodable name, e.g. 'Manhattan, New York, USA'.
               Requires Nominatim to return a polygon — prefer load_graph_from_point
               for neighborhoods that lack one.
        name: graph name for multi-graph sessions (default 'default').
        network_type: 'drive', 'walk', 'bike', or 'all'.
        """
        if ctx:
            await ctx.info(
                f"Geocoding and downloading {network_type} network for '{place}'..."
            )
            await ctx.report_progress(0, 4)

        G = await asyncio.to_thread(
            ox.graph_from_place, place, network_type=network_type
        )
        if ctx:
            await ctx.info(f"Loaded {len(G.nodes)} nodes, {len(G.edges)} edges.")
            await ctx.report_progress(1, 4)

        if add_speeds:
            if ctx:
                await ctx.info("Imputing edge speeds...")
                await ctx.report_progress(2, 4)
            G = await asyncio.to_thread(ox.add_edge_speeds, G)

        if add_travel_times:
            if ctx:
                await ctx.info("Computing travel times...")
                await ctx.report_progress(3, 4)
            G = await asyncio.to_thread(ox.add_edge_travel_times, G)

        _server.set_graph(G, name)
        if ctx:
            await ctx.report_progress(4, 4)

        return {
            "status": "loaded",
            "name": name,
            "place": place,
            "node_count": len(G.nodes),
            "edge_count": len(G.edges),
            "network_type": network_type,
        }

    @mcp.tool
    async def load_graph_from_file(
        path: str,
        name: str = "default",
        add_speeds: bool = False,
        add_travel_times: bool = False,
        ctx: Context = None,
    ) -> dict:
        """
        Load an OSMnx graph from a GraphML file on disk.

        path: absolute path to a .graphml file (saved with save_graph or osmnx.save_graphml).
        name: graph name for multi-graph sessions (default 'default').
        add_speeds / add_travel_times: re-enrich after loading (only needed if not already present).

        This is the fast path for city-sized graphs — download once, save, reload instantly.
        """
        if ctx:
            await ctx.info(f"Loading graph from {path}...")
            await ctx.report_progress(0, 3)

        G = await asyncio.to_thread(ox.load_graphml, path)
        if ctx:
            await ctx.info(f"Loaded {len(G.nodes)} nodes, {len(G.edges)} edges.")
            await ctx.report_progress(1, 3)

        if add_speeds:
            if ctx:
                await ctx.info("Imputing edge speeds...")
            G = await asyncio.to_thread(ox.add_edge_speeds, G)

        if add_travel_times:
            if ctx:
                await ctx.info("Computing travel times...")
            G = await asyncio.to_thread(ox.add_edge_travel_times, G)

        _server.set_graph(G, name)
        if ctx:
            await ctx.report_progress(3, 3)

        return {
            "status": "loaded",
            "name": name,
            "path": path,
            "node_count": len(G.nodes),
            "edge_count": len(G.edges),
            "network_type": G.graph.get("network_type", "unknown"),
        }

    @mcp.tool
    async def save_graph(
        path: str,
        name: str | None = None,
        ctx: Context = None,
    ) -> dict:
        """
        Save a graph to a GraphML file for fast reloading.

        path: destination file path (will be created or overwritten).
        name: graph to save (default: active graph).

        Use this after a slow city-scale download to avoid re-downloading.
        """
        G = _server.get_graph(name)
        graph_name = name or _server._active
        if ctx:
            await ctx.info(f"Saving '{graph_name}' ({len(G.nodes)} nodes) to {path}...")
        await asyncio.to_thread(ox.save_graphml, G, path)
        return {"status": "saved", "name": graph_name, "path": path}

    @mcp.tool
    def list_graphs() -> dict:
        """List all loaded graphs with their sizes and which is active."""
        graphs = {}
        for n, G in _server._graphs.items():
            graphs[n] = {
                "node_count": len(G.nodes),
                "edge_count": len(G.edges),
                "network_type": G.graph.get("network_type", "unknown"),
                "active": n == _server._active,
            }
        return {"graphs": graphs, "active": _server._active, "count": len(graphs)}

    @mcp.tool
    def set_active_graph(name: str) -> dict:
        """
        Switch the active graph by name.

        All tools (routing, stats, visualization) operate on the active graph.
        Use list_graphs() to see available names.
        """
        if name not in _server._graphs:
            available = list(_server._graphs.keys())
            raise ValueError(f"Graph '{name}' not found. Available: {available}")
        _server._active = name
        G = _server._graphs[name]
        return {
            "active": name,
            "node_count": len(G.nodes),
            "edge_count": len(G.edges),
        }

    @mcp.tool
    def drop_graph(name: str) -> dict:
        """
        Remove a named graph from memory.

        If the dropped graph was active, the active graph is switched to the
        next available graph (or None if none remain).
        """
        if name not in _server._graphs:
            raise ValueError(f"Graph '{name}' not found.")
        node_count = len(_server._graphs[name].nodes)
        _server.drop_graph(name)
        return {
            "dropped": name,
            "nodes_freed": node_count,
            "active": _server._active,
        }

    @mcp.tool
    async def subgraph_from_point(
        lat: float,
        lng: float,
        dist_m: float,
        source_name: str,
        target_name: str,
        ctx: Context = None,
    ) -> dict:
        """
        Extract a geographic subgraph within dist_m of (lat, lng) from a source graph.

        source_name: name of the already-loaded graph to extract from (e.g. a city graph).
        target_name: name to store the resulting subgraph under.

        This is the city-scale workflow: load an entire city once, then extract
        neighborhood subgraphs for detailed analysis without re-downloading.
        Returns the new subgraph as the active graph.
        """
        if source_name not in _server._graphs:
            raise ValueError(f"Source graph '{source_name}' not found.")

        G = _server._graphs[source_name]
        if ctx:
            await ctx.info(
                f"Extracting {dist_m}m subgraph from '{source_name}' "
                f"({len(G.nodes)} nodes) around ({lat}, {lng})..."
            )
            await ctx.report_progress(0, 2)

        dist_deg_lat = dist_m / 111320
        dist_deg_lng = dist_m / (111320 * math.cos(math.radians(lat)))
        north = lat + dist_deg_lat
        south = lat - dist_deg_lat
        east = lng + dist_deg_lng
        west = lng - dist_deg_lng

        G_sub = await asyncio.to_thread(
            ox.truncate.truncate_graph_bbox,
            G,
            bbox=(north, south, east, west),
        )
        _server.set_graph(G_sub, target_name)

        if ctx:
            await ctx.report_progress(2, 2)

        return {
            "status": "extracted",
            "source": source_name,
            "target": target_name,
            "node_count": len(G_sub.nodes),
            "edge_count": len(G_sub.edges),
            "bbox": {"north": north, "south": south, "east": east, "west": west},
        }

    @mcp.tool
    def graph_info(name: str | None = None) -> dict:
        """
        Return metadata about a loaded graph.

        name: graph to inspect (default: active graph).
        Returns counts, bbox, CRS, and available edge/node attributes.
        Always call this first after loading — do NOT use features_from_* for
        data already in the graph; use graph://{name}/edge-attributes/{attribute} instead.
        """
        try:
            G = _server.get_graph(name)
        except RuntimeError:
            return {
                "loaded": False,
                "message": "No graph loaded. Call load_graph_from_point first.",
            }
        graph_name = name or _server._active
        ys = [d["y"] for _, d in G.nodes(data=True) if "y" in d]
        xs = [d["x"] for _, d in G.nodes(data=True) if "x" in d]
        return {
            "loaded": True,
            "name": graph_name,
            "active": graph_name == _server._active,
            "node_count": len(G.nodes),
            "edge_count": len(G.edges),
            "crs": str(G.graph.get("crs", "epsg:4326")),
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
