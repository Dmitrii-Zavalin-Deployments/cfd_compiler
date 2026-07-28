import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src import main as main_module
from src.main import main


def test_main_missing_input_file_exits(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests that a non-existent input file triggers sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", "non_existent.json",
        "--output_file_name", "output.json",
    ])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_missing_config_file_exits(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests that missing config/config.json triggers sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    mock_schemas_and_config["config_file"].unlink()

    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", "input_contract.json",
        "--output_file_name", "output.json",
    ])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_corrupt_config_file_exits(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests that malformed JSON in config/config.json triggers sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    mock_schemas_and_config["config_file"].write_text("{corrupt_json: true", encoding="utf-8")

    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", "input_contract.json",
        "--output_file_name", "output.json",
    ])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_corrupt_input_file_exits(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests that malformed JSON in input contract triggers sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    mock_schemas_and_config["input_json"].write_text("NOT_VALID_JSON", encoding="utf-8")

    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", "input_contract.json",
        "--output_file_name", "output.json",
    ])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_missing_config_required_key_exits(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests that missing required parameters in config.json trigger KeyError exit."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    config_file = mock_schemas_and_config["config_file"]

    incomplete_config = {
        "max_element_size": 0.05,
        "min_element_size": 0.001,
        "boundary_condition_mapping": {},
    }
    config_file.write_text(json.dumps(incomplete_config), encoding="utf-8")

    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", "input_contract.json",
        "--output_file_name", "output.json",
    ])

    with patch("src.main.validate_json"), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_missing_input_required_key_exits(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests that missing required keys in input contract trigger KeyError sys.exit(1)."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    input_file = mock_schemas_and_config["input_json"]

    invalid_input = {"step_file_path": "/tmp/test.step"}
    input_file.write_text(json.dumps(invalid_input), encoding="utf-8")

    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", "input_contract.json",
        "--output_file_name", "output.json",
    ])

    with patch("src.main.validate_json"), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


@pytest.mark.parametrize("missing_key", [
    "max_element_size",
    "min_element_size",
    "boundary_condition_mapping"
])
def test_main_config_missing_required_keys(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing_key: str):
    """Covers strict No-Default policy key checks in config."""
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

    orig_load = json.load
    def mock_json_load(f):
        data = orig_load(f)
        if isinstance(data, dict) and missing_key in data:
            data.pop(missing_key)
        return data

    monkeypatch.setattr(json, "load", mock_json_load)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    assert exc_info.value.code == 1


def test_main_input_missing_step_file_path(mock_schemas_and_config, monkeypatch: pytest.MonkeyPatch):
    """Tests failure when 'step_file_path' is missing in the input payload."""
    workspace_dir = mock_schemas_and_config["workspace_dir"]
    output_json = workspace_dir / "output.json"

    bad_input_json = workspace_dir / "bad_input.json"
    bad_input_json.write_text(json.dumps({"boundary_condition_mapping": {}}), encoding="utf-8")

    monkeypatch.setattr("sys.argv", [
        "main.py",
        "--input_output_folder", str(workspace_dir),
        "--input_file_name", bad_input_json.name,
        "--output_file_name", output_json.name
    ])
    monkeypatch.setattr("src.main.validate_json", lambda data, path: None)

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
