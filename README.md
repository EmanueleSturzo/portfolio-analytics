# Portfolio Analytics

A Python portfolio tracker and risk analytics dashboard. Load a portfolio from JSON, fetch live prices from Yahoo Finance, and analyze performance, risk, allocation, correlation, and dividends through an interactive Streamlit web app.

## Features

| Feature | Description |
|---|---|
| **Holdings Tracker** | Current prices, P&L ($, %), cost basis, market value, and portfolio weights pulled live from Yahoo Finance |
| **Performance Metrics** | Total return, CAGR, annual volatility, Sharpe ratio, Sortino ratio, Calmar ratio, win rate |
| **Benchmark Comparison** | Normalized portfolio vs benchmark chart (default: SPY), beta, alpha calculation |
| **Risk Analysis** | Max drawdown with time series chart, VaR and CVaR (95%), individual holding risk contribution |
| **Asset Allocation** | Weight breakdown, HHI concentration index, top-3 concentration metric |
| **Correlation Matrix** | Return correlations across all holdings with heatmap styling |
| **Dividend Tracking** | Income by holding, portfolio yield, payment count |
| **Portfolio Management** | Add/remove holdings, save/load from JSON, download portfolio file |
| **Streamlit Dashboard** | 6-tab interactive web app with charts and real-time data |
| **CLI Interface** | Terminal-based analysis for quick checks |

## Quick Start

Clone the repo:
git clone https://github.com/EmanueleSturzo/Portfolio-Analytics.git
(download zip file and extract)

for Mac:
cd ~/Downloads/Portfolio-Analytics-main

for windows:
cd C:\Users\UserName\Downloads\Portfolio-Analytics-main

```bash
pip install -r requirements.txt

# Launch web app
python -m streamlit run streamlit_app.py

# Or use CLI
python analyze.py --portfolio sample_portfolio.json
python analyze.py --portfolio sample_portfolio.json --period 2y --benchmark QQQ
```

## Web App

The Streamlit dashboard has 6 tabs:

- **Overview** — Holdings table, portfolio value chart vs benchmark, total P&L
- **Performance** — CAGR, Sharpe, Sortino, cumulative returns chart, daily return distribution, per-holding performance
- **Risk Analysis** — Volatility, max drawdown chart, VaR/CVaR in % and $, beta, risk contribution by holding
- **Allocation & Correlation** — Weight breakdown, HHI concentration, return correlation matrix with heatmap
- **Dividends** — Total income, portfolio yield, monthly average, income by holding chart
- **Manage Portfolio** — Add/remove holdings, save/load JSON, download file

## Portfolio JSON Format

```json
{
  "holdings": [
    {"ticker": "AAPL", "shares": 50, "buy_price": 175.00, "buy_date": "2024-06-15"},
    {"ticker": "MSFT", "shares": 30, "buy_price": 380.00, "buy_date": "2024-03-10"},
    {"ticker": "NVDA", "shares": 25, "buy_price": 120.00, "buy_date": "2024-01-08"}
  ],
  "benchmark": "SPY",
  "risk_free_rate": 0.0425
}
```

A sample portfolio with 10 diversified holdings is included in `sample_portfolio.json`.

## Use as a Python Library

```python
from portfolio import Portfolio

# Load portfolio
port = Portfolio.from_json("sample_portfolio.json")

# Holdings summary
print(port.holdings_summary())

# Performance metrics
metrics = port.performance_metrics("1y")
print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
print(f"Alpha: {metrics['alpha']:.2%}")

# Correlation matrix
print(port.correlation_matrix("1y"))

# Dividend income
print(port.dividend_summary("1y"))

# Add a new holding
port.add_holding("TSLA", 20, 250.00, "2025-01-10")
port.to_json("updated_portfolio.json")
```

## Metrics Explained

| Metric | What It Measures |
|---|---|
| **CAGR** | Compound Annual Growth Rate — smoothed annual return |
| **Sharpe Ratio** | Excess return per unit of total risk. Higher = better. Above 1.0 is good, above 2.0 is excellent |
| **Sortino Ratio** | Like Sharpe but only penalizes downside volatility |
| **Max Drawdown** | Largest peak-to-trough decline. Measures worst-case loss |
| **Calmar Ratio** | CAGR divided by max drawdown. Higher = better recovery |
| **VaR (95%)** | Value at Risk — max expected daily loss at 95% confidence |
| **CVaR (95%)** | Conditional VaR — expected loss in the worst 5% of days |
| **Beta** | Sensitivity to benchmark. 1.0 = moves with market. >1.0 = more volatile |
| **Alpha** | Excess return above what beta would predict. Positive = outperformance |
| **HHI** | Herfindahl-Hirschman Index — measures portfolio concentration (0 = diversified, 1 = concentrated) |

## Project Structure

```
portfolio-analytics/
├── portfolio.py             # Core analytics engine
├── streamlit_app.py         # Interactive web dashboard
├── analyze.py               # CLI interface
├── sample_portfolio.json    # Sample 10-stock portfolio
├── requirements.txt
├── LICENSE
├── .gitignore
└── README.md
```

## Data Source

All market data is fetched from [Yahoo Finance](https://finance.yahoo.com) via `yfinance`. No API key required.

## License

[MIT](LICENSE)
