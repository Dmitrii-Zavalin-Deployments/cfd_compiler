"""
Unit tests for src/utils/renderer/maps.py
Achieves 100% branch and line coverage for rendering map functions.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

import src.utils.renderer.maps as maps_module
from src.utils.renderer.maps import (
    render_physical_boundary_map,
    render_spatial_location_map,
    render_step_snapshot,
)


def test_render_step_snapshot(tmp_path: Path) -> None:
    output_path = tmp_path / "step_snapshot.png"
    bounds = (-10.0, 10.0, -20.0, 20.0, -30.0, 30.0)

    # Test normal mode (DEBUG_MODE = False)
    with patch.object(maps_module, "DEBUG_MODE", False):
        render_step_snapshot(output_path, bounds)
    assert output_path.exists()

    # Test debug mode (DEBUG_MODE = True) with step_file_path provided
    with patch.object(maps_module, "DEBUG_MODE", True):
        render_step_snapshot(output_path, bounds, step_file_path="dummy.step")


def test_render_spatial_location_map(tmp_path: Path) -> None:
    output_path = tmp_path / "spatial_location_map.png"
    bounds = (-10.0, 10.0, -20.0, 20.0, -30.0, 30.0)

    # Test normal mode (DEBUG_MODE = False)
    with patch.object(maps_module, "DEBUG_MODE", False):
        render_spatial_location_map(output_path, bounds)
    assert output_path.exists()

    # Test debug mode (DEBUG_MODE = True) with step_file_path provided
    with patch.object(maps_module, "DEBUG_MODE", True):
        render_spatial_location_map(output_path, bounds, step_file_path="dummy.step")


def test_render_physical_boundary_map_success(tmp_path: Path) -> None:
    output_path = tmp_path / "physical_boundary_map.png"
    bounds = (-10.0, 10.0, -20.0, 20.0, -30.0, 30.0)

    required_locations = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "wall"]
    location_to_type = {loc: "wall" for loc in required_locations}
    location_to_type["x_min"] = "inflow"

    # Case 1: Non-zero velocity magnitude (scale = 400.0) under DEBUG_MODE = True
    location_to_values = {
        "x_min": {"u": 1.5, "v": 0.0, "w": 0.0}
    }

    with patch.object(maps_module, "DEBUG_MODE", True):
        render_physical_boundary_map(
            output_path=output_path,
            bounds=bounds,
            location_to_type=location_to_type,
            location_to_values=location_to_values,
            step_file_path="dummy.step",
        )
    assert output_path.exists()

    # Case 2: Zero velocity magnitude (scale = 1.0) under DEBUG_MODE = False
    location_to_values_zero = {
        "x_min": {"u": 0.0, "v": 0.0, "w": 0.0}
    }
    with patch.object(maps_module, "DEBUG_MODE", False):
        render_physical_boundary_map(
            output_path=output_path,
            bounds=bounds,
            location_to_type=location_to_type,
            location_to_values=location_to_values_zero,
        )


def test_render_physical_boundary_map_missing_location(tmp_path: Path) -> None:
    output_path = tmp_path / "physical_map.png"
    bounds = (-10.0, 10.0, -20.0, 20.0, -30.0, 30.0)

    # Omit "wall" from required locations
    location_to_type = {
        "x_min": "wall",
        "x_max": "wall",
        "y_min": "wall",
        "y_max": "wall",
        "z_min": "wall",
        "z_max": "wall",
    }
    location_to_values = {}

    with pytest.raises(KeyError, match="Missing boundary type definition for location 'wall'"):
        render_physical_boundary_map(output_path, bounds, location_to_type, location_to_values)


def test_render_physical_boundary_map_unknown_btype(tmp_path: Path) -> None:
    output_path = tmp_path / "physical_map.png"
    bounds = (-10.0, 10.0, -20.0, 20.0, -30.0, 30.0)

    required_locations = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "wall"]
    location_to_type = {loc: "invalid_boundary_type" for loc in required_locations}
    location_to_values = {}

    with pytest.raises(KeyError, match="Unknown boundary type 'invalid_boundary_type'"):
        render_physical_boundary_map(output_path, bounds, location_to_type, location_to_values)


def test_render_physical_boundary_map_missing_velocity_components(tmp_path: Path) -> None:
    output_path = tmp_path / "physical_map.png"
    bounds = (-10.0, 10.0, -20.0, 20.0, -30.0, 30.0)

    required_locations = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "wall"]
    location_to_type = {loc: "wall" for loc in required_locations}
    location_to_type["x_min"] = "inflow"

    # Missing 'v' and 'w' components in inflow values dictionary
    location_to_values = {
        "x_min": {"u": 10.0}
    }

    with pytest.raises(KeyError, match="missing required velocity components \\(u, v, w\\)"):
        render_physical_boundary_map(output_path, bounds, location_to_type, location_to_values)
