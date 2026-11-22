"""Yahoo Finance chart-data adapter via yfinance.

This adapter is intended for prototyping and personal research. It is not an
official NSE feed, does not guarantee real-time delivery, and may be rate-limited.
Replace this module with a licensed/broker data adapter before relying on the
dashboard for execution decisions.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

from src.config import (
    BENCHMARK_SYMBOL,
    DAILY_HISTORY_PERIOD,
    INTRADAY_HISTORY_PERIOD,
    SECTORS,
)

SUPPORTED_INTERVALS = {"1d", "5m", "15m"}


def _history_period(interval: str) -> str:
    """Return a conservative download window for the requested interval."""
    if interval == "1d":
        return DAILY_HISTORY_PERIOD
    return INTRADAY_HISTORY_PERIOD


def _fetch_one(symbol: str, interval: str) -> pd.DataFrame:
    """Fetch OHLCV history for one Yahoo Finance symbol."""
    history = yf.Ticker(symbol).history(
        period=_history_period(interval),
        interval=interval,
        auto_adjust=True,
        actions=False,
        prepost=False,
        timeout=20,
    )

    if history is None or history.empty or "Close" not in history.columns:
        raise ValueError("No price history returned for this symbol.")

    history = history.copy()
    history = history.dropna(subset=["Close"])
    if history.empty:
        raise ValueError("Price history contains no valid closing prices.")

    # Convert intraday timestamps to Indian market time for display.
    if getattr(history.index, "tz", None) is not None:
        history.index = history.index.tz_convert("Asia/Kolkata")

    return history


def fetch_market_data(interval: str = "1d"):
    """Fetch the benchmark and sector indices.

    Returns:
        tuple: (histories, errors, fetched_at)
        histories maps Yahoo symbols to OHLCV DataFrames.
        errors maps symbols that could not be fetched to readable messages.
    """
    if interval not in SUPPORTED_INTERVALS:
        raise ValueError(
            f"Unsupported interval {interval!r}. "
            f"Choose one of: {', '.join(sorted(SUPPORTED_INTERVALS))}."
        )

    symbols = [BENCHMARK_SYMBOL, *SECTORS.values()]
    histories = {}
    errors = {}

    max_workers = min(6, len(symbols))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_symbols = {
            executor.submit(_fetch_one, symbol, interval): symbol
            for symbol in symbols
        }
        for future in as_completed(future_symbols):
            symbol = future_symbols[future]
            try:
                histories[symbol] = future.result()
            except Exception as exc:
                errors[symbol] = f"{type(exc).__name__}: {exc}"

    fetched_at = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="seconds")
    return histories, errors, fetched_at
