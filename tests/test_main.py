import json
import sys
from pathlib import Path

import jsonschema
import pytest

import src.main as main_module


class DummyOrchestratorSuccess:
    """Mock orchestrator that simulates a successful pipeline run."""

    def __init__(self, steps):
        pass

    def run(self, container):
        container.status = "success"

        class BC:
            def __init__(self):
                self.location = "wall"
                self.type = "no-slip"
                self.values = {}

        container.boundary_conditions = [BC()]


def test_main_output_schema_validation_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Covers output schema validation failure handling."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    step_file = workspace / "test.step"
    step_file.write_text("STEP DATA")

    input_file = workspace / "input.json"
    input_file.write_text(
        json.dumps({
            "step_file_path": str(step_file),
            "boundary_condition_mapping": [
                {"location": "wall", "type": "no-slip"}
            ],
        })
    )

    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(
        json.dumps({
            "tolerance": 1e-6,
            "max_element_size": 0.05,
            "min_element_size": 0.001,
            "boundary_condition_mapping": [],
        })
    )

    monkeypatch.setattr(main_module, "__file__", str(tmp_path / "src" / "main.py"))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder",
            str(workspace),
            "--input_file_name",
            "input.json",
            "--output_file_name",
            "output.json",
        ],
    )

    # Mock orchestrator to prevent early exit during pipeline execution
    monkeypatch.setattr(main_module, "Orchestrator", DummyOrchestratorSuccess)

    # Allow config/input validation to pass, but raise ValidationError for output schema
    def mock_validate(data, schema_path):
        if "output" in str(schema_path):
            raise jsonschema.exceptions.ValidationError("Output schema invalid")

    monkeypatch.setattr(main_module, "validate_json", mock_validate)

    with pytest.raises((SystemExit, jsonschema.exceptions.ValidationError)):
        main_module.main()


def test_main_output_file_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Covers lines 241-243: Output JSON file write/serialization failure handling."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    step_file = workspace / "test.step"
    step_file.write_text("STEP DATA")

    input_file = workspace / "input.json"
    input_file.write_text(
        json.dumps({
            "step_file_path": str(step_file),
            "boundary_condition_mapping": [
                {"location": "wall", "type": "no-slip"}
            ],
        })
    )

    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(
        json.dumps({
            "tolerance": 1e-6,
            "max_element_size": 0.05,
            "min_element_size": 0.001,
            "boundary_condition_mapping": [],
        })
    )

    monkeypatch.setattr(main_module, "__file__", str(tmp_path / "src" / "main.py"))

    # Point output to an existing directory so opening it for writing raises IsADirectoryError
    invalid_output_dir = workspace / "output_dir"
    invalid_output_dir.mkdir()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--input_output_folder",
            str(workspace),
            "--input_file_name",
            "input.json",
            "--output_file_name",
            "output_dir",
        ],
    )

    # Mock orchestrator to prevent early exit during pipeline execution
    monkeypatch.setattr(main_module, "Orchestrator", DummyOrchestratorSuccess)
    monkeypatch.setattr(main_module, "validate_json", lambda data, path: None)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    assert exc_info.value.code == 1