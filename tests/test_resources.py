import asyncio
import json
import socket

import osmnx as ox
import pytest
from claude_code_sdk import ClaudeCodeOptions, ResultMessage, query
from fastmcp import Client

from osmnx_mcp import mount

QUERY_POINT = {"lng": -73.8318, "lat": 40.7108}


@pytest.fixture(scope="module")
def graph():
    G = ox.graph_from_point((40.7090, -73.8295), dist=800, network_type="drive")
    return G


@pytest.fixture(scope="module")
def mcp_server(graph):
    return mount(graph)


@pytest.mark.asyncio
async def test_metadata_resource(mcp_server, graph):
    async with Client(mcp_server) as client:
        result = await client.read_resource("graph://metadata")
        data = json.loads(result[0].text)
        assert data["node_count"] == len(graph.nodes)
        assert data["edge_count"] == len(graph.edges)
        assert "bbox" in data
        assert "edge_attributes" in data
        assert "node_attributes" in data


@pytest.mark.asyncio
async def test_node_resource(mcp_server, graph):
    node_id = next(iter(graph.nodes))
    async with Client(mcp_server) as client:
        result = await client.read_resource(f"graph://default/nodes/{node_id}")
        data = json.loads(result[0].text)
        assert data["node_id"] == node_id


@pytest.mark.asyncio
async def test_edge_resource(mcp_server, graph):
    u, v, key = next(iter(graph.edges(keys=True)))
    async with Client(mcp_server) as client:
        result = await client.read_resource(f"graph://default/edges/{u}/{v}/{key}")
        data = json.loads(result[0].text)
        assert data["u"] == u
        assert data["v"] == v
        assert "geometry" not in data


@pytest.mark.asyncio
async def test_resources_with_haiku(mcp_server, graph):
    """Drive claude-haiku-4-5 via Claude Code SDK session to exercise tools and read metadata."""
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
            max_turns=10,
        )

        async def prompt_stream():
            yield {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": (
                        f"Using the nearest_nodes tool, find the nearest node to "
                        f"({QUERY_POINT['lng']}, {QUERY_POINT['lat']}) in Kew Gardens, Queens "
                        f"and tell me its node_id. "
                        f"Then confirm the graph has more than 50 nodes by calling basic_stats."
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
            f"Expected node id in result, got: {result_text}"
        )
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    # directly verify metadata resource is intact
    async with Client(mcp_server) as mcp_client:
        meta_result = await mcp_client.read_resource("graph://metadata")
        meta = json.loads(meta_result[0].text)
        assert meta["node_count"] > 50
