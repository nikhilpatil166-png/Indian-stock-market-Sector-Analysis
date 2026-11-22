"""Streamlit dashboard for Indian NSE sector analysis."""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analysis.metrics import build_sector_table
from src.config import (
    BENCHMARK_NAME,
    BENCHMARK_SYMBOL,
    INTERVALS,
    SECTORS,
)
from src.data.angel_one.auth import AngelOneAuthError, AngelOneSmartAPI
from src.data.yahoo_provider import fetch_market_data


def _secret(name: str) -> str:
    """Read a secret from environment variables or local Streamlit secrets."""
    value = os.getenv(name)
    if value:
        return value.strip()
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value).strip() if value else ""


def _masked_client_code(client_code: str) -> str:
    if len(client_code) <= 4:
        return "*" * len(client_code)
    return f"{client_code[:2]}{'*' * (len(client_code) - 4)}{client_code[-2:]}"


st.set_page_config(
    page_title="Indian Sector Analysis",
    page_icon="📊",
    layout="wide",
)

st.title("🇮🇳 Indian Stock Market — Sector Analysis")
st.caption(
    "Daily and intraday sector strength dashboard · NSE indices · "
    "Research tool, not a trading signal"
)

with st.sidebar:
    st.header("Dashboard controls")
    interval_label = st.selectbox("Market timeframe", list(INTERVALS.keys()))
    interval = INTERVALS[interval_label]
    st.caption(
        "Daily view compares 1, 5 and 20 sessions. "
        "Intraday view compares 1, 5 and 20 candles."
    )
    if st.button("↻ Refresh market data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.subheader("Angel One SmartAPI")

    api_key = _secret("ANGELONE_API_KEY")
    client_code = _secret("ANGELONE_CLIENT_CODE")
    pin = _secret("ANGELONE_PIN")
    public_ip = _secret("ANGELONE_CLIENT_PUBLIC_IP") or None
    credentials_ready = bool(api_key and client_code and pin)

    if not credentials_ready:
        st.warning(
            "Local SmartAPI credentials are not configured. Copy "
            ".streamlit/secrets.toml.example to "
            ".streamlit/secrets.toml and fill it on this computer."
        )

    active_client = st.session_state.get("angel_one_client")
    if active_client is not None and active_client.is_authenticated:
        st.success(
            f"Connected · {_masked_client_code(client_code or 'account')}"
        )
        if st.button("Disconnect Angel One", use_container_width=True):
            try:
                active_client.logout()
            except AngelOneAuthError as exc:
                st.warning(str(exc))
            finally:
                st.session_state.pop("angel_one_client", None)
                st.rerun()
    elif credentials_ready:
        with st.form("angel_one_login", clear_on_submit=True):
            totp = st.text_input(
                "Current 6-digit TOTP",
                type="password",
                max_chars=6,
                help="Enter the current code from your authenticator app.",
            )
            submitted = st.form_submit_button(
                "Connect to Angel One",
                use_container_width=True,
            )
        if submitted:
            try:
                client = AngelOneSmartAPI(
                    api_key,
                    client_code,
                    public_ip=public_ip,
                )
                profile = client.login(pin, totp)
                profile_data = profile.get("data") or {}
                verified_code = str(profile_data.get("clientcode") or client_code)
                st.session_state["angel_one_client"] = client
                st.session_state["angel_one_verified_account"] = _masked_client_code(
                    verified_code
                )
                st.success(
                    "SmartAPI login and protected profile check succeeded. "
                    f"Account: {_masked_client_code(verified_code)}"
                )
                st.rerun()
            except AngelOneAuthError as exc:
                st.error(str(exc))
            except Exception:
                # Do not show arbitrary exception details, which could contain
                # request metadata or provider response material.
                st.error(
                    "Angel One connection failed unexpectedly. "
                    "Check local configuration and retry."
                )

    st.divider()
    st.markdown("**Market-data provider**")
    st.write("Yahoo Finance prototype")
    st.caption(
        "SmartAPI authentication is now separate from market-data loading. "
        "Angel One historical candles and live streaming are the next integration steps."
    )
    st.write(f"Benchmark: {BENCHMARK_NAME}")
    st.write(f"Configured sectors: {len(SECTORS)}")


@st.cache_data(ttl=60, show_spinner=False)
def load_market_data(selected_interval: str):
    return fetch_market_data(selected_interval)


with st.spinner(f"Fetching {interval_label.lower()} market data..."):
    histories, errors, fetched_at = load_market_data(interval)

if BENCHMARK_SYMBOL not in histories:
    st.error(
        "The NIFTY 50 benchmark could not be loaded. "
        "The data provider may be unavailable or rate-limiting requests."
    )
    if errors:
        with st.expander("Provider diagnostics"):
            st.json(errors)
    st.stop()

sector_table = build_sector_table(histories)
if sector_table.empty:
    st.error("No sector index histories were returned. Try refreshing later.")
    if errors:
        with st.expander("Provider diagnostics"):
            st.json(errors)
    st.stop()

benchmark = histories[BENCHMARK_SYMBOL]
benchmark_close = pd.to_numeric(benchmark["Close"], errors="coerce").dropna()
benchmark_last = float(benchmark_close.iloc[-1])
benchmark_change = (
    (benchmark_close.iloc[-1] / benchmark_close.iloc[-2] - 1) * 100
    if len(benchmark_close) >= 2 and benchmark_close.iloc[-2] != 0
    else float("nan")
)

is_daily = interval == "1d"
short_label, medium_label, long_label = (
    ("1D", "1W", "1M") if is_daily else ("1 bar", "5 bars", "20 bars")
)
primary_relative_column = "relative_5"
best_sector = sector_table.iloc[0]
worst_sector = sector_table.sort_values(
    primary_relative_column, ascending=True, na_position="last"
).iloc[0]

st.caption(
    f"Fetched at {fetched_at} (Asia/Kolkata). "
    f"Latest available benchmark bar: {benchmark.index[-1]}. "
    "This timestamp is the fetch time, not an exchange-certified live timestamp."
)

metric_cols = st.columns(4)
metric_cols[0].metric(
    f"{BENCHMARK_NAME} last",
    f"{benchmark_last:,.2f}",
    f"{benchmark_change:+.2f}%" if pd.notna(benchmark_change) else None,
)
metric_cols[1].metric(
    "Sectors loaded",
    f"{len(sector_table)} / {len(SECTORS)}",
)
metric_cols[2].metric(
    "Relative-strength leader",
    best_sector["sector"],
    f"{best_sector[primary_relative_column]:+.2f} pp"
    if pd.notna(best_sector[primary_relative_column]) else None,
)
metric_cols[3].metric(
    "Relative-strength laggard",
    worst_sector["sector"],
    f"{worst_sector[primary_relative_column]:+.2f} pp"
    if pd.notna(worst_sector[primary_relative_column]) else None,
)

st.subheader("Sector performance and relative strength")
st.caption(
    "Relative strength is sector percentage return minus NIFTY 50 percentage "
    "return over the same number of observations. Values are percentage points (pp)."
)

display = sector_table[
    [
        "sector",
        "last",
        "return_1",
        "return_5",
        "return_20",
        "relative_1",
        "relative_5",
        "relative_20",
        "above_ma20",
        "above_ma50",
    ]
].copy()
display = display.rename(
    columns={
        "sector": "Sector",
        "last": "Last",
        "return_1": f"Return {short_label} (%)",
        "return_5": f"Return {medium_label} (%)",
        "return_20": f"Return {long_label} (%)",
        "relative_1": f"RS {short_label} (pp)",
        "relative_5": f"RS {medium_label} (pp)",
        "relative_20": f"RS {long_label} (pp)",
        "above_ma20": "Above 20 MA",
        "above_ma50": "Above 50 MA",
    }
)
display["Above 20 MA"] = display["Above 20 MA"].map(
    lambda value: "Above" if value is True else "Below" if value is False else "N/A"
)
display["Above 50 MA"] = display["Above 50 MA"].map(
    lambda value: "Above" if value is True else "Below" if value is False else "N/A"
)

st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Last": st.column_config.NumberColumn(format="%,.2f"),
        **{
            column: st.column_config.NumberColumn(format="%+.2f")
            for column in display.columns
            if "Return" in column or "RS " in column
        },
    },
)

chart_left, chart_right = st.columns([1.1, 1])
with chart_left:
    st.subheader(f"Relative-strength ranking ({medium_label})")
    ranking = sector_table.sort_values("relative_5", ascending=True)
    ranking_chart = px.bar(
        ranking,
        x="relative_5",
        y="sector",
        orientation="h",
        labels={
            "relative_5": "Relative strength vs NIFTY 50 (pp)",
            "sector": "",
        },
    )
    ranking_chart.add_vline(x=0, line_dash="dash", line_color="gray")
    ranking_chart.update_layout(
        height=500,
        margin=dict(l=10, r=10, t=20, b=20),
        yaxis={"categoryorder": "total ascending"},
    )
    st.plotly_chart(ranking_chart, use_container_width=True)

with chart_right:
    st.subheader("Sector trend")
    available_sectors = sector_table["sector"].tolist()
    selected_sector = st.selectbox("Choose a sector", available_sectors)
    selected_row = sector_table.loc[sector_table["sector"] == selected_sector].iloc[0]
    sector_history = histories[selected_row["symbol"]].copy()
    sector_history["MA 20"] = sector_history["Close"].rolling(20).mean()
    sector_history["MA 50"] = sector_history["Close"].rolling(50).mean()

    trend_chart = go.Figure()
    trend_chart.add_trace(
        go.Scatter(
            x=sector_history.index,
            y=sector_history["Close"],
            mode="lines",
            name="Close",
        )
    )
    trend_chart.add_trace(
        go.Scatter(
            x=sector_history.index,
            y=sector_history["MA 20"],
            mode="lines",
            name="MA 20",
        )
    )
    trend_chart.add_trace(
        go.Scatter(
            x=sector_history.index,
            y=sector_history["MA 50"],
            mode="lines",
            name="MA 50",
        )
    )
    trend_chart.update_layout(
        height=500,
        xaxis_title="Time",
        yaxis_title="Index value",
        margin=dict(l=10, r=10, t=20, b=20),
        legend=dict(orientation="h", y=1.08),
    )
    st.plotly_chart(trend_chart, use_container_width=True)

    state_20 = (
        "Above" if selected_row["above_ma20"] is True
        else "Below" if selected_row["above_ma20"] is False
        else "Not enough history"
    )
    state_50 = (
        "Above" if selected_row["above_ma50"] is True
        else "Below" if selected_row["above_ma50"] is False
        else "Not enough history"
    )
    st.write(f"**20-period moving average:** {state_20}")
    st.write(f"**50-period moving average:** {state_50}")

if errors:
    with st.expander(f"Data-provider warnings ({len(errors)})"):
        st.write(
            "Some symbols did not return data. This can happen when a Yahoo "
            "Finance symbol is unavailable, the provider is rate-limiting, or "
            "the market-data endpoint is temporarily unavailable."
        )
        st.json(errors)

st.divider()
st.caption(
    "Data limitations: this prototype uses Yahoo Finance data through the "
    "unofficial yfinance library. Intraday history is limited by the provider; "
    "the app requests the latest 5 days. A missing or delayed quote is possible. "
    "Verify prices with your broker or licensed market-data provider before "
    "making trading decisions."
)
