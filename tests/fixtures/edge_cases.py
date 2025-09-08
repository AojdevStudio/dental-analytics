# Edge case test data fixtures


import numpy as np
import pandas as pd


def get_edge_case_data() -> dict[str, pd.DataFrame]:
    """Generate edge case test data."""
    return {
        "zero_values": pd.DataFrame(
            {
                "total_production": [0, 0, 0],
                "total_collections": [0, 0, 0],
                "new_patients": [0, 0, 0],
            }
        ),
        "negative_values": pd.DataFrame(
            {"total_production": [-100, 200, -50], "total_collections": [100, -200, 50]}
        ),
        "very_large_values": pd.DataFrame(
            {
                "total_production": [1e10, 1e11, 1e12],
                "total_collections": [9e9, 9e10, 9e11],
            }
        ),
        "mixed_types": pd.DataFrame(
            {
                "total_production": ["1000", 2000, "3000.50"],
                "total_collections": [900, "1800", "2700.25"],
            }
        ),
        "with_nulls": pd.DataFrame(
            {
                "total_production": [1000, None, 3000, np.nan],
                "total_collections": [None, 1800, np.nan, 2500],
                "new_patients": [3, np.nan, None, 2],
            }
        ),
    }
