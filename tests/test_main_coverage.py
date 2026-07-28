import json
import sys
from pathlib import Path

import jsonschema
import pytest

import src.main as main_module


class DummyContainerSuccess:
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


def test_config_missing_max_element_size(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Covers line 123: missing max_element_size in config."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    step_file = workspace / "test.step"
    step_file.write_text("STEP DATA")

    input_file = workspace / "input.json"
    input_file.write_text(json.dumps({
        "step_file_path": str(step_file),
        "boundary_condition_mapping": [{"location": "wall", "type": "no-slip"}]
    }))

    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps({
        "tolerance": 1e-6,
        "min_element_size": 0.001,
        "boundary_condition_mapping": []
    }))

    monkeypatch.setattr(main_module, "__file__", str(tmp_path / "src" / "main.py"))
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(workspace),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])
    monkeypatch.setattr(main_module, "validate_json", lambda data, path: None)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    assert exc_info.value.code == 1


def test_config_missing_min_element_size(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Covers line 125: missing min_element_size in config."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    step_file = workspace / "test.step"
    step_file.write_text("STEP DATA")

    input_file = workspace / "input.json"
    input_file.write_text(json.dumps({
        "step_file_path": str(step_file),
        "boundary_condition_mapping": [{"location": "wall", "type": "no-slip"}]
    }))

    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps({
        "tolerance": 1e-6,
        "max_element_size": 0.05,
        "boundary_condition_mapping": []
    }))

    monkeypatch.setattr(main_module, "__file__", str(tmp_path / "src" / "main.py"))
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(workspace),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])
    monkeypatch.setattr(main_module, "validate_json", lambda data, path: None)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    assert exc_info.value.code == 1


def test_config_missing_boundary_condition_mapping(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Covers line 127: missing boundary_condition_mapping in config."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    step_file = workspace / "test.step"
    step_file.write_text("STEP DATA")

    input_file = workspace / "input.json"
    input_file.write_text(json.dumps({
        "step_file_path": str(step_file),
        "boundary_condition_mapping": [{"location": "wall", "type": "no-slip"}]
    }))

    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps({
        "tolerance": 1e-6,
        "max_element_size": 0.05,
        "min_element_size": 0.001
    }))

    monkeypatch.setattr(main_module, "__file__", str(tmp_path / "src" / "main.py"))
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(workspace),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])
    monkeypatch.setattr(main_module, "validate_json", lambda data, path: None)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    assert exc_info.value.code == 1


def test_output_schema_validation_failure_lines(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Covers lines 231-233: Output schema validation failure."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    step_file = workspace / "test.step"
    step_file.write_text("STEP DATA")

    input_file = workspace / "input.json"
    input_file.write_text(json.dumps({
        "step_file_path": str(step_file),
        "boundary_condition_mapping": [{"location": "wall", "type": "no-slip"}]
    }))

    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps({
        "tolerance": 1e-6,
        "max_element_size": 0.05,
        "min_element_size": 0.001,
        "boundary_condition_mapping": []
    }))

    monkeypatch.setattr(main_module, "__file__", str(tmp_path / "src" / "main.py"))
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(workspace),
        "--input_file_name", "input.json",
        "--output_file_name", "output.json"
    ])
    monkeypatch.setattr(main_module, "SovereignContainer", DummyContainerSuccess)

    def mock_validate(data, schema_path):
        if "output" in str(schema_path):
            raise jsonschema.exceptions.ValidationError("Output schema invalid")

    monkeypatch.setattr(main_module, "validate_json", mock_validate)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    assert exc_info.value.code == 1


def test_output_file_write_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Covers lines 241-243: Failure writing output JSON."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    step_file = workspace / "test.step"
    step_file.write_text("STEP DATA")

    input_file = workspace / "input.json"
    input_file.write_text(json.dumps({
        "step_file_path": str(step_file),
        "boundary_condition_mapping": [{"location": "wall", "type": "no-slip"}]
    }))

    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps({
        "tolerance": 1e-6,
        "max_element_size": 0.05,
        "min_element_size": 0.001,
        "boundary_condition_mapping": []
    }))

    monkeypatch.setattr(main_module, "__file__", str(tmp_path / "src" / "main.py"))
    invalid_output_dir = workspace / "output_dir"
    invalid_output_dir.mkdir()

    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--input_output_folder", str(workspace),
        "--input_file_name", "input.json",
        "--output_file_name", "output_dir"
    ])
    monkeypatch.setattr(main_module, "SovereignContainer", DummyContainerSuccess)
    monkeypatch.setattr(main_module, "validate_json", lambda data, path: None)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    assert exc_info.value.code == 1
