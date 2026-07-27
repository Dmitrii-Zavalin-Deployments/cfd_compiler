"""
Unit tests for src/utils/renderer.py
Provides 100% test coverage and validates all constitution quality gates.
"""

import logging
from pathlib import Path
import matplotlib.pyplot as plt
import pytest

from src.utils.renderer import (
    PHYSICAL_COLOR_MAP,
    _draw_alternating_edge,
    _draw_domain_geometry,
    _get_face_centroid,
    render_physical_boundary_map,
    render_spatial_location_map,
    render_step_snapshot,
)

logger = logging.getLogger(__name__)

TEST_BOUNDS = (0.0, 100.0, 0.0, 50.0, 0.0, 50.0)


@pytest.fixture(autouse=True)
def cleanup_figures():
    """Ensures Matplotlib figures are closed after every test run."""
    yield
    plt.close("all")


def test_render_step_snapshot_success(tmp_path: Path) -> None:
    """Verifies raw STEP geometry preview snapshot generation."""
    output_file = tmp_path / "step_snapshot.png"
    logger.info("Executing render_step_snapshot verification -> %s", output_file)

    render_step_snapshot(output_file, TEST_BOUNDS)

    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_render_spatial_location_map_success(tmp_path: Path) -> None:
    """Verifies Spatial Location Map (Model 1) generation."""
    output_file = tmp_path / "spatial_map.png"
    logger.info("Executing render_spatial_location_map verification -> %s", output_file)

    render_spatial_location_map(output_file, TEST_BOUNDS)

    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_render_physical_boundary_map_full_success(tmp_path: Path) -> None:
    """Verifies Physical Boundary Map (Model 2) with active velocity vectors."""
    output_file = tmp_path / "physical_map.png"
    location_to_type = {
        "x_min": "inflow",
        "x_max": "outflow",
        "y_min": "no-slip",
        "y_max": "free-slip",
        "z_min": "pressure",
        "z_max": "no-slip",
    }
    location_to_values = {
        "x_min": {"u": 5.0, "v": 0.0, "w": 0.0},
    }

    logger.info("Executing render_physical_boundary_map full success verification")
    render_physical_boundary_map(output_file, TEST_BOUNDS, location_to_type, location_to_values)

    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_render_physical_boundary_map_explicit_wall(tmp_path: Path) -> None:
    """Verifies Physical Boundary Map execution when 'wall' is explicitly present in location_to_type."""
    output_file = tmp_path / "physical_map_explicit_wall.png"
    location_to_type = {
        "x_min": "inflow",
        "x_max": "outflow",
        "y_min": "no-slip",
        "y_max": "free-slip",
        "z_min": "pressure",
        "z_max": "no-slip",
        "wall": "no-slip",
    }
    location_to_values = {
        "x_min": {"u": 1.0, "v": 1.0, "w": 0.0},
    }

    logger.info("Executing render_physical_boundary_map with explicit 'wall'")
    render_physical_boundary_map(output_file, TEST_BOUNDS, location_to_type, location_to_values)

    assert output_file.exists()


def test_render_physical_boundary_map_zero_velocity(tmp_path: Path) -> None:
    """Verifies quiver scaling branch when velocity magnitude is zero (scale = 1.0)."""
    output_file = tmp_path / "physical_map_zero_vel.png"
    location_to_type = {"x_min": "inflow"}
    location_to_values = {"x_min": {"u": 0.0, "v": 0.0, "w": 0.0}}

    logger.info("Executing render_physical_boundary_map with zero magnitude inflow")
    render_physical_boundary_map(output_file, TEST_BOUNDS, location_to_type, location_to_values)

    assert output_file.exists()


def test_render_physical_boundary_map_inflow_not_in_values(tmp_path: Path) -> None:
    """Verifies skip condition when 'inflow' location is missing from location_to_values."""
    output_file = tmp_path / "physical_map_no_values.png"
    location_to_type = {"x_min": "inflow"}
    location_to_values = {}

    logger.info("Executing render_physical_boundary_map with unmapped inflow location")
    render_physical_boundary_map(output_file, TEST_BOUNDS, location_to_type, location_to_values)

    assert output_file.exists()


def test_render_physical_boundary_map_unknown_type_raises(tmp_path: Path) -> None:
    """Verifies KeyError raises on unknown boundary type."""
    output_file = tmp_path / "fail.png"
    location_to_type = {"x_min": "invalid_boundary_type"}
    location_to_values = {}

    logger.info("Verifying KeyError on unknown boundary type")
    with pytest.raises(KeyError, match="CONSTITUTION VIOLATION: Unknown boundary type"):
        render_physical_boundary_map(output_file, TEST_BOUNDS, location_to_type, location_to_values)


def test_render_physical_boundary_map_missing_noslip_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifies KeyError raises when 'no-slip' is missing from PHYSICAL_COLOR_MAP."""
    output_file = tmp_path / "fail.png"
    location_to_type = {"x_min": "inflow"}
    location_to_values = {"x_min": {"u": 1.0, "v": 0.0, "w": 0.0}}

    monkeypatch.delitem(PHYSICAL_COLOR_MAP, "no-slip")

    logger.info("Verifying KeyError when 'no-slip' is missing from PHYSICAL_COLOR_MAP")
    with pytest.raises(KeyError, match="CONSTITUTION VIOLATION: 'no-slip' type missing"):
        render_physical_boundary_map(output_file, TEST_BOUNDS, location_to_type, location_to_values)


def test_render_physical_boundary_map_inflow_missing_components_raises(tmp_path: Path) -> None:
    """Verifies KeyError raises when inflow values lack u, v, or w."""
    output_file = tmp_path / "fail.png"
    location_to_type = {"x_min": "inflow"}
    location_to_values = {"x_min": {"u": 1.0}}  # Missing 'v' and 'w'

    logger.info("Verifying KeyError on missing velocity components")
    with pytest.raises(KeyError, match="missing required velocity components"):
        render_physical_boundary_map(output_file, TEST_BOUNDS, location_to_type, location_to_values)


def test_get_face_centroid_all_locations() -> None:
    """Verifies centroid coordinates for all valid domain faces."""
    locations = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "wall"]

    for loc in locations:
        centroid = _get_face_centroid(loc, TEST_BOUNDS)
        logger.info("Location '%s' centroid -> %s", loc, centroid)
        assert len(centroid) == 3


def test_get_face_centroid_invalid_location_raises() -> None:
    """Verifies KeyError raises on invalid location request."""
    logger.info("Verifying KeyError on invalid centroid location")
    with pytest.raises(KeyError, match="CONSTITUTION VIOLATION: Invalid location"):
        _get_face_centroid("invalid_location", TEST_BOUNDS)


def test_draw_domain_geometry_missing_face_color_raises() -> None:
    """Verifies KeyError raises when face_color_dict is missing bounding box face keys."""
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    incomplete_map = {"x_min": "#000000"}

    logger.info("Verifying KeyError on incomplete face_color_dict")
    with pytest.raises(KeyError, match="CONSTITUTION VIOLATION: Missing face color for location"):
        _draw_domain_geometry(ax, TEST_BOUNDS, incomplete_map)


def test_draw_domain_geometry_missing_wall_color_raises() -> None:
    """Verifies KeyError raises when face_color_dict is missing the 'wall' key."""
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    colors_without_wall = {
        "x_min": "#111111",
        "x_max": "#222222",
        "y_min": "#333333",
        "y_max": "#444444",
        "z_min": "#555555",
        "z_max": "#666666",
    }

    logger.info("Verifying KeyError on missing 'wall' face color")
    with pytest.raises(KeyError, match="CONSTITUTION VIOLATION: Missing face color for 'wall'"):
        _draw_domain_geometry(ax, TEST_BOUNDS, colors_without_wall)


def test_draw_alternating_edge_direct() -> None:
    """Verifies segment rendering loop inside _draw_alternating_edge."""
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    logger.info("Verifying direct edge segment plotting")
    _draw_alternating_edge(ax, (0, 0, 0), (10, 0, 0), "#FF0000", "#00FF00", num_segments=4)

    assert len(ax.lines) == 4
