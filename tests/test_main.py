"""
Unit tests for CFD Compiler CLI Entry Point (src/main.py).
Ensures 100% statement and branch coverage across all execution paths,
schema validations, error traps, and strict No-Default policy checks.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from jsonschema import ValidationError

from src.main import main, validate_json
from tests.conftest import dummy_in, dummy_out

# --- MOCK DATA STRUCTURES ---


@dataclass
class DummyBoundaryCondition:
    location: str
    type: str
    values: dict[str, Any]


# --- FIXTURES ---


@pytest.fixture
def mock_schemas_and_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Sets up a completely isolated workspace directory structure containing valid JSON schemas and configuration files for main.py testing."""
    root_dir = tmp_path
    src_dir = root_dir / "src"
    config_dir = root_dir / "config"
    schema_dir = root_dir / "schema"
    workspace_dir = root_dir / "workspace"

    src_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    schema_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Patch __file__ in src.main so root_dir resolves to tmp_path
    fake_main_file = src_dir / "main.py"
    fake_main_file.touch()
    monkeypatch.setattr("src.main.__file__", str(fake_main_file))

    # 1. Config Schema
    config_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "tolerance": {"type": "number"},
            "max_element_size": {"type": "number"},
            "min_element_size": {"type": "number"},
            "boundary_condition_mapping": {"type": "array"},
        },
        "required": [
            "tolerance",
            "max_element_size",
            "min_element_size",
            "boundary_condition_mapping",
        ],
    }
    with open(
        schema_dir / "cfd_compiler_config_schema.json", "w", encoding="utf-8"
    ) as f:
        json.dump(config_schema, f)

    # 2. Input Schema
    input_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "step_file_path": {"type": "string"},
            "boundary_condition_mapping": {"type": "array"},
        },
        "required": ["step_file_path", "boundary_condition_mapping"],
    }
    with open(
        schema_dir / "cfd_compiler_input_schema.json", "w", encoding="utf-8"
    ) as f:
        json.dump(input_schema, f)

    # 3. Output Schema
    output_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "config": {"type": "object"},
            "input": {"type": "object"},
            "results": {"type": "object"},
        },
        "required": ["config", "input", "results"],
    }
    with open(
        schema_dir / "cfd_compiler_output_schema.json", "w", encoding="utf-8"
    ) as f:
        json.dump(output_schema, f)

    # 4. Valid Config File
    valid_config = {
        "tolerance": 1e-6,
        "max_element_size": 0.05,
        "min_element_size": 0.001,
        "boundary_condition_mapping": [
            {"location": "inlet", "type": "inflow", "values": {"u": 1.0, "v": 0.0, "w": 0.0}},
            {"location": "outlet", "type": "outflow", "values": {"p": 0.0}}
        ],
    }
    with open(config_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(valid_config, f)

    # 5. Dummy STEP File
    step_file = workspace_dir / "geometry.step"
    step_file.write_text(
        "ISO-10303-21 HEADER; ENDSEC; DATA; ENDSEC; END-ISO-10303-21;"
    )

    # 6. Valid Input JSON derived from dummy_in schema fixture
    valid_input = dummy_in().override(
        step_file_path=str(step_file),
        boundary_condition_mapping=[{"location": "x_min", "type": "inflow", "values": {"u": 1.0, "v": 0.0, "w": 0.0}}],
    )
    input_json_path = workspace_dir / "input_contract.json"
    with open(input_json_path, "w", encoding="utf-8") as f:
        json.dump(valid_input, f)

    return {
        "root_dir": root_dir,
        "workspace_dir": workspace_dir,
        "config_file": config_dir / "config.json",
        "input_json": input_json_path,
        "step_file": step_file,
    }


# --- TESTS: validate_json ---


def test_validate_json_missing_schema_raises_file_not_found_error(
    tmp_path: Path,
):
    """Validates that a missing schema file triggers FileNotFoundError and critical logging."""
    non_existent_schema = tmp_path / "missing_schema.json"
    with pytest.raises(
        FileNotFoundError, match="CONSTITUTION VIOLATION: Schema file not found"
    ):
        validate_json({"data": 1}, non_existent_schema)


def test_validate_json_schema_validation_error_raises_and_logs(
    tmp_path: Path,
):
    """Validates that schema compliance mismatches trigger ValidationError."""
    schema_path = tmp_path / "simple_schema.json"
    schema = {
        "type": "object",
        "properties": {"req_val": {"type": "integer"}},
        "required": ["req_val"],
    }
    schema_path.write_text(json.dumps(schema), encoding="utf-8")

    invalid_data = {"req_val": "not_an_integer"}
    with pytest.raises(ValidationError):
        validate_json(invalid_data, schema_path)


def test_validate_json_success(tmp_path: Path):
    """Validates successful schema validation execution."""
    schema_path = tmp_path / "simple_schema.json"
    schema = {
        "type": "object",
        "properties": {"req_val": {"type": "integer"}},
        "required": ["req_val"],
    }
    schema_path.write_text(json.dumps(schema), encoding="utf-8")

    valid_data = {"req_val": 42}
    validate_json(valid_data, schema_path)


# --- TESTS: main() CLI & PATH RESOLUTION ---


def test_main_missing_input_file_exits(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests that a non-existent input file triggers sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        "non_existent.json",
        "--output_file_name",
        "output.json",
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_missing_config_file_exits(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests that missing config/config.json triggers sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    config_file = mock_schemas_and_config["config_file"]
    config_file.unlink()

    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        "input_contract.json",
        "--output_file_name",
        "output.json",
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_corrupt_config_file_exits(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests that malformed JSON in config/config.json triggers sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    config_file = mock_schemas_and_config["config_file"]
    config_file.write_text("{corrupt_json: true", encoding="utf-8")

    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        "input_contract.json",
        "--output_file_name",
        "output.json",
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_missing_config_required_key_exits(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests that missing required parameters in config.json trigger Constitution KeyError exit."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    config_file = mock_schemas_and_config["config_file"]

    # Incomplete config missing 'tolerance'
    incomplete_config = {
        "max_element_size": 0.05,
        "min_element_size": 0.001,
        "boundary_condition_mapping": {},
    }
    config_file.write_text(json.dumps(incomplete_config), encoding="utf-8")

    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        "input_contract.json",
        "--output_file_name",
        "output.json",
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with patch("src.main.validate_json"), pytest.raises(
        SystemExit
    ) as exc_info:
        main()
    assert exc_info.value.code == 1


# --- TESTS: INPUT INGESTION & SCHEMAS ---


def test_main_corrupt_input_file_exits(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests that malformed JSON in input contract triggers sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    input_file = mock_schemas_and_config["input_json"]
    input_file.write_text("NOT_VALID_JSON", encoding="utf-8")

    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        "input_contract.json",
        "--output_file_name",
        "output.json",
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_missing_input_required_key_exits(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests that missing required keys in input contract trigger KeyError sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    input_file = mock_schemas_and_config["input_json"]

    invalid_input = {"step_file_path": "/tmp/test.step"}
    input_file.write_text(json.dumps(invalid_input), encoding="utf-8")

    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        "input_contract.json",
        "--output_file_name",
        "output.json",
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with patch("src.main.validate_json"), pytest.raises(
        SystemExit
    ) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_step_file_input_branch_success(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests direct STEP file ingestion branch (.step or .stp extension)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    step_file = mock_schemas_and_config["step_file"]

    output_path = workspace_dir / "output_step.json"

    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        step_file.name,
        "--output_file_name",
        output_path.name,
    ]
    monkeypatch.setattr("sys.argv", test_args)

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
        container.bounding_box = {"min": [0, 0, 0], "max": [1, 1, 1]}
        container.compiled_cells_count = d_out["compiled_cells_count"]
        container.artifacts_generated = d_out["artifacts_generated"]

    with patch("src.main.Orchestrator.run", side_effect=mock_run, autospec=True):
        main()

    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["results"]["status"] == d_out["status"]


# --- TESTS: PIPELINE EXECUTION & POST-PROCESSING ---


def test_main_pipeline_fault_exits(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests that an exception thrown during pipeline orchestration triggers sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]

    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        "input_contract.json",
        "--output_file_name",
        "output.json",
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with patch(
        "src.main.Orchestrator.run",
        side_effect=RuntimeError("Solver Convergence Fault"),
    ), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_boundary_conditions_none_exits(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests that uninitialized boundary conditions post-execution trigger Constitution exit."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]

    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        "input_contract.json",
        "--output_file_name",
        "output.json",
    ]
    monkeypatch.setattr("sys.argv", test_args)

    def mock_run_no_bc(self, container):
        container.boundary_conditions = None

    with patch(
        "src.main.Orchestrator.run", side_effect=mock_run_no_bc, autospec=True
    ), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_output_write_failure_exits(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests that I/O write failures when saving output payload trigger sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]

    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        "input_contract.json",
        "--output_file_name",
        "output.json",
    ]
    monkeypatch.setattr("sys.argv", test_args)

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
    ), pytest.raises(
        SystemExit
    ) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_non_success_status_exits(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests that a non-'success' container status post-execution triggers sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]

    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        "input_contract.json",
        "--output_file_name",
        "output.json",
    ]
    monkeypatch.setattr("sys.argv", test_args)

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


# --- TESTS: END-TO-END SUCCESS & ABSOLUTE PATHS ---


def test_main_absolute_paths_success(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests full execution using absolute paths for input and output files."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    input_json = mock_schemas_and_config["input_json"].resolve()
    output_json = (workspace_dir / "abs_output.json").resolve()

    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        str(input_json),
        "--output_file_name",
        str(output_json),
    ]
    monkeypatch.setattr("sys.argv", test_args)

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
        container.bounding_box = {"min": [0, 0, 0], "max": [2, 2, 2]}
        container.compiled_cells_count = d_out["compiled_cells_count"]
        container.artifacts_generated = d_out["artifacts_generated"]

    with patch(
        "src.main.Orchestrator.run", side_effect=mock_run_success, autospec=True
    ):
        main()

    assert output_json.exists()
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["results"]["status"] == d_out["status"]
    assert (
        payload["results"]["compiled_cells_count"]
        == d_out["compiled_cells_count"]
    )


def test_main_relative_paths_success(
    mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch
):
    """Tests full execution using relative paths resolved against workspace_dir."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    output_json = workspace_dir / "rel_output.json"

    test_args = [
        "main.py",
        "--input_output_folder",
        str(workspace_dir),
        "--input_file_name",
        "input_contract.json",
        "--output_file_name",
        "rel_output.json",
    ]
    monkeypatch.setattr("sys.argv", test_args)

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
        container.bounding_box = {"min": [0, 0, 0], "max": [1, 1, 1]}
        container.compiled_cells_count = d_out["compiled_cells_count"]
        container.artifacts_generated = d_out["artifacts_generated"]

    with patch(
        "src.main.Orchestrator.run", side_effect=mock_run_success, autospec=True
    ):
        main()

    assert output_json.exists()
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["results"]["status"] == d_out["status"]