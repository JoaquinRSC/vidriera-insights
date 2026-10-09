import numpy as np
import pandas as pd

from vidriera_insights import export


def test_km_grid_covers_typical_mileage_in_10k_steps():
    grid = export.km_grid(pd.Series([10_000, 50_000, 90_000, 120_000]))
    assert grid[0] == 0 and grid[1] == 10_000
    assert 120_000 <= grid[-1] <= 300_000
    assert export.km_grid(pd.Series([5_000.0]))[-1] == 60_000  # never shorter than 60k km


def test_to_matrix_rounds_usd_and_reshapes():
    log_prices = np.log(np.array([10_004.0, 10_996.0, 20_001.0, 21_049.0]))
    assert export.to_matrix(log_prices, (2, 2)) == [[10_000, 11_000], [20_000, 21_050]]


def test_mode_or_unknown():
    assert export.mode_or_unknown(pd.Series(["Nafta", "Nafta", None, "Diésel"])) == "Nafta"
    assert export.mode_or_unknown(pd.Series([None, None])) == "unknown"
