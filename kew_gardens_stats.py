#!/usr/bin/env python3
import osmnx as ox
import numpy as np

# Fetch Kew Gardens street network using bbox
# Kew Gardens approximate bounds
print("Fetching Kew Gardens street network...")
G = ox.graph_from_bbox(
    north=40.7174, south=40.7042, east=-73.8214, west=-73.8368, network_type="drive"
)

# Basic stats
num_nodes = len(G.nodes)
num_edges = len(G.edges)
area_sq_m = ox.features_from_place("Kew Gardens, Queens, New York, USA")

# Calculate basic stats
avg_degree = 2 * num_edges / num_nodes
total_length = sum(d.get("length", 0) for u, v, d in G.edges(data=True))
total_length_km = total_length / 1000

# Street orientation analysis
bearings = ox.bearing.get_bearing(G)
bearings_array = np.array(list(bearings.values()))

# Compute orientation entropy (using 45-degree bins)
bin_size = 45
num_bins = int(360 / bin_size)
bins = np.arange(0, 360, bin_size)
hist, _ = np.histogram(bearings_array, bins=bins + [360])
hist = hist[hist > 0]  # Remove empty bins
probs = hist / hist.sum()
orientation_entropy = -np.sum(probs * np.log2(probs))
max_entropy = np.log2(num_bins)

print("\n=== BASIC STATS ===")
print(f"Nodes: {num_nodes:,}")
print(f"Edges: {num_edges:,}")
print(f"Average degree: {avg_degree:.2f}")
print(f"Total street length: {total_length_km:.1f} km")

print("\n=== ORIENTATION ENTROPY ===")
print(f"Orientation entropy: {orientation_entropy:.3f} bits")
print(f"Max possible entropy ({num_bins} bins): {max_entropy:.3f} bits")
print(f"Normalized entropy: {orientation_entropy / max_entropy:.3f}")
print(f"Number of non-empty orientation bins: {len(hist)}")
