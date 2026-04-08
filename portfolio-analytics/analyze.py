"""
Portfolio Analytics — CLI
==========================
Usage:
    python analyze.py --portfolio sample_portfolio.json
    python analyze.py --portfolio sample_portfolio.json --period 2y
"""

import warnings
from argparse import ArgumentParser
from portfolio import Portfolio


def main():
    warnings.filterwarnings("ignore")

    parser = ArgumentParser(description="Portfolio Analytics CLI")
    parser.add_argument("--portfolio", required=True, help="Path to portfolio JSON file")
    parser.add_argument("--period", default="1y", help="Analysis period (6mo, 1y, 2y, 5y)")
    parser.add_argument("--benchmark", default=None, help="Benchmark ticker (default: SPY)")
    parser.add_argument("--save", default=None, help="Save updated portfolio to JSON")
    args = parser.parse_args()

    port = Portfolio.from_json(args.portfolio)
    if args.benchmark:
        port.benchmark_ticker = args.benchmark

    port.summary(args.period)

    # Correlation
    corr = port.correlation_matrix(args.period)
    if not corr.empty:
        print("  CORRELATION MATRIX")
        print(f"  {'─'*45}")
        print(corr.round(2).to_string())
        print()

    # Dividends
    div = port.dividend_summary(args.period)
    if not div.empty and div["Dividends Received ($)"].sum() > 0:
        print("  DIVIDEND INCOME")
        print(f"  {'─'*45}")
        print(div.to_string(index=False))
        print(f"\n  Total: ${div['Dividends Received ($)'].sum():,.2f}\n")

    if args.save:
        port.to_json(args.save)
        print(f"  Saved to {args.save}\n")


if __name__ == "__main__":
    main()
