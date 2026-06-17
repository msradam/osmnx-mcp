import asyncio
import socket

import osmnx as ox
import pytest
from claude_code_sdk import ClaudeCodeOptions, ResultMessage, query
from fastmcp import Client

from osmnx_mcp import mount

# Two points in Kew Gardens, Queens: near the LIRR station and near Queens Blvd
ORIG = {"lng": -73.8318, "lat": 40.7108}
DEST = {"lng": -73.8265, "lat": 40.7072}


@pytest.fixture(scope="module")
def graph():
    G = ox.graph_from_point((40.7090, -73.8295), dist=800, network_type="drive")
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    return G


@pytest.fixture(scope="module")
def mcp_server(graph):
    return mount(graph)


@pytest.mark.asyncio
async def test_nearest_nodes_direct(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("nearest_nodes", ORIG)
        data = result.data
        assert "node_id" in data
        assert isinstance(data["node_id"], int)


@pytest.mark.asyncio
async def test_nearest_edges_direct(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("nearest_edges", ORIG)
        data = result.data
        assert "u" in data and "v" in data and "key" in data


@pytest.mark.asyncio
async def test_shortest_path_direct(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "shortest_path",
            {
                "orig_lng": ORIG["lng"],
                "orig_lat": ORIG["lat"],
                "dest_lng": DEST["lng"],
                "dest_lat": DEST["lat"],
                "weight": "travel_time",
            },
        )
        data = result.data
        assert data["path"] is not None
        assert data["length_m"] > 0
        assert data["travel_time_s"] is not None and data["travel_time_s"] > 0


@pytest.mark.asyncio
async def test_k_shortest_paths_direct(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
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
        data = result.data
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "path" in data[0] and "length_m" in data[0]


@pytest.mark.asyncio
async def test_routing_with_haiku(mcp_server):
    """Drive claude-haiku-4-5 via Claude Code SDK session to exercise routing tools."""
    with socket.socket() as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    server_task = asyncio.create_task(
        mcp_server.run_http_async(
            transport="streamable-http",
            host="127.0.0.1",
            port=port,
            show_banner=False,
        )
    )
    await asyncio.sleep(0.5)

    try:
        opts = ClaudeCodeOptions(
            model="claude-haiku-4-5",
            mcp_servers={
                "osmnx-mcp": {"type": "http", "url": f"http://127.0.0.1:{port}/mcp"}
            },
            permission_mode="bypassPermissions",
            max_turns=5,
        )

        async def prompt_stream():
            yield {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": (
                        f"Find the shortest path by travel time from "
                        f"({ORIG['lng']}, {ORIG['lat']}) to ({DEST['lng']}, {DEST['lat']}) "
                        f"in Kew Gardens, Queens. Report the length in meters and travel time in seconds."
                    ),
                },
            }

        result_text = ""
        try:
            async for msg in query(prompt=prompt_stream(), options=opts):
                if isinstance(msg, ResultMessage):
                    result_text = msg.result or ""
        except Exception:
            if not result_text:
                pytest.skip("Claude API unavailable (rate limit or session constraint)")

        assert any(c.isdigit() for c in result_text), (
            f"Expected numeric result, got: {result_text}"
        )
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
