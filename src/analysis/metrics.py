"""Return, relative-strength, and moving-average calculations."""

import math

import pandas as pd

from src.config import BENCHMARK_SYMBOL, SECTORS


def percent_change(series: pd.Series, bars: int = 1) -> float:
    """Return percentage change over a number of completed observations.

    For intraday data, bars means candles, not trading days.
    """
    if bars < 1:
        raise ValueError("bars must be at least 1")

    values = pd.to_numeric(series, errors="coerce").dropna()
    if len(values) <= bars:
        return math.nan

    previous = float(values.iloc[-bars - 1])
    latest = float(values.iloc[-1])
    if previous == 0:
        return math.nan

    return (latest / previous - 1.0) * 100.0


def _close_series(history: pd.DataFrame) -> pd.Series:
    if history is None or history.empty or "Close" not in history.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(history["Close"], errors="coerce").dropna()


def build_sector_table(
    histories: dict,
    sectors: dict | None = None,
    benchmark_symbol: str = BENCHMARK_SYMBOL,
) -> pd.DataFrame:
    """Build a sector table with returns, benchmark-relative strength and trend."""
    sectors = sectors or SECTORS
    benchmark_close = _close_series(histories.get(benchmark_symbol))

    benchmark_returns = {
        bars: percent_change(benchmark_close, bars)
        for bars in (1, 5, 20)
    }

    rows = []
    for sector_name, symbol in sectors.items():
        close = _close_series(histories.get(symbol))
        if close.empty:
            continue

        latest = float(close.iloc[-1])
        ma20 = float(close.tail(20).mean()) if len(close) >= 20 else math.nan
        ma50 = float(close.tail(50).mean()) if len(close) >= 50 else math.nan

        row = {
            "sector": sector_name,
            "symbol": symbol,
            "last": latest,
            "return_1": percent_change(close, 1),
            "return_5": percent_change(close, 5),
            "return_20": percent_change(close, 20),
            "ma20": ma20,
            "ma50": ma50,
            "above_ma20": latest > ma20 if not math.isnan(ma20) else None,
            "above_ma50": latest > ma50 if not math.isnan(ma50) else None,
        }

        for bars in (1, 5, 20):
            sector_return = row[f"return_{bars}"]
            benchmark_return = benchmark_returns[bars]
            row[f"relative_{bars}"] = (
                sector_return - benchmark_return
                if not math.isnan(sector_return)
                and not math.isnan(benchmark_return)
                else math.nan
            )

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values("relative_5", ascending=False, na_position="last")
        .reset_index(drop=True)
    )
