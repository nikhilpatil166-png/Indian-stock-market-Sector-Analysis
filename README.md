# Indian Stock Market Sector Analysis

A Streamlit dashboard for comparing NSE sector indices with the NIFTY 50 benchmark. The first milestone supports daily, 5-minute, and 15-minute views, sector-relative strength, moving-average trend context, and a configurable market-data adapter.

> **Status:** First working dashboard milestone. The default provider is Yahoo Finance through the community-maintained `yfinance` library. It is a prototype data source, not an official NSE feed or a guaranteed real-time feed.

## Dashboard capabilities

- Daily, 5-minute, and 15-minute index history.
- NIFTY 50 benchmark overview.
- Sector returns over 1/5/20 observations.
- Relative strength versus NIFTY 50, expressed in percentage points.
- 20-period and 50-period moving-average status.
- Sector ranking and an index close/average chart.
- Per-symbol provider warnings when an index history is unavailable.
- Unit tests for the analysis calculations and GitHub Actions CI.

For daily data, the 1/5/20 observations represent 1 day, 1 week, and roughly 1 month of trading sessions. For intraday data, they mean 1/5/20 candles, not days.

## Supported sector universe

The initial configuration includes NIFTY Auto, Bank, Energy, Financial Services, FMCG, IT, Media, Metal, Pharma, PSU Bank, Realty, and Infrastructure. The NIFTY 50 (`^NSEI`) is the benchmark.

Symbols are configured in `src/config.py`. Market-data vendors sometimes rename, remove, or fail to serve individual index symbols. The dashboard reports missing symbols rather than treating a missing value as zero.

## Technology

- Python 3.10+
- Streamlit
- Pandas and NumPy
- Plotly
- yfinance (Yahoo Finance chart data)
- Pytest and GitHub Actions

## Run locally

### 1. Clone the repository

```bash
git clone https://github.com/nikhilpatil166-png/Indian-stock-market-Sector-Analysis.git
cd Indian-stock-market-Sector-Analysis
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the dashboard

```bash
streamlit run app.py
```

Streamlit prints a local URL, usually `http://localhost:8501`.

### 5. Run the tests

```bash
pytest -q
```

## Data-provider notes

The provider implementation lives in `src/data/yahoo_provider.py`. Analysis logic is deliberately separated in `src/analysis/metrics.py`, so a different provider can be added without rewriting the dashboard calculations.

The yfinance project states that it is not affiliated with, endorsed by, or vetted by Yahoo, and that Yahoo Finance API access is intended for personal use. Read the [yfinance documentation and disclaimer](https://ranaroussi.github.io/yfinance/) and applicable Yahoo terms before using downloaded data.

The yfinance reference documents intraday intervals such as 5m and 15m and notes that intraday data cannot extend beyond the most recent 60 days. This prototype requests only the latest 5 days for intraday views. Data may be delayed, incomplete, unavailable, or rate-limited.

For dependable production or trading use, replace this prototype provider with a licensed market-data service or your broker's documented market-data API. Do not scrape exchange websites or assume a public endpoint provides an execution-grade feed.

## Security

- No API key is required by the current prototype provider.
- Never commit broker access tokens, API keys, passwords, cookies, or `.env` files.
- Keep future provider credentials in environment variables or Streamlit secrets.
- Do not add order placement or automated trading to this dashboard without a separate security and risk-control design.

## Calculation definitions

- **Return:** percentage change between the latest close and the close N observations earlier.
- **Relative strength:** sector return minus NIFTY 50 return over the same observations. A positive result means the sector outperformed the benchmark over that window; it does not predict future returns.
- **Trend context:** latest close above or below its 20-period and 50-period simple moving averages.

The first milestone does not yet calculate constituent breadth, sector-weighted stock contribution, institutional flows, or buy/sell signals.

## Roadmap

1. **Foundation (this milestone):** data adapter, daily/intraday dashboard, relative strength, moving averages, tests, CI.
2. **Data quality:** verify all index symbols and timestamps against a selected licensed provider; add retries and caching.
3. **Sector breadth:** constituent lists, advancing/declining participation, and leading/lagging stocks.
4. **Sector rotation:** multi-week strength/momentum quadrants and historical rotation trails.
5. **Intraday research:** opening range, VWAP context, and 5/15-minute strength filters after feed reliability is established.
6. **Alerts:** configurable notifications after metrics have been validated.

## Disclaimer

This project is for research and educational purposes. It is not investment advice, does not guarantee real-time prices, and must not be used as the sole basis for trading decisions. Verify all prices and signals with an appropriate, licensed source.
