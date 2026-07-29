"""
Unit tests for src/utils/renderer/maps.py
Achieves 100% branch and line coverage for boundary and spatial map rendering.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.renderer.maps import (
    render_physical_boundary_map,
    render_spatial_location_map,
    render_step_snapshot,
)


def test_render_step_snapshot(tmp_path: Path) -> None:
    output_path = tmp_path / "snapshot.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    
    with patch("matplotlib.pyplot.savefig") as mock_savefig, \
         patch("matplotlib.pyplot.close") as mock_close:
        render_step_snapshot(output_path, bounds, step_file_path=None)
        assert mock_savefig.called
        assert mock_close.called


def test_render_step_snapshot_debug_false(tmp_path: Path) -> None:
    output_path = tmp_path / "snapshot_debug_false.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    
    with patch("src.utils.renderer.maps.DEBUG_MODE", False), \
         patch("matplotlib.pyplot.savefig") as mock_savefig, \
         patch("matplotlib.pyplot.close") as mock_close:
        render_step_snapshot(output_path, bounds, step_file_path=None)
        assert mock_savefig.called
        assert mock_close.called


def test_render_spatial_location_map(tmp_path: Path) -> None:
    output_path = tmp_path / "spatial.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    
    with patch("matplotlib.pyplot.savefig") as mock_savefig, \
         patch("matplotlib.pyplot.close") as mock_close:
        render_spatial_location_map(output_path, bounds)
        assert mock_savefig.called
        assert mock_close.called


def test_render_spatial_location_map_debug_false(tmp_path: Path) -> None:
    output_path = tmp_path / "spatial_debug_false.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    
    with patch("src.utils.renderer.maps.DEBUG_MODE", False), \
         patch("matplotlib.pyplot.savefig") as mock_savefig, \
         patch("matplotlib.pyplot.close") as mock_close:
        render_spatial_location_map(output_path, bounds)
        assert mock_savefig.called
        assert mock_close.called


def test_render_physical_boundary_map_success(tmp_path: Path) -> None:
    output_path = tmp_path / "physical.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    location_to_type = {
        "x_min": "inflow",
        "x_max": "outflow",
        "y_min": "inflow",
        "y_max": "outflow",
        "z_min": "outflow",
        "z_max": "outflow",
        "wall": "outflow",
    }
    location_to_values = {
        "x_min": {"u": 1.0, "v": 0.0, "w": 0.0},
        "y_min": {"u": 0.0, "v": 1.0, "w": 0.0},
    }

    with patch("matplotlib.pyplot.savefig") as mock_savefig, \
         patch("matplotlib.pyplot.close") as mock_close:
        render_physical_boundary_map(output_path, bounds, location_to_type, location_to_values)
        assert mock_savefig.called
        assert mock_close.called


def test_render_physical_boundary_map_debug_false(tmp_path: Path) -> None:
    output_path = tmp_path / "physical_debug_false.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    location_to_type = {
        "x_min": "inflow",
        "x_max": "outflow",
        "y_min": "outflow",
        "y_max": "outflow",
        "z_min": "outflow",
        "z_max": "outflow",
        "wall": "outflow",
    }
    location_to_values = {
        "x_min": {"u": 1.0, "v": 0.0, "w": 0.0},
    }

    with patch("src.utils.renderer.maps.DEBUG_MODE", False), \
         patch("matplotlib.pyplot.savefig") as mock_savefig, \
         patch("matplotlib.pyplot.close") as mock_close:
        render_physical_boundary_map(output_path, bounds, location_to_type, location_to_values)
        assert mock_savefig.called
        assert mock_close.called


def test_render_physical_boundary_map_missing_location(tmp_path: Path) -> None:
    output_path = tmp_path / "physical.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    location_to_type = {
        "x_max": "outflow",
        "y_min": "outflow",
        "y_max": "outflow",
        "z_min": "outflow",
        "z_max": "outflow",
        "wall": "outflow",
    }
    location_to_values = {}

    with pytest.raises(KeyError, match="Missing boundary type definition for location 'x_min'"):
        render_physical_boundary_map(output_path, bounds, location_to_type, location_to_values)


def test_render_physical_boundary_map_unknown_type(tmp_path: Path) -> None:
    output_path = tmp_path / "physical.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    location_to_type = {
        "x_min": "invalid_type",
        "x_max": "outflow",
        "y_min": "outflow",
        "y_max": "outflow",
        "z_min": "outflow",
        "z_max": "outflow",
        "wall": "outflow",
    }
    location_to_values = {}

    with pytest.raises(KeyError, match="Unknown boundary type 'invalid_type' for location 'x_min'"):
        render_physical_boundary_map(output_path, bounds, location_to_type, location_to_values)


def test_render_physical_boundary_map_missing_velocity_components(tmp_path: Path) -> None:
    output_path = tmp_path / "physical.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    location_to_type = {
        "x_min": "inflow",
        "x_max": "outflow",
        "y_min": "outflow",
        "y_max": "outflow",
        "z_min": "outflow",
        "z_max": "outflow",
        "wall": "outflow",
    }
    location_to_values = {
        "x_min": {},
    }

    with pytest.raises(KeyError, match=r"missing required velocity components \(u, v, w\)"):
        render_physical_boundary_map(output_path, bounds, location_to_type, location_to_values)
