"""
Portfolio Analytics Engine
===========================
Core portfolio management and performance analysis.

Features:
    - Load/save portfolios from JSON
    - Fetch historical prices via yfinance
    - Calculate returns, P&L, weights
    - Risk metrics (volatility, Sharpe, Sortino, max drawdown, VaR, CVaR)
    - Benchmark comparison
    - Correlation analysis
    - Dividend tracking
"""

import numpy as np
import pandas as pd
import yfinance as yf
import json
import os
from datetime import datetime, timedelta


class Portfolio:
    """
    Portfolio analytics engine.

    Parameters
    ----------
    holdings : list of dict
        Each holding: {"ticker": "AAPL", "shares": 10, "buy_price": 150.0, "buy_date": "2024-01-15"}
    benchmark : str
        Benchmark ticker for comparison (default: "SPY")
    risk_free_rate : float
        Annual risk-free rate for Sharpe/Sortino (default: 0.0425)
    """

    def __init__(self, holdings=None, benchmark="SPY", risk_free_rate=0.0425):
        self.holdings = holdings or []
        self.benchmark_ticker = benchmark
        self.risk_free_rate = risk_free_rate
        self._price_cache = {}

    # ─── Portfolio I/O ───────────────────────────────────────────

    @classmethod
    def from_json(cls, filepath):
        """Load portfolio from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls(
            holdings=data.get("holdings", []),
            benchmark=data.get("benchmark", "SPY"),
            risk_free_rate=data.get("risk_free_rate", 0.0425),
        )

    def to_json(self, filepath):
        """Save portfolio to a JSON file."""
        data = {
            "holdings": self.holdings,
            "benchmark": self.benchmark_ticker,
            "risk_free_rate": self.risk_free_rate,
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def add_holding(self, ticker, shares, buy_price, buy_date):
        """Add a new holding to the portfolio."""
        self.holdings.append({
            "ticker": ticker.upper(),
            "shares": shares,
            "buy_price": buy_price,
            "buy_date": buy_date,
        })

    # ─── Price Data ──────────────────────────────────────────────

    def _fetch_price(self, ticker):
        """Fetch current price for a ticker."""
        if ticker in self._price_cache:
            return self._price_cache[ticker]
        try:
            stock = yf.Ticker(ticker)
            price = stock.info.get("previousClose", stock.info.get("regularMarketPrice", 0))
            self._price_cache[ticker] = price
            return price
        except Exception:
            return 0

    def _fetch_history(self, ticker, period="1y"):
        """Fetch historical adjusted close prices."""
        try:
            data = yf.download(ticker, period=period, progress=False)
            if "Adj Close" in data.columns:
                return data["Adj Close"]
            return data["Close"]
        except Exception:
            return pd.Series(dtype=float)

    def _fetch_dividends(self, ticker, period="1y"):
        """Fetch dividend history for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            divs = stock.dividends
            cutoff = datetime.now() - timedelta(days=365 * (int(period.replace("y", "")) if "y" in period else 1))
            return divs[divs.index >= cutoff.strftime("%Y-%m-%d")]
        except Exception:
            return pd.Series(dtype=float)

    # ─── Holdings Summary ────────────────────────────────────────

    def holdings_summary(self):
        """
        Returns a DataFrame with current holdings data:
        Ticker, Shares, Buy Price, Current Price, Market Value,
        Cost Basis, P&L ($), P&L (%), Weight
        """
        rows = []
        for h in self.holdings:
            ticker = h["ticker"]
            shares = h["shares"]
            buy_price = h["buy_price"]
            current = self._fetch_price(ticker)
            cost = shares * buy_price
            value = shares * current
            pnl = value - cost
            pnl_pct = pnl / cost if cost > 0 else 0

            rows.append({
                "Ticker": ticker,
                "Shares": shares,
                "Buy Price": buy_price,
                "Current Price": current,
                "Cost Basis": cost,
                "Market Value": value,
                "P&L ($)": pnl,
                "P&L (%)": pnl_pct,
                "Buy Date": h.get("buy_date", "N/A"),
            })

        df = pd.DataFrame(rows)
        if len(df) > 0:
            total_value = df["Market Value"].sum()
            df["Weight (%)"] = df["Market Value"] / total_value * 100 if total_value > 0 else 0
        return df

    # ─── Portfolio Returns ───────────────────────────────────────

    def portfolio_history(self, period="1y"):
        """
        Calculate daily portfolio value over time.
        Returns a DataFrame with portfolio value and benchmark.
        """
        tickers = list(set(h["ticker"] for h in self.holdings))
        if not tickers:
            return pd.DataFrame()

        # Download all at once
        try:
            data = yf.download(tickers, period=period, progress=False)
            if len(tickers) == 1:
                prices = data[["Close"]].rename(columns={"Close": tickers[0]})
            else:
                prices = data["Close"] if "Close" in data.columns.get_level_values(0) else data["Adj Close"]
        except Exception:
            return pd.DataFrame()

        if isinstance(prices, pd.Series):
            prices = prices.to_frame(name=tickers[0])

        # Flatten MultiIndex columns if needed
        if isinstance(prices.columns, pd.MultiIndex):
            prices.columns = prices.columns.get_level_values(-1)

        # Portfolio value = sum(shares * price) for each day
        portfolio_val = pd.Series(0.0, index=prices.index)
        for h in self.holdings:
            t = h["ticker"]
            if t in prices.columns:
                portfolio_val += h["shares"] * prices[t].ffill()

        # Benchmark
        try:
            bench = yf.download(self.benchmark_ticker, period=period, progress=False)
            bench_prices = bench["Close"] if "Close" in bench.columns else bench["Adj Close"]
            if isinstance(bench_prices, pd.DataFrame):
                bench_prices = bench_prices.iloc[:, 0]
        except Exception:
            bench_prices = pd.Series(dtype=float)

        result = pd.DataFrame({"Portfolio": portfolio_val})
        if len(bench_prices) > 0:
            # Normalize benchmark to same starting value as portfolio
            common_idx = portfolio_val.index.intersection(bench_prices.index)
            if len(common_idx) > 0:
                scale = portfolio_val.iloc[0] / bench_prices.loc[common_idx[0]] if bench_prices.loc[common_idx[0]] != 0 else 1
                result["Benchmark"] = bench_prices.reindex(portfolio_val.index).ffill() * scale

        return result

    def daily_returns(self, period="1y"):
        """Calculate daily portfolio returns."""
        hist = self.portfolio_history(period)
        if "Portfolio" not in hist.columns or len(hist) < 2:
            return pd.DataFrame()
        returns = hist.pct_change().dropna()
        return returns

    # ─── Performance Metrics ─────────────────────────────────────

    def performance_metrics(self, period="1y"):
        """
        Calculate key performance metrics.
        Returns a dict with all risk/return statistics.
        """
        returns = self.daily_returns(period)
        if returns.empty or "Portfolio" not in returns.columns:
            return {}

        port_ret = returns["Portfolio"].dropna()
        n_days = len(port_ret)
        if n_days < 2:
            return {}

        # Annualization factor
        ann = 252

        # Total return
        hist = self.portfolio_history(period)
        total_return = (hist["Portfolio"].iloc[-1] / hist["Portfolio"].iloc[0]) - 1

        # Annualized return
        years = n_days / ann
        cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # Volatility
        daily_vol = port_ret.std()
        annual_vol = daily_vol * np.sqrt(ann)

        # Sharpe Ratio
        excess_daily = port_ret.mean() - self.risk_free_rate / ann
        sharpe = (excess_daily / daily_vol * np.sqrt(ann)) if daily_vol > 0 else 0

        # Sortino Ratio (downside deviation)
        downside = port_ret[port_ret < 0]
        downside_dev = downside.std() * np.sqrt(ann) if len(downside) > 0 else 0.0001
        sortino = (port_ret.mean() * ann - self.risk_free_rate) / downside_dev if downside_dev > 0 else 0

        # Max Drawdown
        cumulative = (1 + port_ret).cumprod()
        rolling_max = cumulative.cummax()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_dd = drawdown.min()

        # VaR and CVaR (95%)
        var_95 = np.percentile(port_ret, 5)
        cvar_95 = port_ret[port_ret <= var_95].mean() if len(port_ret[port_ret <= var_95]) > 0 else var_95

        # Calmar Ratio
        calmar = cagr / abs(max_dd) if max_dd != 0 else 0

        # Beta and Alpha vs benchmark
        beta, alpha = 0, 0
        if "Benchmark" in returns.columns:
            bench_ret = returns["Benchmark"].dropna()
            common = port_ret.index.intersection(bench_ret.index)
            if len(common) > 10:
                p = port_ret.loc[common]
                b = bench_ret.loc[common]
                cov_matrix = np.cov(p, b)
                beta = cov_matrix[0, 1] / cov_matrix[1, 1] if cov_matrix[1, 1] != 0 else 0
                bench_total = (hist["Benchmark"].iloc[-1] / hist["Benchmark"].iloc[0]) - 1 if "Benchmark" in hist.columns else 0
                bench_ann = (1 + bench_total) ** (1 / years) - 1 if years > 0 else 0
                alpha = cagr - (self.risk_free_rate + beta * (bench_ann - self.risk_free_rate))

        # Win rate
        win_rate = (port_ret > 0).sum() / n_days * 100

        # Best / worst day
        best_day = port_ret.max()
        worst_day = port_ret.min()

        return {
            "total_return": total_return,
            "cagr": cagr,
            "annual_volatility": annual_vol,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown": max_dd,
            "calmar_ratio": calmar,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "beta": beta,
            "alpha": alpha,
            "win_rate": win_rate,
            "best_day": best_day,
            "worst_day": worst_day,
            "trading_days": n_days,
        }

    # ─── Correlation Matrix ──────────────────────────────────────

    def correlation_matrix(self, period="1y"):
        """Calculate return correlations between all holdings."""
        tickers = list(set(h["ticker"] for h in self.holdings))
        if len(tickers) < 2:
            return pd.DataFrame()

        try:
            data = yf.download(tickers, period=period, progress=False)
            if len(tickers) == 1:
                return pd.DataFrame()
            prices = data["Close"] if "Close" in data.columns.get_level_values(0) else data["Adj Close"]
        except Exception:
            return pd.DataFrame()

        if isinstance(prices.columns, pd.MultiIndex):
            prices.columns = prices.columns.get_level_values(-1)

        returns = prices.pct_change().dropna()
        return returns.corr()

    # ─── Dividend Summary ────────────────────────────────────────

    def dividend_summary(self, period="1y"):
        """Calculate dividend income by holding."""
        rows = []
        for h in self.holdings:
            divs = self._fetch_dividends(h["ticker"], period)
            total_div = divs.sum() * h["shares"] if len(divs) > 0 else 0
            div_count = len(divs)
            current = self._fetch_price(h["ticker"])
            div_yield = (divs.sum() / current * 100) if current > 0 and len(divs) > 0 else 0

            rows.append({
                "Ticker": h["ticker"],
                "Shares": h["shares"],
                "Dividends Received ($)": round(total_div, 2),
                "# Payments": div_count,
                "Yield (%)": round(div_yield, 2),
            })

        return pd.DataFrame(rows)

    # ─── Drawdown Series ─────────────────────────────────────────

    def drawdown_series(self, period="1y"):
        """Calculate the drawdown series for charting."""
        returns = self.daily_returns(period)
        if returns.empty or "Portfolio" not in returns.columns:
            return pd.Series(dtype=float)

        cumulative = (1 + returns["Portfolio"]).cumprod()
        rolling_max = cumulative.cummax()
        drawdown = (cumulative - rolling_max) / rolling_max
        return drawdown

    # ─── Summary Print ───────────────────────────────────────────

    def summary(self, period="1y"):
        """Print a full portfolio summary to terminal."""
        sep = "=" * 60

        print(f"\n{sep}")
        print(f"  PORTFOLIO ANALYTICS")
        print(f"{sep}")

        # Holdings
        df = self.holdings_summary()
        if df.empty:
            print("  No holdings.")
            return

        total_cost = df["Cost Basis"].sum()
        total_value = df["Market Value"].sum()
        total_pnl = df["P&L ($)"].sum()

        print(f"\n  HOLDINGS")
        print(f"  {'─'*45}")
        for _, row in df.iterrows():
            print(f"  {row['Ticker']:<6} {row['Shares']:>6} shares  "
                  f"${row['Current Price']:>8.2f}  "
                  f"${row['Market Value']:>10,.2f}  "
                  f"{'↑' if row['P&L ($)'] >= 0 else '↓'} ${abs(row['P&L ($)']):>8,.2f} ({row['P&L (%)']:+.1%})")

        print(f"\n  Total Cost:    ${total_cost:>12,.2f}")
        print(f"  Total Value:   ${total_value:>12,.2f}")
        print(f"  Total P&L:     ${total_pnl:>12,.2f} ({total_pnl/total_cost:+.2%})")

        # Performance
        metrics = self.performance_metrics(period)
        if metrics:
            print(f"\n  PERFORMANCE ({period})")
            print(f"  {'─'*45}")
            print(f"  Total Return:       {metrics['total_return']:>10.2%}")
            print(f"  CAGR:               {metrics['cagr']:>10.2%}")
            print(f"  Annual Volatility:  {metrics['annual_volatility']:>10.2%}")
            print(f"  Sharpe Ratio:       {metrics['sharpe_ratio']:>10.2f}")
            print(f"  Sortino Ratio:      {metrics['sortino_ratio']:>10.2f}")
            print(f"  Max Drawdown:       {metrics['max_drawdown']:>10.2%}")
            print(f"  Calmar Ratio:       {metrics['calmar_ratio']:>10.2f}")
            print(f"  VaR (95%, daily):   {metrics['var_95']:>10.2%}")
            print(f"  CVaR (95%, daily):  {metrics['cvar_95']:>10.2%}")
            print(f"  Beta:               {metrics['beta']:>10.2f}")
            print(f"  Alpha:              {metrics['alpha']:>10.2%}")
            print(f"  Win Rate:           {metrics['win_rate']:>10.1f}%")
            print(f"  Best Day:           {metrics['best_day']:>10.2%}")
            print(f"  Worst Day:          {metrics['worst_day']:>10.2%}")

        print(f"\n{sep}\n")
