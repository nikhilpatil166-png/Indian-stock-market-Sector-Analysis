"""Central configuration for benchmark, sectors, and supported intervals."""

BENCHMARK_NAME = "NIFTY 50"
BENCHMARK_SYMBOL = "^NSEI"

# Yahoo Finance symbols for commonly followed NSE sector indices.
# A missing symbol is reported in the dashboard rather than stopping all data loads.
SECTORS = {
    "NIFTY Auto": "^CNXAUTO",
    "NIFTY Bank": "^NSEBANK",
    "NIFTY Energy": "^CNXENERGY",
    "NIFTY Financial Services": "^CNXFINANCE",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY IT": "^CNXIT",
    "NIFTY Media": "^CNXMEDIA",
    "NIFTY Metal": "^CNXMETAL",
    "NIFTY Pharma": "^CNXPHARMA",
    "NIFTY PSU Bank": "^CNXPSUBANK",
    "NIFTY Realty": "^CNXREALTY",
    "NIFTY Infrastructure": "^CNXINFRA",
}

INTERVALS = {
    "Daily": "1d",
    "5-minute": "5m",
    "15-minute": "15m",
}

DAILY_HISTORY_PERIOD = "6mo"
INTRADAY_HISTORY_PERIOD = "5d"
