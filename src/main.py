import argparse
import json
import logging
import multiprocessing
import os
import sys

from jsonschema import ValidationError, validate

# --- BOOTSTRAP ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.state.mesh_generator_state import SovereignContainer
from src.steps.categorization import CategorizationStep
from src.steps.resolution import ResolutionStep
from src.steps.tracing import TracingStep
from src.steps.voxelization import VoxelizationStep
from src.utils.mask_visualizer import generate_mask_snapshot

from src.pipeline.orchestrator import Orchestrator
from src.steps.ingestion import IngestionStep

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("mesh_generator")


def validate_json(data, schema_path):
    """Validates input or output payload data against a JSON schema file."""
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
        return
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    try:
        validate(instance=data, schema=schema)
        logger.info(f"Schema validation passed: {schema_path}")
    except ValidationError as e:
        logger.error(f"SCHEMA VIOLATION: {schema_path}")
        raise e


def main():
    parser = argparse.ArgumentParser(description="Modular Workspace Mesh Generator")
    parser.add_argument("--input_output_folder", required=True, help="Path to workspace directory")
    parser.add_argument("--input_file_name", required=True, help="Name or relative path of the input STEP file")
    parser.add_argument("--output_file_name", required=True, help="Name or relative path of the output JSON file")
    args = parser.parse_args()

    workspace = os.path.abspath(args.input_output_folder)
    logger.info(f"Pipeline initialized. Workspace: {workspace}")

    # 1. Resolve and Validate Input STEP File Location Explicitly
    if os.path.isabs(args.input_file_name):
        step_file = args.input_file_name
    else:
        step_file = os.path.join(workspace, args.input_file_name)

    if not os.path.isfile(step_file):
        error_msg = f"CONSTITUTION VIOLATION: STEP file not found at location: {os.path.abspath(step_file)}"
        logger.critical(error_msg)
        raise FileNotFoundError(error_msg)

    # Resolve Explicit Output Target Path Structure
    if os.path.isabs(args.output_file_name):
        output_path = args.output_file_name
    else:
        output_path = os.path.join(workspace, args.output_file_name)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # 2. Load and Validate Config
    config_path = os.path.join("config", "config.json")
    if not os.path.exists(config_path):
        config_path = "config.json"
    
    if not os.path.exists(config_path):
        error_msg = f"CONSTITUTION VIOLATION: Configuration file not found at {config_path}."
        logger.critical(error_msg)
        raise FileNotFoundError(error_msg)

    with open(config_path, 'r') as f:
        config = json.load(f)
    
    validate_json(config, os.path.join("schema", "mesh_generator_config_schema.json"))

    # 3. Initialize SovereignContainer (Gmsh Dedicated Engine)
    container = SovereignContainer(
        step_file=step_file,
        max_element_size=config['max_element_size'],
        tolerance=config['tolerance'],
        min_element_size=config['min_element_size'],
        boundary_map=config['boundary_map']
    )

    logger.info("Starting pipeline execution with Gmsh engine.")

    # --- GMSH PARALLELIZATION & TOPOLOGY REMEDIATION LAYER ---
    import gmsh

    if not gmsh.is_initialized():
        logger.info("Initializing Gmsh runtime engine context...")
        gmsh.initialize()
    else:
        logger.warning("Gmsh engine already active in global state context. Skipping initialization.")

    cores = multiprocessing.cpu_count()
    logger.info(f"Commanding hardware allocation: Parallel tracking across {cores} threads.")
    gmsh.option.setNumber("General.NumThreads", cores)
    gmsh.option.setNumber("Mesh.Algorithm3D", 10)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthExtendFromBoundary", 1)
    gmsh.option.setNumber("Geometry.Tolerance", config['tolerance'])
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", config['max_element_size'])
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", config['min_element_size'])

    try:
        # 4. Orchestrate Pipeline Execution
        pipeline = Orchestrator([
            IngestionStep(),
            TracingStep(),
            ResolutionStep(),
            CategorizationStep(),
            VoxelizationStep()
        ])
        pipeline.run(container)

        # 5. Serialize Output Payload (Strictly conforming to schema with additionalProperties: false)
        output_data = {
            "inputs": {
                "step_model": {
                    "path": container.step_file
                }
            },
            "config": {
                "tolerance": container.tolerance,
                "max_element_size": container.max_element_size,
                "min_element_size": container.min_element_size
            },
            "results": {
                "grid": {
                    "x_min": container.grid.x_min, "x_max": container.grid.x_max,
                    "y_min": container.grid.y_min, "y_max": container.grid.y_max,
                    "z_min": container.grid.z_min, "z_max": container.grid.z_max,
                    "nx": container.grid.nx, "ny": container.grid.ny, "nz": container.grid.nz
                } if container.grid else None,
                "mask": container.mask if container.mask is not None else []
            }
        }

        # --- VISUAL MASK VERIFICATION GATE ---
        try:
            generate_mask_snapshot(output_data, fallback_save_dir=workspace)
        except Exception as viz_err:
            logger.error(f"Voxel verification snapshot engine faulted: {viz_err!s}")

        # --- SERIALIZATION LAYER ---
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Results serialized to: {output_path}")

        # Validate serialized payload against output schema
        validate_json(output_data, os.path.join("schema", "mesh_generator_output_schema.json"))

    finally:
        try:
            import gmsh
            if gmsh.is_initialized():
                logger.info("Executing final environment cleanup. Purging Gmsh memory structures...")
                gmsh.finalize()
            else:
                logger.warning("Gmsh finalization bypassed: Engine was already uninitialized by an internal pipeline step.")
        except ImportError:
            pass


if __name__ == "__main__":  # pragma: no cover
    main()