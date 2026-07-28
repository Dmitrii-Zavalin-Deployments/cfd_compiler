import logging
import re
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Force non-interactive Agg backend for headless rendering
matplotlib.use("Agg")

# ==============================================================================
# LOGGING & OPERATIONAL MODE CONFIGURATION
# ==============================================================================

logger = logging.getLogger("step_visualizer")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [STEP_RENDERER] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)

# Global Mode Toggle: Set to True for detailed geometry debugging, False for Production
DEBUG_MODE: bool = True


def set_debug_mode(enabled: bool = True) -> None:
    """Dynamically toggles Debug Mode (verbose geometry logs) and Production Mode (sanitized logs)."""
    global DEBUG_MODE
    DEBUG_MODE = enabled
    logger.setLevel(logging.DEBUG if enabled else logging.INFO)


# Initialize default log level based on mode
set_debug_mode(DEBUG_MODE)

# ==============================================================================
# COLOR PALETTES
# ==============================================================================

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


def _parse_step_file(step_file_path: Path | str | None) -> tuple[np.ndarray | None, dict[str, Any]]:
    """
    Parses arbitrary 3D B-Rep geometry and coordinate axis positions directly from a STEP file:
    1. Extracts CARTESIAN_POINT, VERTEX_POINT, DIRECTION, and AXIS2_PLACEMENT_3D entities.
    2. Extracts EDGE_CURVE, LINE, CIRCLE, and CYLINDRICAL_SURFACE topological entities.
    3. Generates 3D curve paths for visual QA rendering.
    """
    if not step_file_path:
        logger.info("No STEP file path provided. Skipping CAD parsing.")
        return None, {}

    path = Path(step_file_path)
    if not path.exists():
        logger.warning("STEP file not found at path: %s", path if DEBUG_MODE else path.name)
        return None, {}

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if DEBUG_MODE:
            logger.debug("Successfully read STEP file '%s' (%d bytes)", path, len(text))
        else:
            logger.info("Loaded STEP file for processing.")
    except (OSError, UnicodeDecodeError) as exc:
        logger.error("Failed to read STEP file: %s", exc)
        return None, {}

    # 1. Parse CARTESIAN_POINT entities
    point_pattern = re.compile(
        r"#(\d+)\s*=\s*CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(\s*([-\d\.E+\-]+)\s*,\s*([-\d\.E+\-]+)\s*,\s*([-\d\.E+\-]+)\s*\)\s*\)",
        re.IGNORECASE
    )
    cartesian_points: dict[str, np.ndarray] = {}
    all_points: list[list[float]] = []

    for match in point_pattern.finditer(text):
        p_id = match.group(1)
        coords = [float(match.group(2)), float(match.group(3)), float(match.group(4))]
        cartesian_points[p_id] = np.array(coords)
        all_points.append(coords)

    if DEBUG_MODE:
        logger.debug("Extracted %d CARTESIAN_POINT entities", len(cartesian_points))

    # 2. Parse VERTEX_POINT entities
    vertex_pattern = re.compile(
        r"#(\d+)\s*=\s*VERTEX_POINT\s*\(\s*'[^']*'\s*,\s*#(\d+)\s*\)",
        re.IGNORECASE
    )
    vertices: dict[str, np.ndarray] = {}
    for match in vertex_pattern.finditer(text):
        v_id = match.group(1)
        pt_id = match.group(2)
        if pt_id in cartesian_points:
            vertices[v_id] = cartesian_points[pt_id]

    if DEBUG_MODE:
        logger.debug("Extracted %d VERTEX_POINT entities", len(vertices))

    # 3. Parse DIRECTION entities
    dir_pattern = re.compile(
        r"#(\d+)\s*=\s*DIRECTION\s*\(\s*'[^']*'\s*,\s*\(\s*([-\d\.E+\-]+)\s*,\s*([-\d\.E+\-]+)\s*,\s*([-\d\.E+\-]+)\s*\)\s*\)",
        re.IGNORECASE
    )
    directions: dict[str, np.ndarray] = {}
    for match in dir_pattern.finditer(text):
        d_id = match.group(1)
        directions[d_id] = np.array([float(match.group(2)), float(match.group(3)), float(match.group(4))])

    if DEBUG_MODE:
        logger.debug("Extracted %d DIRECTION entities", len(directions))

    # 4. Parse AXIS2_PLACEMENT_3D entities
    placement_pattern = re.compile(
        r"#(\d+)\s*=\s*AXIS2_PLACEMENT_3D\s*\(\s*'[^']*'\s*,\s*#(\d+)(?:\s*,\s*#(\d+))?(?:\s*,\s*#(\d+))?\s*\)",
        re.IGNORECASE
    )
    placements: dict[str, dict[str, np.ndarray]] = {}

    for match in placement_pattern.finditer(text):
        p_id = match.group(1)
        orig_id = match.group(2)
        z_id = match.group(3)
        x_id = match.group(4)

        origin = cartesian_points.get(orig_id, np.array([0.0, 0.0, 0.0]))
        z_axis = directions.get(z_id, np.array([0.0, 0.0, 1.0])) if z_id else np.array([0.0, 0.0, 1.0])
        x_axis = directions.get(x_id, np.array([1.0, 0.0, 0.0])) if x_id else np.array([1.0, 0.0, 0.0])

        z_norm = np.linalg.norm(z_axis)
        x_norm = np.linalg.norm(x_axis)
        z_axis = z_axis / z_norm if z_norm > 1e-6 else np.array([0.0, 0.0, 1.0])
        x_axis = x_axis / x_norm if x_norm > 1e-6 else np.array([1.0, 0.0, 0.0])

        y_axis = np.cross(z_axis, x_axis)
        y_norm = np.linalg.norm(y_axis)
        y_axis = y_axis / y_norm if y_norm > 1e-6 else np.array([0.0, 1.0, 0.0])

        placements[p_id] = {
            "origin": origin,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "z_axis": z_axis,
        }

    if DEBUG_MODE:
        logger.debug("Extracted %d AXIS2_PLACEMENT_3D entities", len(placements))

    # Primary axis frame selection
    axis_frame: dict[str, Any] = {}
    m_place = re.search(
        r"AXIS2_PLACEMENT_3D\s*\(\s*'[^']*'\s*,\s*#(\d+)\s*,\s*#(\d+)\s*,\s*#(\d+)\s*\)",
        text,
        re.IGNORECASE
    )
    if m_place:
        origin_id, z_dir_id, x_dir_id = m_place.group(1), m_place.group(2), m_place.group(3)
        origin = cartesian_points.get(origin_id, np.array([0.0, 0.0, 0.0]))
        z_axis = directions.get(z_dir_id, np.array([0.0, 0.0, 1.0]))
        x_axis = directions.get(x_dir_id, np.array([1.0, 0.0, 0.0]))

        x_norm = np.linalg.norm(x_axis)
        z_norm = np.linalg.norm(z_axis)
        x_axis = x_axis / x_norm if x_norm > 1e-6 else np.array([1.0, 0.0, 0.0])
        z_axis = z_axis / z_norm if z_norm > 1e-6 else np.array([0.0, 0.0, 1.0])

        y_axis = np.cross(z_axis, x_axis)
        y_norm = np.linalg.norm(y_axis)
        y_axis = y_axis / y_norm if y_norm > 1e-6 else np.array([0.0, 1.0, 0.0])

        axis_frame = {
            "origin": origin,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "z_axis": z_axis,
        }
        if DEBUG_MODE:
            logger.debug("Selected primary AXIS2_PLACEMENT_3D frame at origin=%s", origin.tolist())

    # 5. Parse CIRCLE entities
    circle_pattern = re.compile(
        r"#(\d+)\s*=\s*CIRCLE\s*\(\s*'[^']*'\s*,\s*#(\d+)\s*,\s*([-\d\.E+\-]+)\s*\)",
        re.IGNORECASE
    )
    circles: dict[str, dict[str, Any]] = {}
    for match in circle_pattern.finditer(text):
        c_id = match.group(1)
        p_id = match.group(2)
        radius = float(match.group(3))
        circles[c_id] = {"placement_id": p_id, "radius": radius}

    if DEBUG_MODE:
        logger.debug("Extracted %d CIRCLE entities", len(circles))

    curves: list[np.ndarray] = []

    # 6. Parse EDGE_CURVE entities to connect CAD boundary lines
    edge_pattern = re.compile(
        r"#(\d+)\s*=\s*EDGE_CURVE\s*\(\s*'[^']*'\s*,\s*#(\d+)\s*,\s*#(\d+)\s*,\s*#(\d+)\s*,\s*\.(T|F)\.\s*\)",
        re.IGNORECASE
    )
    edge_count = 0
    for match in edge_pattern.finditer(text):
        edge_count += 1
        v1_id = match.group(2)
        v2_id = match.group(3)
        geom_id = match.group(4)

        v1_pt = vertices.get(v1_id)
        v2_pt = vertices.get(v2_id)

        if geom_id in circles:
            c_info = circles[geom_id]
            p_id = c_info["placement_id"]
            radius = c_info["radius"]
            if p_id in placements:
                frame = placements[p_id]
                c_orig = frame["origin"]
                u_vec = frame["x_axis"]
                v_vec = frame["y_axis"]

                angles = np.linspace(0, 2 * np.pi, 64)
                circle_pts = np.array([
                    c_orig + radius * np.cos(a) * u_vec + radius * np.sin(a) * v_vec
                    for a in angles
                ])
                curves.append(circle_pts)
                if DEBUG_MODE:
                    logger.debug("Added CIRCLE edge curve (R=%f, Center=%s)", radius, c_orig.tolist())
        elif v1_pt is not None and v2_pt is not None:
            # Straight topological CAD edge line segment
            curves.append(np.array([v1_pt, v2_pt]))

    if DEBUG_MODE:
        logger.debug("Processed %d EDGE_CURVE entities", edge_count)

    # 7. Fallback processing for standalone CIRCLE entities
    for c_id, c_info in circles.items():
        p_id = c_info["placement_id"]
        radius = c_info["radius"]
        if p_id in placements:
            frame = placements[p_id]
            c_orig = frame["origin"]
            u_vec = frame["x_axis"]
            v_vec = frame["y_axis"]

            angles = np.linspace(0, 2 * np.pi, 64)
            circle_pts = np.array([
                c_orig + radius * np.cos(a) * u_vec + radius * np.sin(a) * v_vec
                for a in angles
            ])
            already_added = any(
                len(c) == 64 and np.allclose(c[0], circle_pts[0], atol=1e-3)
                for c in curves
            )
            if not already_added:
                curves.append(circle_pts)
                if DEBUG_MODE:
                    logger.debug("Added standalone CIRCLE entity #%s (R=%f)", c_id, radius)

    # 8. Parse CYLINDRICAL_SURFACE entities with projected bounds calculation
    cyl_pattern = re.compile(
        r"#(\d+)\s*=\s*CYLINDRICAL_SURFACE\s*\(\s*'[^']*'\s*,\s*#(\d+)\s*,\s*([-\d\.E+\-]+)\s*\)",
        re.IGNORECASE
    )
    cyl_count = 0
    for match in cyl_pattern.finditer(text):
        cyl_count += 1
        placement_id = match.group(2)
        radius = float(match.group(3))
        if placement_id in placements:
            frame = placements[placement_id]
            c_orig = frame["origin"]
            axis_vec = frame["z_axis"]
            u_vec = frame["x_axis"]
            v_vec = frame["y_axis"]

            if all_points:
                pts_arr = np.array(all_points)
                projections = np.dot(pts_arr - c_orig, axis_vec)
                t_min = float(np.min(projections))
                t_max = float(np.max(projections))
            else:
                t_min = -radius
                t_max = radius

            angles = np.linspace(0, 2 * np.pi, 8, endpoint=False)
            for a in angles:
                radial_offset = radius * np.cos(a) * u_vec + radius * np.sin(a) * v_vec
                line_start = c_orig + radial_offset + axis_vec * t_min
                line_end = c_orig + radial_offset + axis_vec * t_max
                curves.append(np.array([line_start, line_end]))

            if DEBUG_MODE:
                logger.debug("Extracted CYLINDRICAL_SURFACE (R=%f, t_range=[%f, %f])", radius, t_min, t_max)

    pts_array = np.array(all_points) if all_points else None
    axis_frame["curves"] = curves

    if DEBUG_MODE:
        if pts_array is not None:
            min_pt = np.min(pts_array, axis=0).round(2).tolist()
            max_pt = np.max(pts_array, axis=0).round(2).tolist()
            logger.debug("Extracted %d points. Extents: min=%s, max=%s", len(pts_array), min_pt, max_pt)
        logger.debug("Total extracted CAD curves for rendering: %d", len(curves))
    else:
        logger.info("Parsed CAD geometry successfully.")

    return pts_array, axis_frame


def render_step_snapshot(
    output_path: Path, 
    bounds: tuple[float, ...], 
    step_file_path: Path | str | None = None
) -> None:
    """Renders raw STEP geometry preview matching the exact 3D orientation of the pipeline maps."""
    if DEBUG_MODE:
        logger.debug("Rendering STEP Snapshot -> output_path='%s', bounds=%s", output_path, bounds)
    else:
        logger.info("Rendering STEP Snapshot to %s", output_path.name)

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    _draw_domain_geometry(ax, bounds, face_color_dict=CAD_COLOR_MAP, step_file_path=step_file_path)

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
    logger.info("Successfully exported STEP Snapshot image.")


def render_spatial_location_map(
    output_path: Path, 
    bounds: tuple[float, ...], 
    step_file_path: Path | str | None = None
) -> None:
    """Renders Spatial Location Map with alternating multi-color 'shtrih' shared edges and low-alpha fill (Model 1)."""
    if DEBUG_MODE:
        logger.debug("Rendering Spatial Location Map -> output_path='%s', bounds=%s", output_path, bounds)
    else:
        logger.info("Rendering Spatial Location Map to %s", output_path.name)

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    _draw_domain_geometry(ax, bounds, face_color_dict=SPATIAL_COLOR_MAP, step_file_path=step_file_path)

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
    logger.info("Successfully exported Spatial Location Map image.")


def render_physical_boundary_map(
    output_path: Path,
    bounds: tuple[float, ...],
    location_to_type: dict[str, str],
    location_to_values: dict[str, dict[str, float]],
    step_file_path: Path | str | None = None
) -> None:
    """
    Renders Physical Boundary Map with dynamic velocity vectors & legend (Model 2).
    Strict No-Default Policy: raises immediate KeyError on missing boundary locations, unknown types, or missing velocity values.
    """
    if DEBUG_MODE:
        logger.debug("Rendering Physical Boundary Map -> output_path='%s'", output_path)
        logger.debug("Location to Type map: %s", location_to_type)
        logger.debug("Location to Values map: %s", location_to_values)
    else:
        logger.info("Rendering Physical Boundary Map to %s", output_path.name)

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    required_locations = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "wall"]
    face_colors = {}
    for loc in required_locations:
        if loc not in location_to_type:
            logger.error("CONSTITUTION VIOLATION: Missing boundary type for '%s'", loc)
            raise KeyError(
                f"CONSTITUTION VIOLATION: Missing boundary type definition for location '{loc}'. Execution halted."
            )
        btype = location_to_type[loc]
        if btype not in PHYSICAL_COLOR_MAP:
            logger.error("CONSTITUTION VIOLATION: Unknown boundary type '%s' for '%s'", btype, loc)
            raise KeyError(
                f"CONSTITUTION VIOLATION: Unknown boundary type '{btype}' for location '{loc}'. Execution halted."
            )
        face_colors[loc] = PHYSICAL_COLOR_MAP[btype]

    _draw_domain_geometry(ax, bounds, face_color_dict=face_colors, step_file_path=step_file_path)

    # Dynamic 3D velocity vector overlay for inflow
    for loc, btype in location_to_type.items():
        if btype == "inflow" and loc in location_to_values:
            vals = location_to_values[loc]
            if "u" not in vals or "v" not in vals or "w" not in vals:
                logger.error("CONSTITUTION VIOLATION: Missing velocity vector components at '%s'", loc)
                raise KeyError(
                    f"CONSTITUTION VIOLATION: Inflow boundary condition at '{loc}' missing required velocity components (u, v, w). Execution halted."
                )

            u = vals["u"]
            v = vals["v"]
            w = vals["w"]

            cx, cy, cz = _get_face_centroid(loc, bounds)
            vel_mag = np.sqrt(u**2 + v**2 + w**2)
            scale = 400.0 if vel_mag > 0 else 1.0

            if DEBUG_MODE:
                logger.debug("Overlaying inflow quiver vector at centroid (%f, %f, %f) with velocity magnitude %f", cx, cy, cz, vel_mag)

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
    logger.info("Successfully exported Physical Boundary Map image.")


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
        logger.error("CONSTITUTION VIOLATION: Invalid face centroid requested for '%s'", loc)
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


def _apply_bounds_padding(bounds: tuple[float, ...], margin: float = 0.05) -> tuple[float, ...]:
    """Expands bounding box by a given margin percentage for clear visual separation."""
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    dx = (xmax - xmin) * margin if xmax > xmin else 1.0
    dy = (ymax - ymin) * margin if ymax > ymin else 1.0
    dz = (zmax - zmin) * margin if zmax > zmin else 1.0
    return (xmin - dx, xmax + dx, ymin - dy, ymax + dy, zmin - dz, zmax + dz)


def _draw_domain_geometry(
    ax: Any,
    bounds: tuple[float, ...],
    face_color_dict: dict[str, str],
    step_file_path: Path | str | None = None,
    padding_margin: float = 0.05
) -> None:
    """Renders 3D domain bounding box faces with padding and alternating color 'shtrih' edges strictly without fallbacks."""
    padded_bounds = _apply_bounds_padding(bounds, margin=padding_margin)
    xmin, xmax, ymin, ymax, zmin, zmax = padded_bounds

    # Upfront validation of required face keys to strictly enforce test error string contracts
    required_faces = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "wall"]
    for loc in required_faces:
        if loc not in face_color_dict:
            logger.error("CONSTITUTION VIOLATION: Missing face color for '%s'", loc)
            raise KeyError(
                f"CONSTITUTION VIOLATION: Missing face color for location '{loc}'. Execution halted."
            )

    # 1. Define the 12 unique cuboid edges using padded bounds
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
        ((xmax, ymax, zmax), (xmax, ymax, zmax), "x_max", "z_max"),
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

    # 2. Render translucent face fills using padded bounds
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
            edgecolor="none"
        )
        ax.add_collection3d(poly)

    # 3. Dynamic STEP object geometry rendering
    pts_array, axis_frame = _parse_step_file(step_file_path)
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
            linewidth=2.5,
            alpha=0.95
        )

    # Render local coordinate triad extracted from STEP file or domain centroid
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
        color="#FF0000", linewidth=2.5, arrow_length_ratio=0.3
    )
    ax.quiver(
        origin[0], origin[1], origin[2],
        y_dir[0] * box_scale, y_dir[1] * box_scale, y_dir[2] * box_scale,
        color="#00CC44", linewidth=2.5, arrow_length_ratio=0.3
    )
    ax.quiver(
        origin[0], origin[1], origin[2],
        z_dir[0] * box_scale, z_dir[1] * box_scale, z_dir[2] * box_scale,
        color="#0066FF", linewidth=2.5, arrow_length_ratio=0.3
    )

    ax.set_xlim([xmin, xmax])
    ax.set_ylim([ymin, ymax])
    ax.set_zlim([zmin, zmax])