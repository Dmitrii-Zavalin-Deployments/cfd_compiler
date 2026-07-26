"""
CFD Compiler CLI Entry Point.

Executes the CFD pre-flight compilation pipeline in headless environments,
reading configuration and workspace inputs, validating schemas, and emitting solver outputs.
Strictly enforces No-Default Policy across all user inputs and configuration parameters.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from jsonschema import ValidationError, validate

# --- BOOTSTRAP ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline.orchestrator import Orchestrator
from src.state.cfd_compiler_state import SovereignContainer
from src.steps.assembly import AssemblyStep
from src.steps.boundary_conditions import BoundaryConditionsStep
from src.steps.ingestion import IngestionStep
from src.steps.rendering import RenderingStep

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cfd_compiler")


def validate_json(data: dict, schema_path: Path) -> None:
    """Validates input, config, or output dictionary against a JSON Schema file."""
    if not schema_path.exists():
        error_msg = f"CONSTITUTION VIOLATION: Schema file not found at {schema_path}"
        logger.critical(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        validate(instance=data, schema=schema)
        logger.info(f"Schema validation passed: {schema_path}")
    except ValidationError as e:
        logger.error(f"SCHEMA VIOLATION: {schema_path}\n{e.message}")
        raise e


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CFD Compiler CLI - Modular Pre-Flight Gate"
    )
    parser.add_argument(
        "--input_output_folder",
        required=True,
        help="Path to working workspace directory containing inputs and targets."
    )
    parser.add_argument(
        "--input_file_name",
        required=True,
        help="Isolated input contract JSON file name or direct STEP file name."
    )
    parser.add_argument(
        "--output_file_name",
        required=True,
        help="Target compiled JSON file name (e.g. cfd_compiler_output.json)."
    )

    args = parser.parse_args()

    # 1. Path Resolution & Validation
    workspace_dir = Path(args.input_output_folder).resolve()
    root_dir = Path(__file__).resolve().parent.parent

    if os.path.isabs(args.input_file_name):
        input_file_path = Path(args.input_file_name)
    else:
        input_file_path = workspace_dir / args.input_file_name

    if os.path.isabs(args.output_file_name):
        output_file_path = Path(args.output_file_name)
    else:
        output_file_path = workspace_dir / args.output_file_name

    logger.info(f"CFD Compiler initialized. Workspace: {workspace_dir}")

    if not input_file_path.exists():
        error_msg = f"CONSTITUTION VIOLATION: Input file missing: {input_file_path}"
        logger.critical(error_msg)
        sys.exit(1)

    # 2. Load and Validate Configuration (`config/config.json`)
    config_path = root_dir / "config" / "config.json"
    config_schema_path = root_dir / "schema" / "cfd_compiler_config_schema.json"

    if not config_path.exists():
        error_msg = f"CONSTITUTION VIOLATION: Configuration file missing: {config_path}"
        logger.critical(error_msg)
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        logger.info(f"Configuration loaded successfully from {config_path}")
    except Exception as err:
        logger.critical(f"Failure reading configuration file {config_path}: {err}")
        sys.exit(1)

    validate_json(config_data, config_schema_path)

    # Strict No-Default Policy: Direct key extraction with immediate failure on missing parameters
    try:
        if "tolerance" not in config_data:
            raise KeyError("tolerance")
        if "max_element_size" not in config_data:
            raise KeyError("max_element_size")
        if "min_element_size" not in config_data:
            raise KeyError("min_element_size")
        if "boundary_condition_mapping" not in config_data:
            raise KeyError("boundary_condition_mapping")

        tolerance = config_data["tolerance"]
        max_element_size = config_data["max_element_size"]
        min_element_size = config_data["min_element_size"]
        config_bc_mapping = config_data["boundary_condition_mapping"]
    except KeyError as err:
        logger.critical(f"CONSTITUTION VIOLATION: Required configuration parameter missing in config.json: {err}")
        sys.exit(1)

    # 3. Ingest Input (Supports JSON Contract or Direct STEP file)
    schema_dir = root_dir / "schema"

    try:
        if input_file_path.suffix.lower() in [".step", ".stp"]:
            input_data = {
                "step_file_path": str(input_file_path),
                "boundary_condition_mapping": config_bc_mapping
            }
            logger.info("Detected direct STEP file input. Synthesized contract using config boundary conditions.")
        else:
            with open(input_file_path, "r", encoding="utf-8") as f:
                input_data = json.load(f)
            logger.info(f"Input contract loaded successfully from {input_file_path}")

            # Validate JSON contract against schema
            validate_json(input_data, schema_dir / "cfd_compiler_input_schema.json")

    except Exception as err:
        logger.critical(f"Failure processing input file {input_file_path}: {err}")
        sys.exit(1)

    # Strict No-Default Policy: Direct key extraction without fallback assignments
    try:
        if "step_file_path" not in input_data:
            raise KeyError(
                "CONSTITUTION VIOLATION: Missing required field 'step_file_path' in input payload. Execution halted."
            )
        if "boundary_condition_mapping" not in input_data:
            raise KeyError(
                "CONSTITUTION VIOLATION: Missing required field 'boundary_condition_mapping' in input payload. Execution halted."
            )

        step_file_path = input_data["step_file_path"]
        bc_mapping = input_data["boundary_condition_mapping"]
    except KeyError as err:
        logger.critical(f"{err}")
        sys.exit(1)

    # 4. Initialize Sovereign State Container with Config & Input Data
    container = SovereignContainer(
        step_file_path=step_file_path,
        boundary_condition_mapping=bc_mapping,
        tolerance=tolerance,
        max_element_size=max_element_size,
        min_element_size=min_element_size
    )

    # 5. Orchestrate Pipeline Execution
    logger.info("Executing CFD Pre-Flight Compilation Pipeline...")
    try:
        pipeline = Orchestrator([
            IngestionStep(),
            BoundaryConditionsStep(),
            RenderingStep(),
            AssemblyStep()
        ])
        pipeline.run(container)
    except Exception as err:
        logger.critical(f"Pipeline execution faulted: {err}")
        sys.exit(1)

    # 6. Assemble and Serialize Output Payload
    if container.boundary_conditions is None:
        logger.critical("CONSTITUTION VIOLATION: Boundary conditions state uninitialized post-execution.")
        sys.exit(1)

    results = {
        "status": container.status,
        "bounding_box": container.bounding_box,
        "compiled_cells_count": container.compiled_cells_count,
        "artifacts_generated": container.artifacts_generated,
        "boundary_conditions": [
            {
                "location": bc.location,
                "type": bc.type,
                "values": bc.values
            }
            for bc in container.boundary_conditions
        ]
    }

    output_payload = {
        "config": config_data,
        "input": input_data,
        "results": results
    }

    # Validate Output Schema
    validate_json(output_payload, schema_dir / "cfd_compiler_output_schema.json")

    # Write JSON Artifact
    try:
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)
        logger.info(f"✅ CFD Compiler executed successfully. Output written to: {output_file_path}")
    except Exception as err:
        logger.critical(f"Failure writing output JSON {output_file_path}: {err}")
        sys.exit(1)

    if container.status != "success":
        logger.error(f"Compilation finished with non-success status: {container.status}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()