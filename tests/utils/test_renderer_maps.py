"""
Unit tests for src/utils/renderer/maps.py
Achieves 100% branch and line coverage for boundary and spatial map rendering.
"""

from pathlib import Path
from unittest.mock import patch
import pytest

from src.utils.renderer.maps import (
    render_physical_boundary_map,
    render_spatial_coordination_map,
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


def test_render_spatial_coordination_map(tmp_path: Path) -> None:
    output_path = tmp_path / "spatial.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    
    with patch("matplotlib.pyplot.savefig") as mock_savefig, \
         patch("matplotlib.pyplot.close") as mock_close:
        render_spatial_coordination_map(output_path, bounds)
        assert mock_savefig.called
        assert mock_close.called


def test_render_physical_boundary_map_success(tmp_path: Path) -> None:
    output_path = tmp_path / "physical.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    boundary_conditions = [
        {"location": "x_min", "type": "inflow", "values": {"u": 1.0, "v": 0.0, "w": 0.0}},
        {"location": "x_max", "type": "outflow", "values": {}},
        {"location": "y_min", "type": "inflow", "values": {"u": 0.0, "v": 1.0, "w": 0.0}},
        {"location": "y_max", "type": "outflow", "values": {}},
        {"location": "z_min", "type": "outflow", "values": {}},
        {"location": "z_max", "type": "outflow", "values": {}},
        {"location": "wall", "type": "outflow", "values": {}},
    ]

    with patch("matplotlib.pyplot.savefig") as mock_savefig, \
         patch("matplotlib.pyplot.close") as mock_close:
        render_physical_boundary_map(output_path, bounds, boundary_conditions)
        assert mock_savefig.called
        assert mock_close.called


def test_render_physical_boundary_map_missing_location(tmp_path: Path) -> None:
    output_path = tmp_path / "physical.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    boundary_conditions = [
        {"location": "x_max", "type": "outflow", "values": {}},
        {"location": "y_min", "type": "outflow", "values": {}},
        {"location": "y_max", "type": "outflow", "values": {}},
        {"location": "z_min", "type": "outflow", "values": {}},
        {"location": "z_max", "type": "outflow", "values": {}},
        {"location": "wall", "type": "outflow", "values": {}},
    ]

    with pytest.raises(KeyError, match="Missing boundary type definition for location 'x_min'"):
        render_physical_boundary_map(output_path, bounds, boundary_conditions)


def test_render_physical_boundary_map_unknown_type(tmp_path: Path) -> None:
    output_path = tmp_path / "physical.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    boundary_conditions = [
        {"location": "x_min", "type": "invalid_type", "values": {}},
        {"location": "x_max", "type": "outflow", "values": {}},
        {"location": "y_min", "type": "outflow", "values": {}},
        {"location": "y_max", "type": "outflow", "values": {}},
        {"location": "z_min", "type": "outflow", "values": {}},
        {"location": "z_max", "type": "outflow", "values": {}},
        {"location": "wall", "type": "outflow", "values": {}},
    ]

    with pytest.raises(KeyError, match="Unknown boundary type 'invalid_type' for location 'x_min'"):
        render_physical_boundary_map(output_path, bounds, boundary_conditions)


def test_render_physical_boundary_map_missing_velocity_components(tmp_path: Path) -> None:
    output_path = tmp_path / "physical.png"
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    boundary_conditions = [
        {"location": "x_min", "type": "inflow", "values": {}},
        {"location": "x_max", "type": "outflow", "values": {}},
        {"location": "y_min", "type": "outflow", "values": {}},
        {"location": "y_max", "type": "outflow", "values": {}},
        {"location": "z_min", "type": "outflow", "values": {}},
        {"location": "z_max", "type": "outflow", "values": {}},
        {"location": "wall", "type": "outflow", "values": {}},
    ]

    with pytest.raises(KeyError, match=r"missing required velocity components \(u, v, w\)"):
        render_physical_boundary_map(output_path, bounds, boundary_conditions)
