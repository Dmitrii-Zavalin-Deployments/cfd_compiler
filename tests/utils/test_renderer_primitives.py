"""
Unit tests for src/utils/renderer/primitives.py
Achieves 100% branch and line coverage for rendering primitive functions.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from src.utils.renderer.primitives import (
    apply_bounds_padding,
    draw_alternating_edge,
    draw_domain_geometry,
    get_face_centroid,
)
import src.utils.renderer.primitives as primitives_module


def test_get_face_centroid_success() -> None:
    bounds = (0.0, 10.0, 0.0, 20.0, 0.0, 30.0)
    # xmin=0, xmax=10 -> mid_x=5
    # ymin=0, ymax=20 -> mid_y=10
    # zmin=0, zmax=30 -> mid_z=15

    assert get_face_centroid("x_min", bounds) == (0.0, 10.0, 15.0)
    assert get_face_centroid("x_max", bounds) == (10.0, 10.0, 15.0)
    assert get_face_centroid("y_min", bounds) == (5.0, 0.0, 15.0)
    assert get_face_centroid("y_max", bounds) == (5.0, 20.0, 15.0)
    assert get_face_centroid("z_min", bounds) == (5.0, 10.0, 0.0)
    assert get_face_centroid("z_max", bounds) == (5.0, 10.0, 30.0)
    assert get_face_centroid("wall", bounds) == (5.0, 10.0, 15.0)


def test_get_face_centroid_invalid_location() -> None:
    bounds = (0.0, 10.0, 0.0, 20.0, 0.0, 30.0)
    with pytest.raises(KeyError, match="Invalid location 'invalid_loc' requested"):
        get_face_centroid("invalid_loc", bounds)


def test_draw_alternating_edge() -> None:
    mock_ax = MagicMock()
    p1 = (0.0, 0.0, 0.0)
    p2 = (10.0, 10.0, 10.0)
    draw_alternating_edge(mock_ax, p1, p2, "#FF0000", "#00FF00", num_segments=4)
    assert mock_ax.plot3D.call_count == 4


def test_apply_bounds_padding() -> None:
    # Case 1: Normal bounds with margin
    bounds = (0.0, 10.0, 0.0, 20.0, 0.0, 30.0)
    padded = apply_bounds_padding(bounds, margin=0.1)
    assert padded == (-1.0, 11.0, -2.0, 22.0, -3.0, 33.0)

    # Case 2: Degenerate bounds (xmax <= xmin, etc.) triggering 1.0 fallback
    deg_bounds = (5.0, 5.0, 10.0, 10.0, 15.0, 15.0)
    padded_deg = apply_bounds_padding(deg_bounds, margin=0.1)
    assert padded_deg == (4.0, 6.0, 9.0, 11.0, 14.0, 16.0)


def test_draw_domain_geometry_success(tmp_path: Path) -> None:
    mock_ax = MagicMock()
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    required_faces = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "wall"]
    face_color_dict = {loc: "#FFFFFF" for loc in required_faces}

    mock_curves = [np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]])]
    mock_axis_frame = {
        "origin": np.array([5.0, 5.0, 5.0]),
        "x_axis": np.array([1.0, 0.0, 0.0]),
        "y_axis": np.array([0.0, 1.0, 0.0]),
        "z_axis": np.array([0.0, 0.0, 1.0]),
        "curves": mock_curves,
    }

    with patch.object(primitives_module, "parse_step_file", return_value=(None, mock_axis_frame)), \
         patch.object(primitives_module, "DEBUG_MODE", True):
        draw_domain_geometry(mock_ax, bounds, face_color_dict, step_file_path="test.step", padding_margin=0.05)

    assert mock_ax.add_collection3d.called
    assert mock_ax.plot3D.called
    assert mock_ax.quiver.called


def test_draw_domain_geometry_missing_face() -> None:
    mock_ax = MagicMock()
    bounds = (0.0, 10.0, 0.0, 10.0, 0.0, 10.0)
    # Missing 'wall'
    face_color_dict = {
        "x_min": "#FFFFFF",
        "x_max": "#FFFFFF",
        "y_min": "#FFFFFF",
        "y_max": "#FFFFFF",
        "z_min": "#FFFFFF",
        "z_max": "#FFFFFF",
    }

    with pytest.raises(KeyError, match="Missing face color for location 'wall'"):
        draw_domain_geometry(mock_ax, bounds, face_color_dict)


def test_draw_domain_geometry_degenerate_and_default_origin() -> None:
    mock_ax = MagicMock()
    # Degenerate bounds where min == max (box_scale <= 0 triggers 1.0 fallback, origin=None triggers midpoint fallback)
    bounds = (5.0, 5.0, 5.0, 5.0, 5.0, 5.0)
    required_faces = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "wall"]
    face_color_dict = {loc: "#FFFFFF" for loc in required_faces}

    mock_axis_frame = {
        "origin": None,
        "x_axis": np.array([1.0, 0.0, 0.0]),
        "y_axis": np.array([0.0, 1.0, 0.0]),
        "z_axis": np.array([0.0, 0.0, 1.0]),
        "curves": [],
    }

    with patch.object(primitives_module, "parse_step_file", return_value=(None, mock_axis_frame)), \
         patch.object(primitives_module, "DEBUG_MODE", False):
        draw_domain_geometry(mock_ax, bounds, face_color_dict)

    assert mock_ax.quiver.called
