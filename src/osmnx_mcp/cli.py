import argparse
import sys
import osmnx as ox
from osmnx_mcp.server import mount


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an MCP server for an OSMnx street network graph."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--place", help="Geocodable place name to fetch from OSM.")
    source.add_argument("--graphml", help="Path to a GraphML file to load.")
    parser.add_argument(
        "--network-type",
        default="drive",
        choices=["drive", "walk", "bike", "all"],
        help="Network type when fetching by place (default: drive).",
    )
    args = parser.parse_args()

    if args.graphml:
        G = ox.load_graphml(args.graphml)
    else:
        print(f"Fetching '{args.place}' ({args.network_type}) from OSM...", file=sys.stderr)
        G = ox.graph_from_place(args.place, network_type=args.network_type)

    print(f"Graph: {len(G.nodes)} nodes, {len(G.edges)} edges", file=sys.stderr)
    server = mount(G)
    server.run()
