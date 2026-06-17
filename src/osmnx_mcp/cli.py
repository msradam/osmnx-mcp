import argparse
import sys
import osmnx as ox
from osmnx_mcp.server import create_server, mount


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an MCP server for an OSMnx street network graph."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--place", help="Geocodable place name to fetch from OSM.")
    source.add_argument("--graphml", help="Path to a GraphML file to load.")
    parser.add_argument(
        "--lat",
        type=float,
        help="Latitude of center point (use with --lng and --dist).",
    )
    parser.add_argument(
        "--lng",
        type=float,
        help="Longitude of center point (use with --lat and --dist).",
    )
    parser.add_argument(
        "--dist",
        type=int,
        default=1000,
        help="Radius in meters when using --lat/--lng (default: 1000).",
    )
    parser.add_argument(
        "--network-type",
        default="drive",
        choices=["drive", "walk", "bike", "all"],
        help="Network type when fetching from OSM (default: drive).",
    )
    args = parser.parse_args()

    if args.graphml:
        G = ox.load_graphml(args.graphml)
        print(f"Graph: {len(G.nodes)} nodes, {len(G.edges)} edges", file=sys.stderr)
        server = mount(G)
    elif args.place:
        print(
            f"Fetching '{args.place}' ({args.network_type}) from OSM...",
            file=sys.stderr,
        )
        G = ox.graph_from_place(args.place, network_type=args.network_type)
        print(f"Graph: {len(G.nodes)} nodes, {len(G.edges)} edges", file=sys.stderr)
        server = mount(G)
    elif args.lat is not None and args.lng is not None:
        print(
            f"Fetching point ({args.lat}, {args.lng}) dist={args.dist}m "
            f"({args.network_type}) from OSM...",
            file=sys.stderr,
        )
        G = ox.graph_from_point(
            (args.lat, args.lng), dist=args.dist, network_type=args.network_type
        )
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        print(f"Graph: {len(G.nodes)} nodes, {len(G.edges)} edges", file=sys.stderr)
        server = mount(G)
    else:
        print(
            "No graph specified — starting empty. Use load_graph_from_point to load one.",
            file=sys.stderr,
        )
        server = create_server()

    server.run()
