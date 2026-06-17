import asyncio
import socket

import osmnx as ox
import pytest
from claude_code_sdk import ClaudeCodeOptions, ResultMessage, query
from fastmcp import Client

from osmnx_mcp import mount


@pytest.fixture(scope="module")
def graph():
    G = ox.graph_from_point((40.7090, -73.8295), dist=800, network_type="drive")
    return G


@pytest.fixture(scope="module")
def mcp_server(graph):
    return mount(graph)


@pytest.mark.asyncio
async def test_basic_stats_direct(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("basic_stats", {})
        data = result.data
        assert "n" in data
        assert data["n"] > 0


@pytest.mark.asyncio
async def test_basic_stats_with_area(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("basic_stats", {"area_km2": 2.5})
        data = result.data
        assert isinstance(data, dict) and len(data) > 0


@pytest.mark.asyncio
async def test_orientation_entropy_direct(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("orientation_entropy", {})
        data = result.data
        assert "orientation_entropy" in data
        assert data["orientation_entropy"] > 0


@pytest.mark.asyncio
async def test_streets_per_node_avg(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("streets_per_node_avg", {})
        data = result.data
        assert "streets_per_node_avg" in data
        assert data["streets_per_node_avg"] > 0


@pytest.mark.asyncio
async def test_streets_per_node_proportions(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("streets_per_node_proportions", {})
        data = result.data
        assert isinstance(data, dict)
        total = sum(data.values())
        assert abs(total - 1.0) < 0.01


@pytest.mark.asyncio
async def test_stats_with_haiku(mcp_server):
    """Drive claude-haiku-4-5 via Claude Code SDK session to exercise stats tools."""
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
                        "What are the basic stats of this Kew Gardens, Queens street network? "
                        "Also report the orientation entropy. Give me the key numbers."
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
