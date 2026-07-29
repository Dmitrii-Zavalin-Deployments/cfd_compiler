"""
Unit tests for src/utils/renderer/step_parser.py
Achieves 100% branch and line coverage for STEP file parsing and geometry extraction.
"""

from pathlib import Path
from unittest.mock import patch

import src.utils.renderer.step_parser as step_parser_module
from src.utils.renderer.step_parser import parse_step_file


def test_parse_step_file_none_or_empty() -> None:
    assert parse_step_file(None) == (None, {})
    assert parse_step_file("") == (None, {})


def test_parse_step_file_not_exists(tmp_path: Path) -> None:
    non_existent = tmp_path / "non_existent.step"
    
    with patch.object(step_parser_module, "DEBUG_MODE", False):
        assert parse_step_file(non_existent) == (None, {})

    with patch.object(step_parser_module, "DEBUG_MODE", True):
        assert parse_step_file(non_existent) == (None, {})


def test_parse_step_file_read_exceptions(tmp_path: Path) -> None:
    dummy_file = tmp_path / "dummy.step"
    dummy_file.write_text("dummy")

    with patch.object(Path, "read_text", side_effect=OSError("Disk error")):
        assert parse_step_file(dummy_file) == (None, {})

    with patch.object(Path, "read_text", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
        assert parse_step_file(dummy_file) == (None, {})


def test_parse_step_file_debug_false_success(tmp_path: Path) -> None:
    step_content = """
    #1 = CARTESIAN_POINT('origin', (0.0, 0.0, 0.0));
    #20 = DIRECTION('z_dir', (0.0, 0.0, 1.0));
    #21 = DIRECTION('x_dir', (1.0, 0.0, 0.0));
    #30 = AXIS2_PLACEMENT_3D('placement1', #1, #20, #21);
    """
    step_file = tmp_path / "success.step"
    step_file.write_text(step_content)

    with patch.object(step_parser_module, "DEBUG_MODE", False):
        pts_array, axis_frame = parse_step_file(step_file)

    assert pts_array is not None
    assert "origin" in axis_frame


def test_parse_step_file_comprehensive_geometry(tmp_path: Path) -> None:
    step_content = """
    #1 = CARTESIAN_POINT('origin', (0.0, 0.0, 0.0));
    #2 = CARTESIAN_POINT('pt1', (10.0, 0.0, 0.0));
    #3 = CARTESIAN_POINT('pt2', (10.0, 10.0, 0.0));
    
    #10 = VERTEX_POINT('v1', #2);
    #11 = VERTEX_POINT('v2', #3);
    
    #20 = DIRECTION('z_dir', (0.0, 0.0, 1.0));
    #21 = DIRECTION('x_dir', (1.0, 0.0, 0.0));
    #22 = DIRECTION('zero_dir', (0.0, 0.0, 0.0));
    
    #30 = AXIS2_PLACEMENT_3D('placement1', #1, #20, #21);
    #31 = AXIS2_PLACEMENT_3D('bad_placement', #1, #22, #22);
    
    #40 = CIRCLE('circle1', #30, 5.0);
    
    #50 = EDGE_CURVE('edge1', #10, #11, #40, .T.);
    #51 = EDGE_CURVE('edge2', #10, #11, #40, .F.);
    #52 = EDGE_CURVE('edge_straight', #10, #11, #99, .T.);
    
    #60 = CYLINDRICAL_SURFACE('cyl1', #30, 5.0);
    """
    
    step_file = tmp_path / "test.step"
    step_file.write_text(step_content)

    with patch.object(step_parser_module, "DEBUG_MODE", True):
        pts_array, axis_frame = parse_step_file(step_file)

    assert pts_array is not None
    assert "origin" in axis_frame
    assert "curves" in axis_frame
    assert len(axis_frame["curves"]) > 0


def test_parse_step_file_fallback_and_no_placement_match(tmp_path: Path) -> None:
    step_content = """
    #1 = CARTESIAN_POINT('p1', (1.0, 2.0, 3.0));
    #20 = DIRECTION('z_dir', (0.0, 0.0, 1.0));
    #21 = DIRECTION('x_dir', (1.0, 0.0, 0.0));
    #30 = AXIS2_PLACEMENT_3D('placement_simple', #1, #20, #21);
    #40 = CIRCLE('circle_standalone', #30, 2.5);
    #60 = CYLINDRICAL_SURFACE('cyl_empty', #30, 2.5);
    """
    step_file = tmp_path / "fallback.step"
    step_file.write_text(step_content)

    with patch.object(step_parser_module, "DEBUG_MODE", False):
        pts_array, _axis_frame = parse_step_file(step_file)

    assert pts_array is not None


def test_parse_step_file_no_topological_points(tmp_path: Path) -> None:
    step_content = """
    #20 = DIRECTION('z_dir', (0.0, 0.0, 1.0));
    #21 = DIRECTION('x_dir', (1.0, 0.0, 0.0));
    #30 = AXIS2_PLACEMENT_3D('place', #1, #20, #21);
    #60 = CYLINDRICAL_SURFACE('cyl', #30, 10.0);
    """
    step_file = tmp_path / "no_points.step"
    step_file.write_text(step_content)

    with patch.object(step_parser_module, "DEBUG_MODE", True):
        pts_array, axis_frame = parse_step_file(step_file)

    assert pts_array is None
    assert len(axis_frame["curves"]) > 0
