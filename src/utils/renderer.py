from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Force non-interactive Agg backend for headless rendering
matplotlib.use("Agg")

# Color palette for Raw STEP Geometry Preview
CAD_COLOR_MAP = {
    "x_min": "#4A6572",  # Steel Slate Blue
    "x_max": "#4A6572",  # Steel Slate Blue
    "y_min": "#4A6572",  # Steel Slate Blue
    "y_max": "#4A6572",  # Steel Slate Blue
    "z_min": "#4A6572",  # Steel Slate Blue
    "z_max": "#4A6572",  # Steel Slate Blue
    "wall":  "#2C3E50",  # Dark Slate Charcoal
}

# Color palette for Spatial Location Map (Model 1)
SPATIAL_COLOR_MAP = {
    "x_min": "#FF0000",  # Bright Red
    "x_max": "#0066FF",  # Royal Blue
    "y_min": "#00CC44",  # Emerald Green
    "y_max": "#800080",  # Solid Purple
    "z_min": "#FF9900",  # Deep Amber / Orange
    "z_max": "#FF00AA",  # Bright Magenta
    "wall":  "#2C3E50",  # Dark Slate Charcoal
}

# Color palette for Physical Boundary Map (Model 2)
PHYSICAL_COLOR_MAP = {
    "inflow":    "#0000FF",  # Electric Blue
    "outflow":   "#FF0000",  # Bright Red
    "no-slip":   "#708090",  # Slate Gray
    "free-slip": "#3CB371",  # Medium Sea Green
    "pressure":  "#800080",  # Purple
}


def render_step_snapshot(output_path: Path, bounds: tuple[float, ...]) -> None:
    """Renders raw STEP geometry preview matching the exact 3D orientation of the pipeline maps."""
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    _draw_domain_geometry(ax, bounds, face_color_dict=CAD_COLOR_MAP)

    ax.set_title("3D Visual QA - Raw STEP Geometry", fontsize=12, fontweight="bold")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")

    legend_patches = [
        mpatches.Patch(color="#4A6572", label="Raw CAD Geometry")
    ]
    ax.legend(
        handles=legend_patches,
        title="Input Model",
        loc="center left",
        bbox_to_anchor=(1.05, 0.5),
        fontsize=9,
        title_fontsize=10,
        frameon=True
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def render_spatial_location_map(output_path: Path, bounds: tuple[float, ...]) -> None:
    """Renders Spatial Location Map with alternating multi-color 'shtrih' shared edges and low-alpha fill (Model 1)."""
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    _draw_domain_geometry(ax, bounds, face_color_dict=SPATIAL_COLOR_MAP)

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
    bounds: tuple[float, ...],
    location_to_type: dict[str, str],
    location_to_values: dict[str, dict[str, float]]
) -> None:
    """
    Renders Physical Boundary Map with dynamic velocity vectors & legend (Model 2).
    Strict No-Default Policy: raises immediate KeyError on missing boundary locations, unknown types, or missing velocity values.
    """
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    required_locations = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "wall"]
    face_colors = {}
    for loc in required_locations:
        if loc not in location_to_type:
            raise KeyError(
                f"CONSTITUTION VIOLATION: Missing boundary type definition for location '{loc}'. Execution halted."
            )
        btype = location_to_type[loc]
        if btype not in PHYSICAL_COLOR_MAP:
            raise KeyError(
                f"CONSTITUTION VIOLATION: Unknown boundary type '{btype}' for location '{loc}'. Execution halted."
            )
        face_colors[loc] = PHYSICAL_COLOR_MAP[btype]

    _draw_domain_geometry(ax, bounds, face_color_dict=face_colors)

    # Dynamic 3D velocity vector overlay for inflow
    for loc, btype in location_to_type.items():
        if btype == "inflow" and loc in location_to_values:
            vals = location_to_values[loc]
            if "u" not in vals or "v" not in vals or "w" not in vals:
                raise KeyError(
                    f"CONSTITUTION VIOLATION: Inflow boundary condition at '{loc}' missing required velocity components (u, v, w). Execution halted."
                )

            u = vals["u"]
            v = vals["v"]
            w = vals["w"]

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


def _get_face_centroid(loc: str, bounds: tuple[float, ...]) -> tuple[float, float, float]:
    """Calculates center coordinate for a given bounding box location strictly without silent fallback."""
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

    if loc not in centroids:
        raise KeyError(
            f"CONSTITUTION VIOLATION: Invalid location '{loc}' requested for face centroid. Execution halted."
        )

    return centroids[loc]


def _draw_alternating_edge(
    ax: Any,
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    color1: str,
    color2: str,
    num_segments: int = 12
) -> None:
    """Renders a shared edge as an alternating multi-color dashed segment ('shtrih')."""
    p1_arr = np.array(p1)
    p2_arr = np.array(p2)
    t = np.linspace(0, 1, num_segments + 1)

    for i in range(num_segments):
        seg_start = p1_arr + t[i] * (p2_arr - p1_arr)
        seg_end = p1_arr + t[i + 1] * (p2_arr - p1_arr)
        color = color1 if i % 2 == 0 else color2

        ax.plot3D(
            [seg_start[0], seg_end[0]],
            [seg_start[1], seg_end[1]],
            [seg_start[2], seg_end[2]],
            color=color,
            linewidth=3.0,
            alpha=1.0
        )


def _draw_domain_geometry(
    ax: Any,
    bounds: tuple[float, ...],
    face_color_dict: dict[str, str],
) -> None:
    """Renders 3D bounding box faces with faint fills and alternating color 'shtrih' edges strictly without fallbacks."""
    xmin, xmax, ymin, ymax, zmin, zmax = bounds

    # Upfront validation of required face keys to strictly enforce test error string contracts
    required_faces = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "wall"]
    for loc in required_faces:
        if loc not in face_color_dict:
            raise KeyError(
                f"CONSTITUTION VIOLATION: Missing face color for location '{loc}'. Execution halted."
            )

    # 1. Define the 12 unique cuboid edges
    edges = [
        # Parallel to X-axis (4 edges)
        ((xmin, ymin, zmin), (xmax, ymin, zmin), "y_min", "z_min"),
        ((xmin, ymax, zmin), (xmax, ymax, zmin), "y_max", "z_min"),
        ((xmin, ymin, zmax), (xmax, ymin, zmax), "y_min", "z_max"),
        ((xmin, ymax, zmax), (xmax, ymax, zmax), "y_max", "z_max"),
        # Parallel to Y-axis (4 edges)
        ((xmin, ymin, zmin), (xmin, ymax, zmin), "x_min", "z_min"),
        ((xmax, ymin, zmin), (xmax, ymax, zmin), "x_max", "z_min"),
        ((xmin, ymin, zmax), (xmin, ymax, zmax), "x_min", "z_max"),
        ((xmax, ymin, zmax), (xmax, ymax, zmax), "x_max", "z_max"),
        # Parallel to Z-axis (4 edges)
        ((xmin, ymin, zmin), (xmin, ymin, zmax), "x_min", "y_min"),
        ((xmax, ymin, zmin), (xmax, ymin, zmax), "x_max", "y_min"),
        ((xmin, ymax, zmin), (xmin, ymax, zmax), "x_min", "y_max"),
        ((xmax, ymax, zmin), (xmax, ymax, zmax), "x_max", "y_max"),
    ]

    for p1, p2, face1, face2 in edges:
        c1 = face_color_dict[face1]
        c2 = face_color_dict[face2]
        _draw_alternating_edge(ax, p1, p2, c1, c2, num_segments=12)

    # 2. Render translucent face fills
    plane_definitions = {
        "x_min": np.array([[xmin, ymin, zmin], [xmin, ymax, zmin], [xmin, ymax, zmax], [xmin, ymin, zmax]]),
        "x_max": np.array([[xmax, ymin, zmin], [xmax, ymax, zmin], [xmax, ymax, zmax], [xmax, ymin, zmax]]),
        "y_min": np.array([[xmin, ymin, zmin], [xmax, ymin, zmin], [xmax, ymin, zmax], [xmin, ymin, zmax]]),
        "y_max": np.array([[xmin, ymax, zmin], [xmax, ymax, zmin], [xmax, ymax, zmax], [xmin, ymax, zmax]]),
        "z_min": np.array([[xmin, ymin, zmin], [xmax, ymin, zmin], [xmax, ymax, zmin], [xmin, ymin, zmin]]),
        "z_max": np.array([[xmin, ymin, zmax], [xmax, ymin, zmax], [xmax, ymax, zmax], [xmin, ymin, zmax]]),
    }

    for loc, verts in plane_definitions.items():
        color = face_color_dict[loc]
        poly = Poly3DCollection(
            [verts],
            alpha=0.10,
            facecolor=color,
            edgecolor="none"
        )
        ax.add_collection3d(poly)

    # 3. Dynamic derivation of internal cylinder geometry from domain bounds
    span_x = xmax - xmin
    span_z = zmax - zmin
    radius = min(span_x, span_z) * 0.375

    cyl_center_x = (xmin + xmax) / 2.0
    cyl_center_z = (zmin + zmax) / 2.0

    y_coords = np.linspace(ymin, ymax, 25)
    theta = np.linspace(0, 2 * np.pi, 40)
    theta_grid, y_grid = np.meshgrid(theta, y_coords)

    x_grid = cyl_center_x + radius * np.cos(theta_grid)
    z_grid = cyl_center_z + radius * np.sin(theta_grid)

    wall_color = face_color_dict["wall"]

    ax.plot_surface(
        x_grid, y_grid, z_grid,
        color=wall_color,
        alpha=0.75,
        shade=True,
        edgecolor="none"
    )

    ax.set_xlim([xmin, xmax])
    ax.set_ylim([ymin, ymax])
    ax.set_zlim([zmin, zmax])