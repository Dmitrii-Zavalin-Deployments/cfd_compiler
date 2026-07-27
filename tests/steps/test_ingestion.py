"""
Unit tests for CFD Compiler Stage 1: Ingestion Step (src/steps/ingestion.py).

Validates:
- Successful STEP file reading, CAD shape extraction, and spatial bounding box calculation.
- Module-level HAS_OCC fallback behavior when OpenCASCADE import fails (Lines 12-13).
- Strict OpenCASCADE requirement check during execution (ImportError).
- Non-existent STEP file path validation (FileNotFoundError).
- Non-zero status return from STEP reader (RuntimeError).
- Memory discipline via __slots__ enforcement.
- Standardized informational logging.
"""

import importlib
import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.state.cfd_compiler_state import SovereignContainer
import src.steps.ingestion
from src.steps.ingestion import IngestionStep


# --- FIXTURES ---

@pytest.fixture
def ingestion_step() -> IngestionStep:
    """Provides an instance of IngestionStep."""
    return IngestionStep()


@pytest.fixture
def mock_container(tmp_path: Path) -> SovereignContainer:
    """Provides a mock SovereignContainer instance with a valid temporary STEP file path."""
    step_file = tmp_path / "test_geometry.step"
    step_file.write_text("HEADER; DATA; ENDSEC;")  # Dummy STEP content

    container = MagicMock(spec=SovereignContainer)
    container.step_file_path = str(step_file)
    container.cad_solid = None
    container.bounding_box = None
    return container


# --- TESTS: MODULE IMPORT FALLBACK ---

def test_ingestion_has_occ_import_error_coverage(monkeypatch):
    """
    Verifies lines 12-13 (except ImportError: HAS_OCC = False) by forcing an 
    ImportError on OpenCASCADE modules during module reload.
    """
    orig_import = __builtins__["__import__"]

    def mock_failing_import(name, *args, **kwargs):
        if name.startswith("OCC"):
            raise ImportError("Simulated missing OpenCASCADE dependency")
        return orig_import(name, *args, **kwargs)

    try:
        monkeypatch.setattr("builtins.__import__", mock_failing_import)
        importlib.reload(src.steps.ingestion)
        assert src.steps.ingestion.HAS_OCC is False
    finally:
        # Restore normal module state
        monkeypatch.undo()
        importlib.reload(src.steps.ingestion)


# --- TESTS: HAPPY PATH & BOUNDING BOX CALCULATION ---

def test_ingestion_step_success(
    ingestion_step: IngestionStep, mock_container: SovereignContainer, monkeypatch, caplog
):
    """
    Verifies successful execution, STEP reading, shape assignment, 
    and (xmin, xmax, ymin, ymax, zmin, zmax) bounding box formatting.
    """
    mock_shape = MagicMock(name="TopoDS_Shape")
    mock_reader = MagicMock()
    mock_reader.ReadFile.return_value = 1  # 1 == IFSelect_RetDone
    mock_reader.Shape.return_value = mock_shape

    mock_bnd_box = MagicMock()
    # Get() returns (xmin, ymin, zmin, xmax, ymax, zmax)
    mock_bnd_box.Get.return_value = (-10.0, -20.0, -30.0, 10.0, 20.0, 30.0)

    mock_brepbndlib = MagicMock()

    monkeypatch.setattr("src.steps.ingestion.HAS_OCC", True)
    monkeypatch.setattr("src.steps.ingestion.STEPControl_Reader", lambda: mock_reader)
    monkeypatch.setattr("src.steps.ingestion.Bnd_Box", lambda: mock_bnd_box)
    monkeypatch.setattr("src.steps.ingestion.brepbndlib", mock_brepbndlib)

    with caplog.at_level(logging.INFO):
        ingestion_step.execute(mock_container)

    # Validate OpenCASCADE operations
    mock_reader.ReadFile.assert_called_once_with(mock_container.step_file_path)
    mock_reader.TransferRoots.assert_called_once()
    mock_brepbndlib.Add.assert_called_once_with(mock_shape, mock_bnd_box)

    # Validate container updates (xmin, xmax, ymin, ymax, zmin, zmax)
    assert mock_container.cad_solid is mock_shape
    assert mock_container.bounding_box == (-10.0, 10.0, -20.0, 20.0, -30.0, 30.0)

    # Validate logging
    assert f"Executing IngestionStep for: {mock_container.step_file_path}" in caplog.text
    assert "OCC Bounding Box parsed successfully from geometry:" in caplog.text


# --- TESTS: CONSTITUTION VIOLATIONS & EXCEPTIONS ---

def test_ingestion_step_missing_occ_dependency(
    ingestion_step: IngestionStep, mock_container: SovereignContainer, monkeypatch
):
    """
    Verifies that execute() raises ImportError when HAS_OCC is False (Lines 29-32).
    """
    monkeypatch.setattr("src.steps.ingestion.HAS_OCC", False)

    with pytest.raises(
        ImportError,
        match=r"CONSTITUTION VIOLATION: OpenCASCADE \(pythonocc\) is required for CAD ingestion\."
    ):
        ingestion_step.execute(mock_container)


def test_ingestion_step_file_not_found(
    ingestion_step: IngestionStep, mock_container: SovereignContainer, monkeypatch
):
    """
    Verifies that execute() raises FileNotFoundError when step_file_path does not exist (Lines 35-38).
    """
    monkeypatch.setattr("src.steps.ingestion.HAS_OCC", True)
    mock_container.step_file_path = "/nonexistent/path/to/missing.step"

    with pytest.raises(
        FileNotFoundError,
        match=r"CONSTITUTION VIOLATION: STEP file not found at path '.*missing\.step'\. Execution halted\."
    ):
        ingestion_step.execute(mock_container)


@pytest.mark.parametrize("failed_status", [0, 2, -1])
def test_ingestion_step_read_file_failure(
    ingestion_step: IngestionStep, mock_container: SovereignContainer, monkeypatch, failed_status: int
):
    """
    Verifies that execute() raises RuntimeError when STEP reader status is not 1 (Lines 42-45).
    """
    mock_reader = MagicMock()
    mock_reader.ReadFile.return_value = failed_status

    monkeypatch.setattr("src.steps.ingestion.HAS_OCC", True)
    monkeypatch.setattr("src.steps.ingestion.STEPControl_Reader", lambda: mock_reader)

    with pytest.raises(
        RuntimeError,
        match=rf"CONSTITUTION VIOLATION: Failed to read STEP geometry at '.*' \(status code: {failed_status}\)\. Execution halted\."
    ):
        ingestion_step.execute(mock_container)


# --- TESTS: MEMORY & SLOTS ENFORCEMENT ---

def test_ingestion_step_slots_enforcement(ingestion_step: IngestionStep):
    """
    Verifies that IngestionStep enforces __slots__ = () preventing dynamic attribute allocation.
    """
    with pytest.raises(AttributeError, match="'IngestionStep' object has no attribute 'dynamic_attr'"):
        ingestion_step.dynamic_attr = "unauthorized"  # type: ignore
