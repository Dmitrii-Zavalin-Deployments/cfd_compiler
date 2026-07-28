import json
from unittest.mock import patch

import pytest

from src.main import main
from tests.conftest import DummyBoundaryCondition, dummy_out


def test_main_step_file_input_branch_success(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests direct STEP file ingestion branch (.step or .stp extension)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    step_file = mock_schemas_and_config["step_file"]
    output_path = workspace_dir / "output_step.json"

    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", step_file.name,
        "--output_file_name", output_path.name,
    ])

    d_out = dummy_out()

    def mock_run(self, container):
        container.boundary_conditions = [
            DummyBoundaryCondition(
                location=bc["location"],
                type=bc["type"],
                values=bc["values"],
            )
            for bc in d_out["boundary_conditions"]
        ]
        container.status = d_out["status"]
        container.bounding_box = (0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
        container.compiled_cells_count = d_out["compiled_cells_count"]
        container.artifacts_generated = d_out["artifacts_generated"]

    with patch("src.main.Orchestrator.run", side_effect=mock_run, autospec=True):
        main()

    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["results"]["status"] == d_out["status"]


def test_main_pipeline_fault_exits(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests that an exception thrown during pipeline orchestration triggers sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", "input_contract.json",
        "--output_file_name", "output.json",
    ])

    with patch(
        "src.main.Orchestrator.run",
        side_effect=RuntimeError("Solver Convergence Fault"),
    ), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_boundary_conditions_none_exits(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests that uninitialized boundary conditions post-execution trigger exit."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", "input_contract.json",
        "--output_file_name", "output.json",
    ])

    def mock_run_no_bc(self, container):
        container.boundary_conditions = None

    with patch(
        "src.main.Orchestrator.run", side_effect=mock_run_no_bc, autospec=True
    ), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_output_write_failure_exits(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests that I/O write failures when saving output payload trigger sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", "input_contract.json",
        "--output_file_name", "output.json",
    ])

    d_out = dummy_out()

    def mock_run(self, container):
        container.boundary_conditions = [
            DummyBoundaryCondition(
                location=bc["location"],
                type=bc["type"],
                values=bc["values"],
            )
            for bc in d_out["boundary_conditions"]
        ]

    with patch(
        "src.main.Orchestrator.run", side_effect=mock_run, autospec=True
    ), patch(
        "builtins.open",
        side_effect=[
            open(mock_schemas_and_config["config_file"], "r", encoding="utf-8"),
            open(mock_schemas_and_config["input_json"], "r", encoding="utf-8"),
            PermissionError("Disk write error"),
        ],
    ), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_non_success_status_exits(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests that a non-'success' container status post-execution triggers sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", "input_contract.json",
        "--output_file_name", "output.json",
    ])

    d_out = dummy_out()

    def mock_run_partial(self, container):
        container.boundary_conditions = [
            DummyBoundaryCondition(
                location=bc["location"],
                type=bc["type"],
                values=bc["values"],
            )
            for bc in d_out["boundary_conditions"]
        ]
        container.status = "partial_failure"

    with patch(
        "src.main.Orchestrator.run", side_effect=mock_run_partial, autospec=True
    ), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_absolute_paths_success(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests full execution using absolute paths for input and output files."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    input_json = mock_schemas_and_config["input_json"].resolve()
    output_json = (workspace_dir / "abs_output.json").resolve()

    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", str(input_json),
        "--output_file_name", str(output_json),
    ])

    d_out = dummy_out()

    def mock_run_success(self, container):
        container.boundary_conditions = [
            DummyBoundaryCondition(
                location=bc["location"],
                type=bc["type"],
                values=bc["values"],
            )
            for bc in d_out["boundary_conditions"]
        ]
        container.status = d_out["status"]
        container.bounding_box = (0.0, 0.0, 0.0, 2.0, 2.0, 2.0)
        container.compiled_cells_count = d_out["compiled_cells_count"]
        container.artifacts_generated = d_out["artifacts_generated"]

    with patch("src.main.Orchestrator.run", side_effect=mock_run_success, autospec=True):
        main()

    assert output_json.exists()
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["results"]["status"] == d_out["status"]
    assert payload["results"]["compiled_cells_count"] == d_out["compiled_cells_count"]


def test_main_relative_paths_success(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests full execution using relative paths resolved against workspace_dir."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    output_json = workspace_dir / "rel_output.json"

    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", "input_contract.json",
        "--output_file_name", "rel_output.json",
    ])

    d_out = dummy_out()

    def mock_run_success(self, container):
        container.boundary_conditions = [
            DummyBoundaryCondition(
                location=bc["location"],
                type=bc["type"],
                values=bc["values"],
            )
            for bc in d_out["boundary_conditions"]
        ]
        container.status = d_out["status"]
        container.bounding_box = (0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
        container.compiled_cells_count = d_out["compiled_cells_count"]
        container.artifacts_generated = d_out["artifacts_generated"]

    with patch("src.main.Orchestrator.run", side_effect=mock_run_success, autospec=True):
        main()

    assert output_json.exists()
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["results"]["status"] == d_out["status"]
