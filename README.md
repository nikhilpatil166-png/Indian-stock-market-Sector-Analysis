# Indian Stock Market Sector Analysis

A Streamlit dashboard for comparing NSE sector indices with the NIFTY 50 benchmark. The project is being developed in stages: sector analytics, broker-backed historical data, and eventually real-time intraday market updates.

> **Current status:** SmartAPI authentication and protected-profile verification are implemented on the feature branch. The dashboard's market-data display still uses the Yahoo Finance prototype until Angel One historical candles are integrated and tested.

## Current dashboard

- Daily, 5-minute, and 15-minute prototype views.
- NIFTY 50 benchmark overview.
- Sector returns over 1/5/20 observations.
- Relative strength versus NIFTY 50, expressed in percentage points.
- 20-period and 50-period moving-average status.
- Sector ranking and index close/average chart.

## Angel One SmartAPI authentication

The current feature branch adds:

- Login using API key, client code, PIN, and current 6-digit TOTP.
- Protected profile call to verify the session.
- In-memory JWT, refresh token, and feed token handling.
- Token-refresh method for later authenticated data calls.
- Explicit logout and local token clearing.
- No broker secrets, TOTP values, or session tokens in source control or application logs.
- TLS certificate verification enabled.

### Configure locally

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in your own API key, client code, and PIN. The real secrets file is excluded by `.gitignore`.

The current TOTP is entered in the Streamlit sidebar when connecting. The TOTP is not saved to disk. See [ANGEL_ONE_SETUP.md](ANGEL_ONE_SETUP.md) for instructions.

### Authentication scope

This is authentication and a connection test only. It does not place orders. The current Yahoo Finance prototype remains the dashboard's market-data source until the historical-candle adapter is implemented in the next milestone.

## Technology

- Python 3.10+
- Streamlit
- Pandas / NumPy
- Plotly
- yfinance (temporary prototype feed)
- requests (direct SmartAPI HTTPS client)
- Pytest and GitHub Actions

## Run locally

```bash
git clone https://github.com/nikhilpatil166-png/Indian-stock-market-Sector-Analysis.git
cd Indian-stock-market-Sector-Analysis
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Install and start:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Run tests:

```bash
pytest -q
```

## Data provider notes

The prototype provider is in `src/data/yahoo_provider.py`. It is not an official NSE feed or a guaranteed real-time source. Replace it with a licensed or broker-provided source for production or trading use.

The Angel One auth client is in `src/data/angel_one/auth.py`. Historical candle retrieval and WebSocket live streaming are planned follow-on integrations.

## Security

- Keep real credentials in local Streamlit secrets or environment variables.
- Never commit `.streamlit/secrets.toml`, API keys, PINs, TOTP seeds/codes, cookies, or access tokens.
- JWT, refresh, and feed tokens are held only in the running process memory.
- Do not add order placement or automated trading without a separate security and risk-control review.

## Roadmap

1. **Foundation:** dashboard, prototype provider, sector relative-strength calculations, tests.
2. **SmartAPI authentication:** secure login, protected profile test, in-memory token management.
3. **Historical market data:** instrument-master mapping and 1D/5m/15m candle retrieval from Angel One.
4. **Live market data:** WebSocket V2, tick normalization, 5-minute/15-minute candle builder.
5. **Sector intelligence:** breadth, leaders/laggards, relative-strength rotation.
6. **Intraday research:** VWAP, opening range, relative volume, and validated alerts.

## Disclaimer

This project is for research and educational purposes. It is not investment advice, does not guarantee real-time prices, and must not be used as the sole basis for trading decisions. Verify prices with your broker or licensed data provider.
