from pathlib import Path
from typing import Any

import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from src.utils.renderer.config import DEBUG_MODE, logger
from src.utils.renderer.step_parser import parse_step_file


def get_face_centroid(loc: str, bounds: tuple[float, ...]) -> tuple[float, float, float]:
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
        logger.error("CONSTITUTION VIOLATION: Invalid face centroid requested for '%s'", loc)
        raise KeyError(
            f"CONSTITUTION VIOLATION: Invalid location '{loc}' requested for face centroid. Execution halted."
        )

    return centroids[loc]


def draw_alternating_edge(
    ax: Any,
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    color1: str,
    color2: str,
    num_segments: int = 12,
    linewidth: float = 3.0,
    zorder: int = 5
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
            linewidth=linewidth,
            alpha=1.0,
            zorder=zorder
        )


def apply_bounds_padding(bounds: tuple[float, ...], margin: float = 0.0) -> tuple[float, ...]:
    """Expands bounding box by a given margin percentage for visual separation."""
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    dx = (xmax - xmin) * margin if xmax > xmin else 1.0
    dy = (ymax - ymin) * margin if ymax > ymin else 1.0
    dz = (zmax - zmin) * margin if zmax > zmin else 1.0
    return (xmin - dx, xmax + dx, ymin - dy, ymax + dy, zmin - dz, zmax + dz)


def draw_domain_geometry(
    ax: Any,
    bounds: tuple[float, ...],
    face_color_dict: dict[str, str],
    step_file_path: Path | str | None = None,
    padding_margin: float = 0.0
) -> None:
    """Renders 3D domain bounding box faces and alternating color 'shtrih' edges with priority layering."""
    padded_bounds = apply_bounds_padding(bounds, margin=padding_margin)
    xmin, xmax, ymin, ymax, zmin, zmax = padded_bounds

    # Upfront validation of required face keys to strictly enforce test contracts
    required_faces = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "wall"]
    for loc in required_faces:
        if loc not in face_color_dict:
            logger.error("CONSTITUTION VIOLATION: Missing face color for '%s'", loc)
            raise KeyError(
                f"CONSTITUTION VIOLATION: Missing face color for location '{loc}'. Execution halted."
            )

    # 1. Dynamic STEP object geometry rendering
    pts_array, axis_frame = parse_step_file(step_file_path)
    wall_color = face_color_dict["wall"]

    curves = axis_frame.get("curves", [])
    if DEBUG_MODE:
        logger.debug("Plotting %d CAD geometry curves on 3D canvas", len(curves))

    for curve_pts in curves:
        ax.plot3D(
            curve_pts[:, 0],
            curve_pts[:, 1],
            curve_pts[:, 2],
            color=wall_color,
            linewidth=2.0,
            alpha=0.85,
            zorder=2
        )

    # 2. Render translucent face fills
    plane_definitions = {
        "x_min": np.array([[xmin, ymin, zmin], [xmin, ymax, zmin], [xmin, ymax, zmax], [xmin, ymin, zmax]]),
        "x_max": np.array([[xmax, ymin, zmin], [xmax, ymax, zmin], [xmax, ymax, zmax], [xmax, ymin, zmax]]),
        "y_min": np.array([[xmin, ymin, zmin], [xmax, ymin, zmin], [xmax, ymin, zmax], [xmin, ymin, zmax]]),
        "y_max": np.array([[xmin, ymax, zmin], [xmax, ymax, zmin], [xmax, ymax, zmax], [xmin, ymax, zmin]]),
        "z_min": np.array([[xmin, ymin, zmin], [xmax, ymin, zmin], [xmax, ymin, zmax], [xmin, ymin, zmin]]),
        "z_max": np.array([[xmin, ymin, zmax], [xmax, ymin, zmax], [xmax, ymax, zmax], [xmin, ymin, zmax]]),
    }

    for loc, verts in plane_definitions.items():
        color = face_color_dict[loc]
        poly = Poly3DCollection(
            [verts],
            alpha=0.10,
            facecolor=color,
            edgecolor="none",
            zorder=1
        )
        ax.add_collection3d(poly)

    # 3. Define and draw the 12 unique cuboid edges
    edges = [
        ((xmin, ymin, zmin), (xmax, ymin, zmin), "y_min", "z_min"),
        ((xmin, ymax, zmin), (xmax, ymax, zmin), "y_max", "z_min"),
        ((xmin, ymin, zmax), (xmax, ymin, zmax), "y_min", "z_max"),
        ((xmin, ymax, zmax), (xmax, ymax, zmax), "y_max", "z_max"),
        ((xmin, ymin, zmin), (xmin, ymax, zmin), "x_min", "z_min"),
        ((xmax, ymin, zmin), (xmax, ymax, zmin), "x_max", "z_min"),
        ((xmin, ymin, zmax), (xmin, ymax, zmax), "x_min", "z_max"),
        ((xmax, ymax, zmax), (xmax, ymax, zmax), "x_max", "z_max"),
        ((xmin, ymin, zmin), (xmin, ymin, zmax), "x_min", "y_min"),
        ((xmax, ymin, zmin), (xmax, ymin, zmax), "x_max", "y_min"),
        ((xmin, ymax, zmin), (xmin, ymax, zmax), "x_min", "y_max"),
        ((xmax, ymax, zmin), (xmax, ymax, zmax), "x_max", "y_max"),
    ]

    for p1, p2, face1, face2 in edges:
        c1 = face_color_dict[face1]
        c2 = face_color_dict[face2]
        draw_alternating_edge(ax, p1, p2, c1, c2, num_segments=12, linewidth=3.0, zorder=5)

    # Local coordinate triad overlay
    origin = axis_frame.get("origin")
    if origin is None:
        origin = np.array([
            (bounds[0] + bounds[1]) / 2.0,
            (bounds[2] + bounds[3]) / 2.0,
            (bounds[4] + bounds[5]) / 2.0
        ])

    x_dir = axis_frame.get("x_axis", np.array([1.0, 0.0, 0.0]))
    y_dir = axis_frame.get("y_axis", np.array([0.0, 1.0, 0.0]))
    z_dir = axis_frame.get("z_axis", np.array([0.0, 0.0, 1.0]))

    box_scale = min(xmax - xmin, ymax - ymin, zmax - zmin) * 0.20
    if box_scale <= 0:
        box_scale = 1.0

    ax.quiver(
        origin[0], origin[1], origin[2],
        x_dir[0] * box_scale, x_dir[1] * box_scale, x_dir[2] * box_scale,
        color="#FF0000", linewidth=2.5, arrow_length_ratio=0.3, zorder=6
    )
    ax.quiver(
        origin[0], origin[1], origin[2],
        y_dir[0] * box_scale, y_dir[1] * box_scale, y_dir[2] * box_scale,
        color="#00CC44", linewidth=2.5, arrow_length_ratio=0.3, zorder=6
    )
    ax.quiver(
        origin[0], origin[1], origin[2],
        z_dir[0] * box_scale, z_dir[1] * box_scale, z_dir[2] * box_scale,
        color="#0066FF", linewidth=2.5, arrow_length_ratio=0.3, zorder=6
    )

    ax.set_xlim([xmin, xmax])
    ax.set_ylim([ymin, ymax])
    ax.set_zlim([zmin, zmax])
