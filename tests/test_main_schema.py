import json
import sys
from pathlib import Path

import jsonschema
import pytest
from jsonschema import ValidationError

from src import main as main_module
from src.main import validate_json


def test_validate_json_missing_schema_raises_file_not_found_error(tmp_path: Path):
    """Validates that a missing schema file triggers FileNotFoundError."""
    non_existent_schema = tmp_path / "missing_schema.json"
    with pytest.raises(
        FileNotFoundError, match="CONSTITUTION VIOLATION: Schema file not found"
    ):
        validate_json({"data": 1}, non_existent_schema)


def test_validate_json_schema_validation_error_raises_and_logs(tmp_path: Path):
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


def test_main_config_schema_generic_exception(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Covers generic exception during config schema validation."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    input_file = workspace / "input.json"
    input_file.write_text(json.dumps({
        "step_file_path": "dummy.step",
        "boundary_condition_mapping": {"wall": "no-slip"}
    }))

    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(workspace),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])

    def mock_validate(data, schema_path):
        if "config" in str(schema_path):
            raise RuntimeError("Unexpected non-validation error")

    monkeypatch.setattr(main_module, "validate_json", mock_validate)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    assert exc_info.value.code == 1


def test_main_input_schema_validation_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Covers input schema validation failure."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    input_file = workspace / "input.json"
    input_file.write_text(json.dumps({"invalid_contract": True}))

    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(workspace),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])

    def mock_validate(data, schema_path):
        if "input" in str(schema_path):
            raise jsonschema.exceptions.ValidationError("Input schema violation")

    monkeypatch.setattr(main_module, "validate_json", mock_validate)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    assert exc_info.value.code == 1


def test_main_output_schema_validation_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Covers output schema validation failure."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    step_file = workspace / "test.step"
    step_file.write_text("STEP DATA")

    input_file = workspace / "input.json"
    input_file.write_text(json.dumps({
        "step_file_path": str(step_file),
        "boundary_condition_mapping": [{"location": "wall", "type": "no-slip"}]
    }))

    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(workspace),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])

    class DummyContainer:
        def __init__(self, **kwargs):
            self.status = "success"
            self.bounding_box = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
            self.compiled_cells_count = 100
            self.artifacts_generated = []

            class BC:
                def __init__(self):
                    self.location = "wall"
                    self.type = "no-slip"
                    self.values = {}

            self.boundary_conditions = [BC()]

    monkeypatch.setattr(main_module, "SovereignContainer", DummyContainer)

    def mock_validate(data, schema_path):
        if "output" in str(schema_path):
            raise jsonschema.exceptions.ValidationError("Output schema violation")

    monkeypatch.setattr(main_module, "validate_json", mock_validate)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    assert exc_info.value.code == 1