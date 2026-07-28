import logging

# Set up dedicated logger for STEP rendering engine
logger = logging.getLogger("step_visualizer")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [STEP_RENDERER] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)

# Global Mode Toggle: Set to True for detailed geometry debugging, False for Production
DEBUG_MODE: bool = True


def set_debug_mode(enabled: bool = True) -> None:
    """Dynamically toggles Debug Mode (verbose geometry logs) and Production Mode (sanitized logs)."""
    global DEBUG_MODE
    DEBUG_MODE = enabled
    logger.setLevel(logging.DEBUG if enabled else logging.INFO)


set_debug_mode(DEBUG_MODE)

# Color palette for Raw STEP Geometry Preview
CAD_COLOR_MAP = {
    "x_min": "#4A6572",
    "x_max": "#4A6572",
    "y_min": "#4A6572",
    "y_max": "#4A6572",
    "z_min": "#4A6572",
    "z_max": "#4A6572",
    "wall":  "#2C3E50",
}

# Color palette for Spatial Location Map (Model 1)
SPATIAL_COLOR_MAP = {
    "x_min": "#FF0000",
    "x_max": "#0066FF",
    "y_min": "#00CC44",
    "y_max": "#800080",
    "z_min": "#FF9900",
    "z_max": "#FF00AA",
    "wall":  "#2C3E50",
}

# Color palette for Physical Boundary Map (Model 2)
PHYSICAL_COLOR_MAP = {
    "inflow":    "#0000FF",
    "outflow":   "#FF0000",
    "no-slip":   "#708090",
    "free-slip": "#3CB371",
    "pressure":  "#800080",
}
