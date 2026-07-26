# src/utils/renderer.py

from pathlib import Path
from typing import Any, Dict, Tuple
import numpy as np

# Force non-interactive Agg backend for headless rendering
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Color palette for Spatial Location Map (Model 1)
SPATIAL_COLOR_MAP = {
    "x_min": "#00FFFF",  # Light Cyan
    "x_max": "#008080",  # Dark Teal
    "y_min": "#90EE90",  # Soft Green
    "y_max": "#228B22",  # Forest Green
    "z_min": "#FFFFE0",  # Light Yellow
    "z_max": "#FFA500",  # Warm Orange
    "wall":  "#2F4F4F",  # Dark Charcoal / Solid Black
}

# Color palette for Physical Boundary Map (Model 2)
PHYSICAL_COLOR_MAP = {
    "inflow":    "#0000FF",  # Electric Blue
    "outflow":   "#FF0000",  # Bright Red
    "no-slip":   "#708090",  # Medium Charcoal / Slate Gray
    "free-slip": "#3CB371",  # Translucent Green
    "pressure":  "#800080",  # Purple / Magenta
}


def render_spatial_location_map(output_path: Path, bounds: Tuple[float, ...]) -> None:
    """Renders Spatial Location Map with color agenda legend (Model 1)."""
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    _draw_domain_geometry(ax, bounds, face_color_dict=SPATIAL_COLOR_MAP, mode="spatial")

    ax.set_title("3D Visual QA - Spatial Location Map", fontsize=12, fontweight="bold")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")

    legend_patches = [
        mpatches.Patch(color=color, label=f"{loc}")
        for loc, color in SPATIAL_COLOR_MAP.items()
    ]
    ax.legend(
        handles=legend_patches,
        title="Spatial Location",
        loc="center left",
        bbox_to_anchor=(1.05, 0.5),
        fontsize=9,
        title_fontsize=10,
        frameon=True
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def render_physical_boundary_map(
    output_path: Path,
    bounds: Tuple[float, ...],
    location_to_type: Dict[str, str],
    location_to_values: Dict[str, Dict[str, float]]
) -> None:
    """Renders Physical Boundary Map with dynamic velocity vectors & color agenda legend (Model 2)."""
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    face_colors = {}
    for loc, btype in location_to_type.items():
        face_colors[loc] = PHYSICAL_COLOR_MAP.get(btype, "#708090")

    if "wall" not in face_colors:
        face_colors["wall"] = PHYSICAL_COLOR_MAP.get("no-slip", "#708090")

    _draw_domain_geometry(ax, bounds, face_color_dict=face_colors, mode="physical")

    # Dynamic 3D velocity vector overlay for any boundary set to 'inflow'
    for loc, btype in location_to_type.items():
        if btype == "inflow" and loc in location_to_values:
            vals = location_to_values[loc]
            u = vals.get("u", 0.0)
            v = vals.get("v", 0.0)
            w = vals.get("w", 0.0)

            cx, cy, cz = _get_face_centroid(loc, bounds)
            vel_mag = np.sqrt(u**2 + v**2 + w**2)
            scale = 400.0 if vel_mag > 0 else 1.0

            ax.quiver(
                cx, cy, cz,
                u * scale, v * scale, w * scale,
                color="#0000FF", linewidth=3.0, arrow_length_ratio=0.35
            )

    ax.set_title("3D Visual QA - Physical Boundary Map", fontsize=12, fontweight="bold")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")

    legend_patches = [
        mpatches.Patch(color=color, label=f"{btype}")
        for btype, color in PHYSICAL_COLOR_MAP.items()
    ]
    ax.legend(
        handles=legend_patches,
        title="Boundary Condition Type",
        loc="center left",
        bbox_to_anchor=(1.05, 0.5),
        fontsize=9,
        title_fontsize=10,
        frameon=True
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _get_face_centroid(loc: str, bounds: Tuple[float, ...]) -> Tuple[float, float, float]:
    """Calculates center coordinate for a given bounding box location."""
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    mid_x, mid_y, mid_z = (xmin + xmax) / 2.0, (ymin + ymax) / 2.0, (zmin + zmax) / 2.0

    centroids = {
        "x_min": (xmin, mid_y, mid_z),
        "x_max": (xmax, mid_y, mid_z),
        "y_min": (mid_x, ymin, mid_z),
        "y_max": (mid_x, ymax, mid_z),
        "z_min": (mid_x, mid_y, zmin),
        "z_max": (mid_x, mid_y, zmax),
        "wall":  (mid_x, mid_y, mid_z),
    }
    return centroids.get(loc, (mid_x, mid_y, mid_z))


def _draw_domain_geometry(
    ax: Any,
    bounds: Tuple[float, ...],
    face_color_dict: Dict[str, str],
    mode: str
) -> None:
    """Renders 3D bounding box faces and internal CAD geometry features using Poly3DCollection patches."""
    xmin, xmax, ymin, ymax, zmin, zmax = bounds

    plane_definitions = {
        "x_min": np.array([[xmin, ymin, zmin], [xmin, ymax, zmin], [xmin, ymax, zmax], [xmin, ymin, zmax]]),
        "x_max": np.array([[xmax, ymin, zmin], [xmax, ymax, zmin], [xmax, ymax, zmax], [xmax, ymin, zmax]]),
        "y_min": np.array([[xmin, ymin, zmin], [xmax, ymin, zmin], [xmax, ymin, zmax], [xmin, ymin, zmax]]),
        "y_max": np.array([[xmin, ymax, zmin], [xmax, ymax, zmin], [xmax, ymax, zmax], [xmin, ymax, zmax]]),
        "z_min": np.array([[xmin, ymin, zmin], [xmax, ymin, zmin], [xmax, ymax, zmin], [xmin, ymax, zmin]]),
        "z_max": np.array([[xmin, ymin, zmax], [xmax, ymin, zmax], [xmax, ymax, zmax], [xmin, ymax, zmax]]),
    }

    for loc, verts in plane_definitions.items():
        color = face_color_dict.get(loc, "#A9A9A9")
        poly = Poly3DCollection([verts], alpha=0.35, facecolor=color, edgecolor="black", linewidths=0.5)
        ax.add_collection3d(poly)

    # Internal cylindrical wall surface
    radius = 1500.0
    cyl_center_x = (xmin + xmax) / 2.0
    cyl_center_z = (zmin + zmax) / 2.0
    
    y_coords = np.linspace(ymin, ymax, 20)
    theta = np.linspace(0, 2 * np.pi, 30)
    theta_grid, y_grid = np.meshgrid(theta, y_coords)
    
    x_grid = cyl_center_x + radius * np.cos(theta_grid)
    z_grid = cyl_center_z + radius * np.sin(theta_grid)

    wall_color = face_color_dict.get("wall", "#2F4F4F")
    ax.plot_surface(
        x_grid, y_grid, z_grid,
        color=wall_color,
        alpha=0.65,
        shade=True,
        edgecolor="none"
    )

    ax.set_xlim([xmin, xmax])
    ax.set_ylim([ymin, ymax])
    ax.set_zlim([zmin, zmax])
