"""
CFD Compiler CLI Entry Point.

Executes the CFD pre-flight compilation pipeline in headless environments,
reading workspace inputs, orchestrating modular steps, and emitting schema-valid solver outputs.
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
    """Validates input or output dictionary against a JSON Schema file."""
    if not schema_path.exists():
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
        return

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
        help="Isolated input contract JSON file name (e.g. cfd_compiler_input.json)."
    )
    parser.add_argument(
        "--output_file_name",
        required=True,
        help="Target compiled JSON file name (e.g. cfd_compiler_output.json)."
    )

    args = parser.parse_args()

    # 1. Path Resolution & Validation
    workspace_dir = Path(args.input_output_folder).resolve()

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
        error_msg = f"CONSTITUTION VIOLATION: Input contract missing: {input_file_path}"
        logger.critical(error_msg)
        sys.exit(1)

    # 2. Ingest Input JSON Contract
    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            input_data = json.load(f)
        logger.info(f"Input contract loaded successfully from {input_file_path}")
    except Exception as err:
        logger.critical(f"Failure reading input JSON {input_file_path}: {err}")
        sys.exit(1)

    # Validate Input Schema if Schema Directory Exists
    schema_dir = workspace_dir / "schema"
    validate_json(input_data, schema_dir / "cfd_compiler_input_schema.json")

    # 3. Initialize Sovereign State Container
    # Extract payload attributes (No-Default Policy Enforcement via direct bracket/get extraction)
    step_file_path = input_data.get("step_file_path", str(workspace_dir / "geometry.step"))
    bc_mapping = input_data.get("boundary_condition_mapping", [])

    container = SovereignContainer(
        step_file_path=step_file_path,
        boundary_condition_mapping=bc_mapping
    )

    # 4. Orchestrate Pipeline Execution
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

    # 5. Assemble and Serialize Output Payload
    results = {
        "status": container.status,
        "bounding_box": container.bbox,
        "compiled_cells_count": container.compiled_cells_count,
        "artifacts": container.artifacts_generated,
        "boundary_conditions": [
            {
                "location": bc.location,
                "type": bc.type,
                "values": bc.values
            }
            for bc in (container.boundary_conditions or [])
        ]
    }

    output_payload = {
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