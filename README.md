# Indian Stock Market Sector Analysis

A data-driven project to study Indian stock-market sectors, compare their strength against the NIFTY 50, and identify which sectors are leading, weakening, or moving sideways.

> **Project status:** Initial setup. The first version will focus on reliable daily sector analysis. Intraday analysis and alerts can be added after the core calculations are tested.

## What this project should answer

- Which NSE sectors are outperforming or underperforming the NIFTY 50?
- Which sectors have the strongest trend and momentum?
- Is a sector's move supported by participation across its constituent stocks?
- Which stocks are leading or dragging each sector?
- Is sector strength improving, fading, or changing direction?

## First version (MVP)

The first working version should provide:

1. **Market overview** — NIFTY 50 and available NSE sector indices.
2. **Sector performance** — daily, weekly, and monthly percentage change.
3. **Relative strength** — each sector's performance compared with NIFTY 50.
4. **Trend view** — price versus 20-day and 50-day moving averages.
5. **Sector ranking** — leaders, improving sectors, weak sectors, and laggards.
6. **Constituent breadth** — advancing versus declining stocks, where constituent data is available.
7. **Charts and tables** — simple visual summaries with the data timestamp and source shown.

Intraday 5-minute/15-minute analysis, alerts, and broker integration are later milestones, not part of the first version.

## Suggested technology

- **Python** for calculations and data processing.
- **Pandas / NumPy** for market data and indicators.
- **Streamlit** for a simple interactive dashboard.
- **Plotly** for charts.
- **Pytest** for testing calculations.

Keep market-data collection separate from analysis. This makes it possible to change data providers without rewriting the sector-strength calculations.

## Data approach

Start with CSV files that can be downloaded or exported from a legitimate data source. This lets us validate the calculations before depending on a live feed.

Later, connect a documented and permitted market-data API. Record the source, exchange, interval, and last-updated time for every dataset. Do not commit API keys, broker credentials, cookies, or other secrets to GitHub.

## Proposed project structure

```text
Indian-stock-market-Sector-Analysis/
├── app.py                  # Streamlit dashboard entry point
├── requirements.txt        # Python dependencies
├── README.md
├── data/
│   └── sample/             # Small, non-sensitive sample datasets
├── src/
│   ├── data/
│   │   └── loader.py       # Load and validate market data
│   ├── analysis/
│   │   ├── performance.py  # Returns and relative strength
│   │   ├── trend.py        # Moving averages and trend state
│   │   └── breadth.py      # Advancers / decliners
│   └── config.py           # Sector and benchmark configuration
└── tests/
    ├── test_performance.py
    └── test_trend.py
```

## Build roadmap

### Phase 1 — Foundation
- Set up the Python project and dependencies.
- Decide the initial list of NSE sector indices and benchmark.
- Define a consistent CSV format and validate dates, symbols, and missing values.

### Phase 2 — Core analysis
- Calculate 1-day, 5-day, and 20-day returns.
- Calculate relative strength versus NIFTY 50.
- Add 20-day and 50-day moving-average trend states.
- Rank sectors and test the calculations on known sample data.

### Phase 3 — Dashboard
- Add sector ranking tables and performance charts.
- Show leading and lagging sectors.
- Display data source and last-updated timestamp.

### Phase 4 — Breadth and intraday
- Add constituent-level breadth and sector leaders/laggards.
- Add 5-minute and 15-minute views only when reliable intraday data is available.
- Consider notifications after the analysis has been validated.

## Initial analysis rules (to be tested, not treated as trading signals)

- **Relative strength:** sector return minus NIFTY 50 return over the same period.
- **Positive trend:** close above the selected moving averages.
- **Improving sector:** relative strength is rising across consecutive observations.
- **Breadth confirmation:** a larger share of constituent stocks is advancing.

These are analytical measures, not guaranteed buy/sell signals. Any trading use needs independent validation, risk management, and testing across different market conditions.

## Run locally (after the application files are added)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Important

This project is for market research and educational analysis. Market data can be delayed, incomplete, revised, or unavailable. It is not investment advice and should not place trades automatically.
