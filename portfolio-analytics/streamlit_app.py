"""
Portfolio Analytics — Streamlit Dashboard
===========================================
Run: python -m streamlit run streamlit_app.py
"""

import streamlit as st
import numpy as np
import pandas as pd
import json
from portfolio import Portfolio

st.set_page_config(page_title="Portfolio Analytics", layout="wide", initial_sidebar_state="expanded")

# ─── Custom Styling ──────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    h1 { font-size: 1.8rem !important; font-weight: 700 !important; color: #1a1a2e !important; letter-spacing: -0.02em; }
    h2 { font-size: 1.3rem !important; font-weight: 600 !important; color: #1a1a2e !important; }
    h3 { font-size: 1.05rem !important; font-weight: 600 !important; color: #2d3748 !important; }
    [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.03em; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
    .stTabs [data-baseweb="tab"] { font-size: 0.85rem; font-weight: 500; padding: 0.5rem 1.2rem; }
</style>
""", unsafe_allow_html=True)

st.title("Portfolio Analytics")

# ─── Top Navigation ──────────────────────────────────────────
tab_overview, tab_performance, tab_risk, tab_allocation, tab_dividends, tab_manage = st.tabs([
    "Overview", "Performance", "Risk Analysis", "Allocation & Correlation", "Dividends", "Manage Portfolio"
])

# ─── Load Portfolio ──────────────────────────────────────────
if "portfolio" not in st.session_state:
    try:
        st.session_state.portfolio = Portfolio.from_json("sample_portfolio.json")
    except Exception:
        st.session_state.portfolio = Portfolio()

port = st.session_state.portfolio

# ─── Sidebar ─────────────────────────────────────────────────
st.sidebar.markdown("### Settings")

period = st.sidebar.selectbox("Analysis Period", ["6mo", "1y", "2y", "5y"], index=1)
benchmark = st.sidebar.text_input("Benchmark", value=port.benchmark_ticker)
port.benchmark_ticker = benchmark
st.session_state.portfolio.benchmark_ticker = benchmark
rfr = st.sidebar.number_input("Risk-Free Rate (%)", value=port.risk_free_rate * 100, step=0.25) / 100
port.risk_free_rate = rfr
st.session_state.portfolio.risk_free_rate = rfr

st.sidebar.markdown("---")
st.sidebar.markdown("### Load Portfolio")
uploaded = st.sidebar.file_uploader("Upload portfolio JSON", type=["json"])
if uploaded and st.session_state.get("last_upload") != uploaded.name:
    try:
        data = json.load(uploaded)
        st.session_state.portfolio = Portfolio(
            holdings=data.get("holdings", []),
            benchmark=data.get("benchmark", "SPY"),
            risk_free_rate=data.get("risk_free_rate", 0.0425),
        )
        st.session_state.last_upload = uploaded.name
        port = st.session_state.portfolio
        st.sidebar.success("Portfolio loaded")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════════
#  TAB 1: OVERVIEW
# ══════════════════════════════════════════════════════════════
with tab_overview:
    if not port.holdings:
        st.info("No holdings. Go to **Manage Portfolio** to add positions or upload a JSON file.")
    else:
        df = port.holdings_summary()
        total_cost = df["Cost Basis"].sum()
        total_value = df["Market Value"].sum()
        total_pnl = df["P&L ($)"].sum()
        total_pnl_pct = total_pnl / total_cost if total_cost > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Portfolio Value", f"${total_value:,.2f}")
        m2.metric("Total Cost", f"${total_cost:,.2f}")
        m3.metric("Total P&L", f"${total_pnl:,.2f}", delta=f"{total_pnl_pct:+.2%}")
        m4.metric("Holdings", len(df))

        st.markdown("---")

        st.markdown("#### Holdings")
        display_df = df.copy()
        display_df["Buy Price"] = display_df["Buy Price"].apply(lambda x: f"${x:,.2f}")
        display_df["Current Price"] = display_df["Current Price"].apply(lambda x: f"${x:,.2f}")
        display_df["Cost Basis"] = display_df["Cost Basis"].apply(lambda x: f"${x:,.2f}")
        display_df["Market Value"] = display_df["Market Value"].apply(lambda x: f"${x:,.2f}")
        display_df["P&L ($)"] = display_df["P&L ($)"].apply(lambda x: f"${x:+,.2f}")
        display_df["P&L (%)"] = display_df["P&L (%)"].apply(lambda x: f"{x:+.2%}")
        display_df["Weight (%)"] = display_df["Weight (%)"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        st.markdown("#### Portfolio Value Over Time")
        hist = port.portfolio_history(period)
        if not hist.empty:
            st.line_chart(hist, use_container_width=True)
            st.caption(f"Portfolio vs {benchmark} — {period}")


# ══════════════════════════════════════════════════════════════
#  TAB 2: PERFORMANCE
# ══════════════════════════════════════════════════════════════
with tab_performance:
    if not port.holdings:
        st.info("No holdings.")
    else:
        metrics = port.performance_metrics(period)

        if metrics:
            st.markdown("#### Return Metrics")
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Total Return", f"{metrics['total_return']:.2%}")
            p2.metric("CAGR", f"{metrics['cagr']:.2%}")
            p3.metric("Annual Volatility", f"{metrics['annual_volatility']:.2%}")
            p4.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")

            p5, p6, p7, p8 = st.columns(4)
            p5.metric("Sortino Ratio", f"{metrics['sortino_ratio']:.2f}")
            p6.metric("Max Drawdown", f"{metrics['max_drawdown']:.2%}")
            p7.metric("Calmar Ratio", f"{metrics['calmar_ratio']:.2f}")
            p8.metric("Win Rate", f"{metrics['win_rate']:.1f}%")

            st.markdown("---")

            st.markdown(f"#### Benchmark Comparison ({benchmark})")
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Beta", f"{metrics['beta']:.2f}")
            b2.metric("Alpha", f"{metrics['alpha']:.2%}")
            b3.metric("Best Day", f"{metrics['best_day']:.2%}")
            b4.metric("Worst Day", f"{metrics['worst_day']:.2%}")

            st.markdown("---")

            st.markdown("#### Cumulative Returns")
            hist = port.portfolio_history(period)
            if not hist.empty and len(hist) > 1:
                normalized = hist / hist.iloc[0] * 100
                col_names = list(normalized.columns)
                rename_map = {}
                for i, c in enumerate(col_names):
                    final_val = normalized.iloc[-1, i]
                    label = "Portfolio" if i == 0 else "Benchmark"
                    rename_map[c] = f"{label} ({final_val:.1f})"
                normalized = normalized.rename(columns=rename_map)
                st.line_chart(normalized, use_container_width=True)
                st.caption("Indexed to 100 at start of period")

            st.markdown("---")

            st.markdown("#### Daily Return Distribution")
            returns = port.daily_returns(period)
            if not returns.empty and "Portfolio" in returns.columns:
                ret_data = returns["Portfolio"].dropna()
                hist_data = pd.DataFrame({"Daily Return (%)": ret_data * 100})
                st.bar_chart(hist_data["Daily Return (%)"].value_counts(bins=50).sort_index())

            st.markdown("---")

            st.markdown("#### Holding Performance")
            df = port.holdings_summary()
            perf_df = df[["Ticker", "P&L (%)"]].copy()
            perf_df["P&L (%)"] = perf_df["P&L (%)"] * 100
            perf_df = perf_df.sort_values("P&L (%)", ascending=True)
            st.bar_chart(perf_df.set_index("Ticker")["P&L (%)"])
        else:
            st.warning("Not enough data to calculate metrics.")


# ══════════════════════════════════════════════════════════════
#  TAB 3: RISK ANALYSIS
# ══════════════════════════════════════════════════════════════
with tab_risk:
    if not port.holdings:
        st.info("No holdings.")
    else:
        metrics = port.performance_metrics(period)

        if metrics:
            st.markdown("#### Risk Metrics")
            r1, r2, r3 = st.columns(3)
            r1.metric("Annual Volatility", f"{metrics['annual_volatility']:.2%}")
            r2.metric("Max Drawdown", f"{metrics['max_drawdown']:.2%}")
            r3.metric("Beta", f"{metrics['beta']:.2f}")

            r4, r5, r6 = st.columns(3)
            r4.metric("VaR (95%, daily)", f"{metrics['var_95']:.2%}")
            r5.metric("CVaR (95%, daily)", f"{metrics['cvar_95']:.2%}")
            r6.metric("Calmar Ratio", f"{metrics['calmar_ratio']:.2f}")

            st.markdown("---")

            df = port.holdings_summary()
            total_value = df["Market Value"].sum()
            st.markdown(f"**1-Day Value at Risk (95%):** ${abs(metrics['var_95']) * total_value:,.2f} — "
                        f"Maximum expected single-day loss at 95% confidence.")
            st.markdown(f"**1-Day Conditional VaR (95%):** ${abs(metrics['cvar_95']) * total_value:,.2f} — "
                        f"Expected loss in the worst 5% of days.")

            st.markdown("---")

            st.markdown("#### Drawdown Over Time")
            dd = port.drawdown_series(period)
            if not dd.empty:
                dd_df = pd.DataFrame({"Drawdown (%)": dd * 100})
                st.area_chart(dd_df, use_container_width=True)
                st.caption("Distance from portfolio peak at each point in time.")

            st.markdown("---")

            st.markdown("#### Risk Contribution by Holding")
            rows = []
            for h in port.holdings:
                try:
                    hist = port._fetch_history(h["ticker"], period)
                    if isinstance(hist, pd.DataFrame):
                        hist = hist.iloc[:, 0]
                    if len(hist) > 20:
                        vol = float(hist.pct_change().dropna().std() * np.sqrt(252))
                    else:
                        vol = 0.0
                except Exception:
                    vol = 0.0
                current = port._fetch_price(h["ticker"])
                value = float(h["shares"] * current)
                rows.append({"Ticker": h["ticker"], "Volatility": vol, "Value": value})

            risk_df = pd.DataFrame(rows)
            if not risk_df.empty and risk_df["Value"].sum() > 0:
                total_val = risk_df["Value"].sum()
                risk_df["Weight"] = risk_df["Value"] / total_val
                risk_df["Risk Contribution"] = risk_df["Weight"] * risk_df["Volatility"]
                risk_df["Volatility"] = risk_df["Volatility"].apply(lambda x: f"{x:.1%}")
                risk_df["Weight"] = risk_df["Weight"].apply(lambda x: f"{x:.1%}")
                risk_df["Risk Contribution"] = risk_df["Risk Contribution"].apply(lambda x: f"{x:.2%}")
                risk_df["Value"] = risk_df["Value"].apply(lambda x: f"${x:,.0f}")
                st.dataframe(risk_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
#  TAB 4: ALLOCATION & CORRELATION
# ══════════════════════════════════════════════════════════════
with tab_allocation:
    if not port.holdings:
        st.info("No holdings.")
    else:
        df = port.holdings_summary()

        col_alloc, col_weights = st.columns(2)

        with col_alloc:
            st.markdown("#### Allocation by Holding")
            alloc_df = df[["Ticker", "Weight (%)"]].set_index("Ticker")
            st.bar_chart(alloc_df)

        with col_weights:
            st.markdown("#### Portfolio Weights")
            weight_df = df[["Ticker", "Market Value", "Weight (%)"]].copy()
            weight_df["Market Value"] = weight_df["Market Value"].apply(lambda x: f"${x:,.0f}")
            weight_df["Weight (%)"] = weight_df["Weight (%)"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(weight_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        st.markdown("#### Concentration")
        weights = df["Weight (%)"].values / 100
        hhi = np.sum(weights ** 2)
        top3 = df.nlargest(3, "Weight (%)")["Weight (%)"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("HHI Index", f"{hhi:.4f}", help="0 = perfectly diversified, 1 = single stock")
        c2.metric("Top 3 Concentration", f"{top3:.1f}%")
        c3.metric("Holdings", len(df))

        st.markdown("---")

        st.markdown("#### Return Correlation Matrix")
        corr = port.correlation_matrix(period)
        if not corr.empty:
            st.dataframe(corr.round(2).style.background_gradient(cmap="RdYlGn", vmin=-1, vmax=1),
                         use_container_width=True)
            st.caption("1.0 = perfectly correlated · 0 = uncorrelated · negative = inverse relationship")
        else:
            st.info("Need at least 2 holdings for correlation analysis.")


# ══════════════════════════════════════════════════════════════
#  TAB 5: DIVIDENDS
# ══════════════════════════════════════════════════════════════
with tab_dividends:
    if not port.holdings:
        st.info("No holdings.")
    else:
        div_df = port.dividend_summary(period)

        if not div_df.empty:
            total_div = div_df["Dividends Received ($)"].sum()
            df = port.holdings_summary()
            total_value = df["Market Value"].sum()
            portfolio_yield = total_div / total_value * 100 if total_value > 0 else 0

            d1, d2, d3 = st.columns(3)
            d1.metric("Total Dividends", f"${total_div:,.2f}")
            d2.metric("Portfolio Yield", f"{portfolio_yield:.2f}%")
            d3.metric("Avg Monthly Income", f"${total_div/12:,.2f}")

            st.markdown("---")

            st.markdown("#### Dividend by Holding")
            st.dataframe(div_df, use_container_width=True, hide_index=True)

            payers = div_df[div_df["Dividends Received ($)"] > 0].set_index("Ticker")
            if not payers.empty:
                st.bar_chart(payers["Dividends Received ($)"])


# ══════════════════════════════════════════════════════════════
#  TAB 6: MANAGE PORTFOLIO
# ══════════════════════════════════════════════════════════════
with tab_manage:
    col_add, col_current = st.columns([1, 2])

    with col_add:
        st.markdown("#### Add Holding")
        new_ticker = st.text_input("Ticker", "AAPL", key="new_ticker").upper()
        new_shares = st.number_input("Shares", min_value=1, value=10, key="new_shares")
        new_price = st.number_input("Buy Price ($)", min_value=0.01, value=100.0, step=1.0, key="new_price")
        new_date = st.date_input("Buy Date", key="new_date")

        if st.button("Add to Portfolio", use_container_width=True):
            port.add_holding(new_ticker, new_shares, new_price, str(new_date))
            st.success(f"Added {new_shares} shares of {new_ticker}")
            st.rerun()

        st.markdown("---")

        st.markdown("#### Remove Holding")
        if port.holdings:
            tickers = [h["ticker"] for h in port.holdings]
            remove_ticker = st.selectbox("Select ticker", tickers, key="rm_ticker")
            if st.button("Remove", use_container_width=True):
                port.holdings = [h for h in port.holdings if h["ticker"] != remove_ticker]
                st.success(f"Removed {remove_ticker}")
                st.rerun()

        st.markdown("---")

        st.markdown("#### Save Portfolio")
        save_name = st.text_input("Filename", "my_portfolio.json", key="save_name")
        if st.button("Save as JSON", use_container_width=True):
            port.to_json(save_name)
            st.success(f"Saved to {save_name}")

    with col_current:
        st.markdown("#### Current Holdings")
        if port.holdings:
            manage_df = pd.DataFrame(port.holdings)
            st.dataframe(manage_df, use_container_width=True, hide_index=True)

            json_str = json.dumps({
                "holdings": port.holdings,
                "benchmark": port.benchmark_ticker,
                "risk_free_rate": port.risk_free_rate,
            }, indent=2)
            st.download_button("Download Portfolio JSON", json_str,
                               file_name="portfolio.json", mime="application/json",
                               use_container_width=True)
        else:
            st.info("No holdings yet.")

        st.markdown("---")

        st.markdown("#### Current Portfolio Data")
        if port.holdings:
            st.json({
                "holdings": port.holdings,
                "benchmark": port.benchmark_ticker,
                "risk_free_rate": port.risk_free_rate,
            })
        else:
            st.caption("Add holdings to see portfolio data here.")


# ─── Footer ──────────────────────────────────────────────────
st.markdown("---")
st.caption(f"Portfolio Analytics · {len(port.holdings)} holdings · Benchmark: {benchmark} · Period: {period}")
