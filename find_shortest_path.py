#!/usr/bin/env python3
import osmnx as ox

# Coordinates in (lon, lat) order
origin = (-73.8318, 40.7108)
destination = (-73.8265, 40.7072)

print("Fetching Kew Gardens street network...")
# Use bbox around the coordinates (bbox format: left, bottom, right, top)
bbox = (-73.8375, 40.7012, -73.8205, 40.7168)
G = ox.graph_from_bbox(bbox=bbox, network_type="drive")
print(f"Graph loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")

print("\nAdding edge speeds...")
G = ox.add_edge_speeds(G)
print(
    f"Edges with speed_kph: {sum(1 for _, _, d in G.edges(data=True) if 'speed_kph' in d)}"
)

print("Adding edge travel times...")
G = ox.add_edge_travel_times(G)
print(
    f"Edges with travel_time: {sum(1 for _, _, d in G.edges(data=True) if 'travel_time' in d)}"
)

print(f"\nFinding shortest path by travel time from {origin} to {destination}...")
orig_node = ox.nearest_nodes(G, origin[0], origin[1])
dest_node = ox.nearest_nodes(G, destination[0], destination[1])
print(f"Origin node: {orig_node}, Destination node: {dest_node}")

path = ox.shortest_path(G, orig_node, dest_node, weight="travel_time")
if path:
    length = sum(G[u][v][0].get("length", 0) for u, v in zip(path[:-1], path[1:]))
    travel_time = sum(
        G[u][v][0].get("travel_time", 0) for u, v in zip(path[:-1], path[1:])
    )
    print("\nShortest path by travel time:")
    print(f"  Path length: {length:.1f} meters")
    print(f"  Travel time: {travel_time:.1f} seconds")
    print(f"  Number of nodes in path: {len(path)}")
else:
    print("No path found!")
