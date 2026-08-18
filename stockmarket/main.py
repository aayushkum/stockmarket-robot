"""Stock market analysis CLI entry point."""
import argparse

from .analyzer import analyze
from .backtest import (
    backtest_with_snapshots,
    load_snapshot_history,
)
from .config import Settings
from .dashboard import create_app
from .data import price_history
from .db import Database
from .universe import sp500_tickers


def run_scan(
    settings: Settings,
    limit: int | None = None,
) -> None:
    """Scan S&P 500 stocks and save analysis results."""

    db = Database(settings.db_path)

    tickers = (
        sp500_tickers()[:limit]
        if limit
        else sp500_tickers()
    )

    success_count = 0
    error_count = 0

    for ticker in tickers:

        try:
            result = analyze(ticker)

            db.save_analysis(
                ticker,
                result["analyzed_at"],
                result,
            )

            fair_value = (
                result["fair_value"]
                or 0
            )

            print(
                f"{ticker:6} "
                f"{result['signal']:4} "
                f"score={result['master_score']:5.1f} "
                f"price=${result['price']:9.2f} "
                f"fair=${fair_value:9.2f}"
            )

            success_count += 1

        except ValueError as exc:

            print(
                f"{ticker:6} "
                f"ERROR Data unavailable: {exc}"
            )

            error_count += 1

        except Exception as exc:

            print(
                f"{ticker:6} "
                f"ERROR Unexpected error: "
                f"{type(exc).__name__}: {exc}"
            )

            error_count += 1

    db.close()

    print(
        f"\nScan complete: "
        f"{success_count} succeeded, "
        f"{error_count} failed"
    )


def run_backtest(
    ticker: str,
    period: str,
    snapshots_path: str,
) -> None:
    """Run the robot against point-in-time historical snapshots."""

    snapshots = load_snapshot_history(
        snapshots_path
    )

    prices = price_history(
        ticker,
        period,
    )

    result = backtest_with_snapshots(
        ticker=ticker,
        prices=prices,
        snapshots=snapshots,
    )

    print(
        f"Ticker:              "
        f"{result['ticker']}"
    )

    print(
        f"Period:              "
        f"{result['start_date']} → "
        f"{result['end_date']}"
    )

    print(
        f"Initial capital:     "
        f"${result['initial_capital']:,.2f}"
    )

    print(
        f"Final equity:        "
        f"${result['final_equity']:,.2f}"
    )

    print(
        f"Strategy return:     "
        f"{result['strategy_return']:.2%}"
    )

    print(
        f"Benchmark return:    "
        f"{result['benchmark_return']:.2%}"
    )

    print(
        f"CAGR:                "
        f"{result['cagr']:.2%}"
    )

    print(
        f"Max drawdown:        "
        f"{result['max_drawdown']:.2%}"
    )

    print(
        f"Sharpe:              "
        f"{result['sharpe']:.2f}"
    )

    print(
        f"Trades:              "
        f"{result['trade_count']}"
    )

    print(
        f"Skipped observations:"
        f"{result['skipped_observations']}"
    )


def main() -> None:
    """Main CLI entry point."""

    parser = argparse.ArgumentParser(
        description="Stock market analysis robot"
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan S&P 500 stocks",
    )

    scan_parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of stocks to scan",
    )

    backtest_parser = subparsers.add_parser(
        "backtest",
        help="Backtest the actual analysis engine",
    )

    backtest_parser.add_argument(
        "--ticker",
        default="AAPL",
        help="Stock ticker",
    )

    backtest_parser.add_argument(
        "--period",
        default="5y",
        help="Historical price period",
    )

    backtest_parser.add_argument(
        "--snapshots",
        required=True,
        help=(
            "JSON file containing point-in-time "
            "fundamental snapshots keyed by date"
        ),
    )

    subparsers.add_parser(
        "dashboard",
        help="Launch Flask dashboard",
    )

    args = parser.parse_args()

    settings = Settings.from_env()

    if args.command == "scan":

        run_scan(
            settings,
            args.limit,
        )

    elif args.command == "backtest":

        run_backtest(
            args.ticker,
            args.period,
            args.snapshots,
        )

    else:

        app = create_app(
            settings.db_path
        )

        app.run(
            host=settings.dashboard_host,
            port=settings.dashboard_port,
        )


if __name__ == "__main__":
    main()
