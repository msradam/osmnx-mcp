import sys
from pathlib import Path

import typer

app = typer.Typer(
    name="osmnx-mcp",
    help="MCP server for OSMnx street network graphs.",
    no_args_is_help=True,
)

_PROJECT_DIR = Path(__file__).parent.parent.parent.parent  # repo root


@app.command()
def serve(
    place: str = typer.Option(None, "--place", help="Geocodable place name."),
    graphml: str = typer.Option(None, "--graphml", help="Path to a GraphML file."),
    lat: float = typer.Option(None, "--lat", help="Latitude of center point."),
    lng: float = typer.Option(None, "--lng", help="Longitude of center point."),
    dist: int = typer.Option(1000, "--dist", help="Radius in meters (default 1000)."),
    network_type: str = typer.Option(
        "drive",
        "--network-type",
        help="Network type: drive, walk, bike, all.",
    ),
    name: str = typer.Option(
        "default", "--name", help="Graph name in multi-graph sessions."
    ),
) -> None:
    """Start the MCP server (stdio transport, compatible with Claude Desktop and Claude Code)."""
    import osmnx as ox
    from osmnx_mcp.server import create_server, mount

    if graphml:
        typer.echo(f"Loading '{graphml}'...", err=True)
        G = ox.load_graphml(graphml)
        typer.echo(f"Loaded: {len(G.nodes)} nodes, {len(G.edges)} edges", err=True)
        server = mount(G, name=name)
    elif place:
        typer.echo(f"Fetching '{place}' ({network_type}) from OSM...", err=True)
        G = ox.graph_from_place(place, network_type=network_type)
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        typer.echo(f"Loaded: {len(G.nodes)} nodes, {len(G.edges)} edges", err=True)
        server = mount(G, name=name)
    elif lat is not None and lng is not None:
        typer.echo(
            f"Fetching ({lat}, {lng}) dist={dist}m ({network_type})...", err=True
        )
        G = ox.graph_from_point((lat, lng), dist=dist, network_type=network_type)
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        typer.echo(f"Loaded: {len(G.nodes)} nodes, {len(G.edges)} edges", err=True)
        server = mount(G, name=name)
    else:
        typer.echo(
            "Starting empty — use load_graph_from_point to load a graph.", err=True
        )
        server = create_server()

    server.run()


@app.command()
def doctor() -> None:
    """Diagnose the environment: versions, imports, connectivity, and suggested config."""
    import importlib
    import shutil
    import subprocess

    ok = typer.style("✓", fg=typer.colors.GREEN, bold=True)
    fail = typer.style("✗", fg=typer.colors.RED, bold=True)
    warn = typer.style("!", fg=typer.colors.YELLOW, bold=True)

    typer.echo("\nosmnx-mcp doctor\n" + "─" * 40)

    # Python version
    v = sys.version_info
    if v >= (3, 12):
        typer.echo(f"  {ok}  Python {v.major}.{v.minor}.{v.micro}")
    else:
        typer.echo(f"  {fail}  Python {v.major}.{v.minor}.{v.micro} (need ≥ 3.12)")

    # uv
    uv_path = shutil.which("uv")
    if uv_path:
        try:
            uv_ver = subprocess.check_output(["uv", "--version"], text=True).split()[1]
            typer.echo(f"  {ok}  uv {uv_ver}  ({uv_path})")
        except Exception:
            typer.echo(f"  {ok}  uv found ({uv_path})")
    else:
        typer.echo(f"  {fail}  uv not found in PATH")

    # Package imports + versions
    packages = [
        ("osmnx", "osmnx"),
        ("fastmcp", "fastmcp"),
        ("networkx", "networkx"),
        ("matplotlib", "matplotlib"),
        ("scipy", "scipy"),
        ("sklearn", "scikit-learn"),
    ]
    for mod, display in packages:
        try:
            m = importlib.import_module(mod)
            ver = getattr(m, "__version__", "?")
            typer.echo(f"  {ok}  {display} {ver}")
        except ImportError:
            typer.echo(f"  {fail}  {display} — not importable")

    # osmnx-mcp itself
    try:
        import importlib.util

        if importlib.util.find_spec("osmnx_mcp") is not None:
            typer.echo(f"  {ok}  osmnx-mcp importable")
        else:
            typer.echo(f"  {fail}  osmnx-mcp not found")
    except Exception as e:
        typer.echo(f"  {fail}  osmnx-mcp import failed: {e}")

    # Overpass API connectivity
    typer.echo("\n  Connectivity checks (may take a few seconds)...")
    try:
        import osmnx as ox

        ox.geocode("Times Square, New York")
        typer.echo(f"  {ok}  Nominatim reachable")
    except Exception as e:
        typer.echo(f"  {warn}  Nominatim: {e}")

    try:
        import osmnx as ox

        ox.features_from_point((40.758, -73.985), tags={"amenity": "cafe"}, dist=100)
        typer.echo(f"  {ok}  Overpass API reachable")
    except Exception as e:
        typer.echo(f"  {warn}  Overpass API: {e}")

    # Project directory
    venv_exe = _PROJECT_DIR / ".venv" / "bin" / "osmnx-mcp"
    typer.echo(f"\n  Project dir : {_PROJECT_DIR}")
    typer.echo(
        f"  venv binary : {venv_exe} {'(exists)' if venv_exe.exists() else '(not found)'}"
    )

    # Suggested configs
    project_dir = str(_PROJECT_DIR)
    typer.echo("\n" + "─" * 40)
    typer.echo(
        "Claude Desktop  ~/Library/Application Support/Claude/claude_desktop_config.json"
    )
    typer.echo("─" * 40)
    config = f"""\
{{
  "mcpServers": {{
    "osmnx-mcp": {{
      "command": "uv",
      "args": ["run", "--project", "{project_dir}", "osmnx-mcp", "serve"]
    }}
  }}
}}"""
    typer.echo(config)

    typer.echo("\n" + "─" * 40)
    typer.echo("Claude Code  .mcp.json  (project root)")
    typer.echo("─" * 40)
    mcp_json = f"""\
{{
  "mcpServers": {{
    "osmnx-mcp": {{
      "command": "uv",
      "args": ["run", "osmnx-mcp", "serve"],
      "cwd": "{project_dir}",
      "type": "stdio"
    }}
  }}
}}"""
    typer.echo(mcp_json)
    typer.echo()


@app.command()
def version() -> None:
    """Print version and dependency info."""
    import importlib

    packages = ["osmnx", "fastmcp", "networkx", "matplotlib", "scipy"]
    typer.echo("osmnx-mcp 0.1.0")
    for pkg in packages:
        try:
            m = importlib.import_module(pkg)
            typer.echo(f"  {pkg} {getattr(m, '__version__', '?')}")
        except ImportError:
            typer.echo(f"  {pkg} not installed")


def main() -> None:
    app()
