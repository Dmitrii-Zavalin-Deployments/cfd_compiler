"""
CFD Compiler CLI Entry Point.

Executes the CFD pre-flight compilation pipeline in headless environments,
reading workspace inputs and emitting schema-valid solver outputs along with 3D diagnostic maps.
"""

import argparse
import json
import sys
from pathlib import Path
from cfd_compiler.cfd_compiler import solve


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CFD Compiler CLI - Deterministic Pre-Flight Gate"
    )
    parser.add_argument(
        "--input_output_folder",
        type=str,
        required=True,
        help="Path to working workspace directory containing inputs and targets."
    )
    parser.add_argument(
        "--input_file_name",
        type=str,
        required=True,
        help="Isolated input contract file name (e.g. cfd_compiler_input.json)."
    )
    parser.add_argument(
        "--output_file_name",
        type=str,
        required=True,
        help="Target compiled JSON file name (e.g. cfd_compiler_output.json)."
    )

    args = parser.parse_args()

    workspace_dir = Path(args.input_output_folder).resolve()
    input_file_path = workspace_dir / args.input_file_name
    output_file_path = workspace_dir / args.output_file_name

    if not input_file_path.exists():
        print(f"❌ Error: Input contract file standard missing: {input_file_path}", file=sys.stderr)
        sys.exit(1)

    # Ingest input JSON contract
    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            input_data = json.load(f)
    except Exception as err:
        print(f"❌ Failure reading input JSON {input_file_path}: {err}", file=sys.stderr)
        sys.exit(1)

    # Execute core compilation gate
    results = solve(input_data, workspace_dir=workspace_dir)

    # Assemble full outer payload conforming to cfd_compiler_output_schema.json
    output_payload = {
        "input": input_data,
        "results": results
    }

    # Write output contract
    try:
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)
        print(f"✅ CFD Compiler executed successfully. Compiled payload written to {output_file_path}")
    except Exception as err:
        print(f"❌ Failure writing output JSON {output_file_path}: {err}", file=sys.stderr)
        sys.exit(1)

    if results.get("status") == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()