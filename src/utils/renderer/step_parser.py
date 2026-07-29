import re
from pathlib import Path
from typing import Any

import numpy as np

from src.utils.renderer.config import DEBUG_MODE, logger


def parse_step_file(step_file_path: Path | str | None) -> tuple[np.ndarray | None, dict[str, Any]]:
    """
    Parses arbitrary 3D B-Rep geometry and coordinate axis positions directly from a STEP file:
    1. Extracts CARTESIAN_POINT, VERTEX_POINT, DIRECTION, and AXIS2_PLACEMENT_3D entities.
    2. Filters points to VERTEX_POINT topological vertices to exclude CAD construction origins.
    3. Projects cylinder generator lines strictly within true solid bounds.
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
    for match in point_pattern.finditer(text):
        p_id = match.group(1)
        coords = [float(match.group(2)), float(match.group(3)), float(match.group(4))]
        cartesian_points[p_id] = np.array(coords)

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

    # FILTER FIX: Filter out construction points (origins at X = -3000 mm)
    topological_points = list(vertices.values()) if vertices else list(cartesian_points.values())

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

    curves: list[np.ndarray] = []

    # 6. Parse EDGE_CURVE entities
    edge_pattern = re.compile(
        r"#(\d+)\s*=\s*EDGE_CURVE\s*\(\s*'[^']*'\s*,\s*#(\d+)\s*,\s*#(\d+)\s*,\s*#(\d+)\s*,\s*\.(T|F)\.\s*\)",
        re.IGNORECASE
    )
    for match in edge_pattern.finditer(text):
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
        elif v1_pt is not None and v2_pt is not None:
            curves.append(np.array([v1_pt, v2_pt]))

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

    # 8. Parse CYLINDRICAL_SURFACE with projection fix from TOPOLOGICAL VERTICES ONLY
    cyl_pattern = re.compile(
        r"#(\d+)\s*=\s*CYLINDRICAL_SURFACE\s*\(\s*'[^']*'\s*,\s*#(\d+)\s*,\s*([-\d\.E+\-]+)\s*\)",
        re.IGNORECASE
    )
    for match in cyl_pattern.finditer(text):
        placement_id = match.group(2)
        radius = float(match.group(3))
        if placement_id in placements:
            frame = placements[placement_id]
            c_orig = frame["origin"]
            axis_vec = frame["z_axis"]
            u_vec = frame["x_axis"]
            v_vec = frame["y_axis"]

            # FIX: Project ONLY topological points to avoid unattached origin points (e.g., X = -3000 mm)
            if topological_points:
                top_pts_arr = np.array(topological_points)
                projections = np.dot(top_pts_arr - c_orig, axis_vec)
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

    # Return topological points array for accurate bounding box representation
    pts_array = np.array(topological_points) if topological_points else None
    axis_frame["curves"] = curves

    if DEBUG_MODE:
        if pts_array is not None:
            min_pt = np.min(pts_array, axis=0).round(2).tolist()
            max_pt = np.max(pts_array, axis=0).round(2).tolist()
            logger.debug("Extracted %d topological vertices. Extents: min=%s, max=%s", len(pts_array), min_pt, max_pt)
        logger.debug("Total extracted CAD curves for rendering: %d", len(curves))
    else:
        logger.info("Parsed CAD geometry successfully.")

    return pts_array, axis_frame
