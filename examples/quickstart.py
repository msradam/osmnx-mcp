#!/usr/bin/env python3
"""
Quickstart: load a Kew Gardens, Queens drive network and call the MCP tools
directly via the FastMCP in-process client.

Run with:
    uv run python examples/quickstart.py
"""

import asyncio

import osmnx as ox
from fastmcp import Client

from osmnx_mcp import mount

CENTER = (40.7090, -73.8295)  # Kew Gardens, Queens
ORIG = {"lng": -73.8318, "lat": 40.7108}
DEST = {"lng": -73.8265, "lat": 40.7072}


async def main() -> None:
    print("Downloading graph (Kew Gardens, 800 m radius)...")
    G = ox.graph_from_point(CENTER, dist=800, network_type="drive")
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    print(f"  {len(G.nodes)} nodes, {len(G.edges)} edges")

    server = mount(G)

    async with Client(server) as client:
        tools = await client.list_tools()
        print(f"\nAvailable tools ({len(tools)}):")
        for t in tools:
            print(f"  {t.name}")

        print("\n--- nearest_nodes ---")
        r = await client.call_tool("nearest_nodes", ORIG)
        print(" ", r.data)

        print("\n--- basic_stats ---")
        r = await client.call_tool("basic_stats", {})
        s = r.data
        print(f"  nodes={s['n']}, edges={s['m']}, avg_degree={s.get('k_avg', 0):.2f}")

        print("\n--- orientation_entropy ---")
        r = await client.call_tool("orientation_entropy", {})
        print(f"  entropy={r.data['orientation_entropy']:.4f}")

        print("\n--- shortest_path (travel_time) ---")
        r = await client.call_tool(
            "shortest_path",
            {
                "orig_lng": ORIG["lng"],
                "orig_lat": ORIG["lat"],
                "dest_lng": DEST["lng"],
                "dest_lat": DEST["lat"],
                "weight": "travel_time",
            },
        )
        p = r.data
        print(f"  {p['length_m']:.0f} m, {p['travel_time_s']:.0f} s")
        print(f"  {len(p['path'])} nodes in path")

        print("\n--- k_shortest_paths (k=3) ---")
        r = await client.call_tool(
            "k_shortest_paths",
            {
                "orig_lng": ORIG["lng"],
                "orig_lat": ORIG["lat"],
                "dest_lng": DEST["lng"],
                "dest_lat": DEST["lat"],
                "k": 3,
                "weight": "length",
            },
        )
        for i, path in enumerate(r.data, 1):
            print(f"  path {i}: {path['length_m']:.0f} m")


if __name__ == "__main__":
    asyncio.run(main())
