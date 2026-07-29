from pathlib import Path

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")

from src.utils.renderer.config import (
    CAD_COLOR_MAP,
    DEBUG_MODE,
    PHYSICAL_COLOR_MAP,
    SPATIAL_COLOR_MAP,
    logger,
)
from src.utils.renderer.primitives import (
    draw_domain_geometry,
    get_face_centroid,
)


def render_step_snapshot(
    output_path: Path, 
    bounds: tuple[float, ...], 
    step_file_path: Path | str | None = None
) -> None:
    """Renders raw STEP geometry preview matching the exact 3D orientation of the pipeline maps."""
    if DEBUG_MODE:
        logger.debug("Rendering STEP Snapshot -> output_path='%s', bounds=%s", output_path, bounds)
    else:
        logger.info("Rendering STEP Snapshot to %s", output_path.name)

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    draw_domain_geometry(ax, bounds, face_color_dict=CAD_COLOR_MAP, step_file_path=step_file_path)

    ax.set_title("3D Visual QA - Raw STEP Geometry", fontsize=12, fontweight="bold")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")

    legend_patches = [mpatches.Patch(color="#4A6572", label="Raw CAD Geometry")]
    ax.legend(
        handles=legend_patches,
        title="Input Model",
        loc="center left",
        bbox_to_anchor=(1.05, 0.5),
        fontsize=9,
        title_fontsize=10,
        frameon=True
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Successfully exported STEP Snapshot image.")


def render_spatial_location_map(
    output_path: Path, 
    bounds: tuple[float, ...], 
    step_file_path: Path | str | None = None
) -> None:
    """Renders Spatial Location Map with alternating multi-color 'shtrih' shared edges and low-alpha fill (Model 1)."""
    if DEBUG_MODE:
        logger.debug("Rendering Spatial Location Map -> output_path='%s', bounds=%s", output_path, bounds)
    else:
        logger.info("Rendering Spatial Location Map to %s", output_path.name)

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    draw_domain_geometry(ax, bounds, face_color_dict=SPATIAL_COLOR_MAP, step_file_path=step_file_path)

    ax.set_title("3D Visual QA - Spatial Location Map", fontsize=12, fontweight="bold")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")

    legend_patches = [
        mpatches.Patch(color=color, label=f"{loc}")
        for loc, color in SPATIAL_COLOR_MAP.items()
    ]
    ax.legend(
        handles=legend_patches,
        title="Spatial Location",
        loc="center left",
        bbox_to_anchor=(1.05, 0.5),
        fontsize=9,
        title_fontsize=10,
        frameon=True
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Successfully exported Spatial Location Map image.")


def render_physical_boundary_map(
    output_path: Path,
    bounds: tuple[float, ...],
    location_to_type: dict[str, str],
    location_to_values: dict[str, dict[str, float]],
    step_file_path: Path | str | None = None
) -> None:
    """
    Renders Physical Boundary Map with dynamic velocity vectors & legend (Model 2).
    Strict No-Default Policy: raises immediate KeyError on missing boundary locations, unknown types, or missing velocity values.
    """
    if DEBUG_MODE:
        logger.debug("Rendering Physical Boundary Map -> output_path='%s'", output_path)
        logger.debug("Location to Type map: %s", location_to_type)
        logger.debug("Location to Values map: %s", location_to_values)
    else:
        logger.info("Rendering Physical Boundary Map to %s", output_path.name)

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    required_locations = ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "wall"]
    face_colors = {}
    for loc in required_locations:
        if loc not in location_to_type:
            logger.error("CONSTITUTION VIOLATION: Missing boundary type for '%s'", loc)
            raise KeyError(
                f"CONSTITUTION VIOLATION: Missing boundary type definition for location '{loc}'. Execution halted."
            )
        btype = location_to_type[loc]
        if btype not in PHYSICAL_COLOR_MAP:
            logger.error("CONSTITUTION VIOLATION: Unknown boundary type '%s' for '%s'", btype, loc)
            raise KeyError(
                f"CONSTITUTION VIOLATION: Unknown boundary type '{btype}' for location '{loc}'. Execution halted."
            )
        face_colors[loc] = PHYSICAL_COLOR_MAP[btype]

    draw_domain_geometry(ax, bounds, face_color_dict=face_colors, step_file_path=step_file_path)

    # Dynamic 3D velocity vector overlay for inflow
    for loc, btype in location_to_type.items():
        if btype == "inflow" and loc in location_to_values:
            vals = location_to_values[loc]
            if "u" not in vals or "v" not in vals or "w" not in vals:
                logger.error("CONSTITUTION VIOLATION: Missing velocity vector components at '%s'", loc)
                raise KeyError(
                    f"CONSTITUTION VIOLATION: Inflow boundary condition at '{loc}' missing required velocity components (u, v, w). Execution halted."
                )

            u = vals["u"]
            v = vals["v"]
            w = vals["w"]

            cx, cy, cz = get_face_centroid(loc, bounds)
            vel_mag = np.sqrt(u**2 + v**2 + w**2)
            scale = 400.0 if vel_mag > 0 else 1.0

            if DEBUG_MODE:
                logger.debug("Overlaying inflow quiver vector at centroid (%f, %f, %f) with magnitude %f", cx, cy, cz, vel_mag)

            ax.quiver(
                cx, cy, cz,
                u * scale, v * scale, w * scale,
                color="#0000FF", linewidth=3.0, arrow_length_ratio=0.35, zorder=6
            )

    ax.set_title("3D Visual QA - Physical Boundary Map", fontsize=12, fontweight="bold")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")

    legend_patches = [
        mpatches.Patch(color=color, label=f"{btype}")
        for btype, color in PHYSICAL_COLOR_MAP.items()
    ]
    ax.legend(
        handles=legend_patches,
        title="Boundary Condition Type",
        loc="center left",
        bbox_to_anchor=(1.05, 0.5),
        fontsize=9,
        title_fontsize=10,
        frameon=True
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Successfully exported Physical Boundary Map image.")
