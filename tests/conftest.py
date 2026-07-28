import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest


class dummy_in(dict):
    def __init__(self):
        # 1. Initialize primary fields from cfd_compiler_input_schema.json
        super().__init__({
            "step_file_path": "./assets/geometry.step"
        })

    def override(self, **kwargs):
        """Updates dictionary strictly for schema fields."""
        for key, value in kwargs.items():
            self[key] = value
        return self


class dummy_out(dict):
    def __init__(self):
        # 1. Initialize primary fields from cfd_compiler_results_schema.json
        super().__init__({
            "status": "success",
            "compiled_cells_count": 24576,
            "boundary_conditions": [
                {
                    "location": "x_min",
                    "type": "inflow",
                    "values": {"u": 2.5, "v": 0.0, "w": 0.0, "p": 101325.0}
                },
                {
                    "location": "x_max",
                    "type": "outflow",
                    "values": {"p": 100000.0}
                },
                {
                    "location": "wall",
                    "type": "no-slip",
                    "values": {"u": 0.0, "v": 0.0, "w": 0.0}
                },
                {
                    "location": "y_min",
                    "type": "free-slip",
                    "values": {"u": 0.0, "v": 0.0, "w": 0.0}
                },
                {
                    "location": "y_max",
                    "type": "free-slip",
                    "values": {"u": 0.0, "v": 0.0, "w": 0.0}
                },
                {
                    "location": "z_min",
                    "type": "free-slip",
                    "values": {"u": 0.0, "v": 0.0, "w": 0.0}
                },
                {
                    "location": "z_max",
                    "type": "free-slip",
                    "values": {"u": 0.0, "v": 0.0, "w": 0.0}
                }
            ],
            "artifacts_generated": [
                "spatial_location_map.png",
                "physical_boundary_map.png"
            ]
        })

    def override(self, **kwargs):
        """Updates dictionary strictly for schema fields."""
        for key, value in kwargs.items():
            self[key] = value
        return self


@dataclass
class DummyBoundaryCondition:
    location: str
    type: str
    values: dict[str, Any]


@pytest.fixture
def mock_schemas_and_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Sets up an isolated workspace directory structure containing valid JSON schemas and config."""
    root_dir = tmp_path
    src_dir = root_dir / "src"
    config_dir = root_dir / "config"
    schema_dir = root_dir / "schema"
    workspace_dir = root_dir / "workspace"

    src_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    schema_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)

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
    (schema_dir / "cfd_compiler_config_schema.json").write_text(
        json.dumps(config_schema), encoding="utf-8"
    )

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
    (schema_dir / "cfd_compiler_input_schema.json").write_text(
        json.dumps(input_schema), encoding="utf-8"
    )

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
    (schema_dir / "cfd_compiler_output_schema.json").write_text(
        json.dumps(output_schema), encoding="utf-8"
    )

    # 4. Valid Config File
    valid_config = {
        "tolerance": 1e-6,
        "max_element_size": 0.05,
        "min_element_size": 0.001,
        "boundary_condition_mapping": [
            {"location": "inlet", "type": "inflow", "values": {"u": 1.0, "v": 0.0, "w": 0.0}},
            {"location": "outlet", "type": "outflow", "values": {"p": 0.0}},
        ],
    }
    (config_dir / "config.json").write_text(
        json.dumps(valid_config), encoding="utf-8"
    )

    # 5. Dummy STEP File
    step_file = workspace_dir / "geometry.step"
    step_file.write_text(
        "ISO-10303-21 HEADER; ENDSEC; DATA; ENDSEC; END-ISO-10303-21;"
    )

    # 6. Valid Input JSON
    valid_input = dummy_in().override(
        step_file_path=str(step_file),
        boundary_condition_mapping=[
            {"location": "x_min", "type": "inflow", "values": {"u": 1.0, "v": 0.0, "w": 0.0}}
        ],
    )
    input_json_path = workspace_dir / "input_contract.json"
    input_json_path.write_text(json.dumps(valid_input), encoding="utf-8")

    return {
        "root_dir": root_dir,
        "workspace_dir": workspace_dir,
        "config_file": config_dir / "config.json",
        "input_json": input_json_path,
        "step_file": step_file,
    }