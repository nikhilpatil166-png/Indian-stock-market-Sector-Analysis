import math

import pandas as pd
import pytest

from src.analysis.metrics import build_sector_table, percent_change


def test_percent_change_uses_requested_number_of_bars():
    close = pd.Series([100.0, 102.0, 105.0])
    assert percent_change(close, bars=1) == pytest.approx(105 / 102 * 100 - 100)
    assert percent_change(close, bars=2) == pytest.approx(5.0)


def test_percent_change_returns_nan_when_history_is_too_short():
    assert math.isnan(percent_change(pd.Series([100.0]), bars=1))


def test_build_sector_table_calculates_relative_strength_and_trend():
    index = pd.date_range("2026-01-01", periods=55, freq="D")
    histories = {
        "BENCH": pd.DataFrame({"Close": [100.0 + i for i in range(55)]}, index=index),
        "SECTOR": pd.DataFrame({"Close": [100.0 + 2 * i for i in range(55)]}, index=index),
    }

    table = build_sector_table(
        histories,
        sectors={"Test sector": "SECTOR"},
        benchmark_symbol="BENCH",
    )

    assert len(table) == 1
    row = table.iloc[0]
    assert row["sector"] == "Test sector"
    assert row["relative_1"] > 0
    assert row["relative_5"] > 0
    assert bool(row["above_ma20"])
    assert bool(row["above_ma50"])


def test_build_sector_table_skips_missing_sector_data():
    histories = {
        "BENCH": pd.DataFrame({"Close": [100.0, 101.0, 102.0]}),
    }
    table = build_sector_table(
        histories,
        sectors={"Unavailable": "MISSING"},
        benchmark_symbol="BENCH",
    )
    assert table.empty
