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
