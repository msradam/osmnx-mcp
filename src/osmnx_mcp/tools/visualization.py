import io
from typing import Callable

import matplotlib
import osmnx as ox
from fastmcp import FastMCP
from fastmcp.utilities.types import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _fig_to_image(fig: plt.Figure, dpi: int = 150) -> Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(data=buf.read(), format="png")


def register(mcp: FastMCP, get_graph: Callable) -> None:

    @mcp.tool
    def plot_graph(
        figsize_w: float = 10.0,
        figsize_h: float = 10.0,
        edge_color: str = "#333333",
        bgcolor: str = "white",
        node_size: float = 0,
    ) -> Image:
        """
        Render the active street network as a static map image.

        Returns a PNG image suitable for display in Claude Desktop.
        """
        G = get_graph()
        fig, _ = ox.plot_graph(
            G,
            figsize=(figsize_w, figsize_h),
            edge_color=edge_color,
            bgcolor=bgcolor,
            node_size=node_size,
            show=False,
            close=False,
        )
        return _fig_to_image(fig)

    @mcp.tool
    def plot_route_from_path(
        route: list[int],
        route_color: str = "#cc0000",
        figsize_w: float = 10.0,
        figsize_h: float = 10.0,
    ) -> Image:
        """
        Plot a route given a node sequence from shortest_path or k_shortest_paths.

        route: list of node IDs as returned by shortest_path['path'].
        Use this to visualize a route you've already computed — compose with
        shortest_path or k_shortest_paths to inspect the path before plotting.
        Returns a PNG image.
        """
        G = get_graph()
        fig, _ = ox.plot_graph_route(
            G,
            route,
            figsize=(figsize_w, figsize_h),
            route_color=route_color,
            route_linewidth=4,
            route_alpha=0.8,
            orig_dest_size=100,
            node_size=0,
            bgcolor="white",
            edge_color="#cccccc",
            edge_linewidth=0.5,
            show=False,
            close=False,
        )
        return _fig_to_image(fig)

    @mcp.tool
    def plot_route(
        orig_lng: float,
        orig_lat: float,
        dest_lng: float,
        dest_lat: float,
        weight: str = "length",
        route_color: str = "#cc0000",
        figsize_w: float = 10.0,
        figsize_h: float = 10.0,
    ) -> Image:
        """
        Plot the shortest path between two coordinates on the active street network.

        Convenience wrapper — use shortest_path + plot_route_from_path if you need
        to inspect or compare the path before rendering.
        weight: 'length' (meters) or 'travel_time' (seconds, requires enriched graph).
        Returns a PNG image with the route highlighted.
        """
        G = get_graph()
        orig = ox.nearest_nodes(G, orig_lng, orig_lat)
        dest = ox.nearest_nodes(G, dest_lng, dest_lat)
        route = ox.shortest_path(G, orig, dest, weight=weight)
        if route is None:
            raise ValueError(f"No {weight} path found between the given coordinates.")
        fig, _ = ox.plot_graph_route(
            G,
            route,
            figsize=(figsize_w, figsize_h),
            route_color=route_color,
            route_linewidth=4,
            route_alpha=0.8,
            orig_dest_size=100,
            node_size=0,
            bgcolor="white",
            edge_color="#cccccc",
            edge_linewidth=0.5,
            show=False,
            close=False,
        )
        return _fig_to_image(fig)

    @mcp.tool
    def plot_orientation(
        num_bins: int = 36,
        figsize_w: float = 5.0,
        figsize_h: float = 5.0,
        title: str = "Street Orientation",
    ) -> Image:
        """
        Plot a polar histogram of street orientations (rose diagram).

        Reveals the grid structure (or lack thereof) of the street network.
        Returns a PNG image.
        """
        G = get_graph()
        fig, _ = ox.plot_orientation(
            G,
            num_bins=num_bins,
            figsize=(figsize_w, figsize_h),
            title=title,
            show=False,
            close=False,
        )
        return _fig_to_image(fig)

    @mcp.tool
    def plot_figure_ground(
        figsize_w: float = 10.0,
        figsize_h: float = 10.0,
        edge_color: str = "white",
        bgcolor: str = "#111111",
        edge_linewidth: float = 1.5,
    ) -> Image:
        """
        Render the street network as a high-contrast figure-ground diagram.

        Returns a PNG image suitable as a cartographic visualization.
        """
        G = get_graph()
        fig, _ = ox.plot_graph(
            G,
            figsize=(figsize_w, figsize_h),
            edge_color=edge_color,
            bgcolor=bgcolor,
            node_size=0,
            edge_linewidth=edge_linewidth,
            show=False,
            close=False,
        )
        return _fig_to_image(fig)
