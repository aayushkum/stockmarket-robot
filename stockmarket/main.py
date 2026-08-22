"""Stock market analysis CLI entry point."""
import argparse
from datetime import datetime, timezone
from typing import Optional

from .config import Settings
from .analyzer import analyze
from .db import Database
from .universe import sp500_tickers
from .dashboard import create_app
from .paper import PaperPortfolio


def run_scan(settings: Settings, limit: Optional[int] = None) -> None:
    """Scan S&P 500 stocks and save analysis results.
    
    Args:
        settings: Configuration settings.
        limit: Maximum number of tickers to scan (None = all).
    """
    db = Database(settings.db_path)
    tickers = sp500_tickers()[:limit] if limit else sp500_tickers()
    
    success_count = 0
    error_count = 0
    
    for ticker in tickers:
        try:
            result = analyze(ticker, settings)
            db.save_analysis(ticker, result['analyzed_at'], result)
            fair_value = result['fair_value'] or 0
            print(
                f"{ticker:6} {result['signal']:4} score={result['master_score']:5.1f} "
                f"price=${result['price']:9.2f} fair=${fair_value:9.2f}"
            )
            success_count += 1
        except ValueError as e:
            # Data fetch error - ticker may be invalid or data unavailable
            print(f"{ticker:6} ERROR Data unavailable: {e}")
            error_count += 1
        except Exception as e:
            # Unexpected error - log with more context
            print(f"{ticker:6} ERROR Unexpected error: {type(e).__name__}: {e}")
            error_count += 1
    
    db.close()
    print(f"\nScan complete: {success_count} succeeded, {error_count} failed")


def run_paper_trade(settings: Settings, limit: Optional[int] = None) -> None:
    """Analyze a watchlist and execute configured signals in paper only."""
    db = Database(settings.db_path)
    portfolio = db.load_portfolio(settings)
    tickers = sp500_tickers()[:limit] if limit else sp500_tickers()
    timestamp = datetime.now(timezone.utc).isoformat()

    for ticker in tickers:
        try:
            result = analyze(ticker, settings)
            price = result["price"]
            if result["signal"] == "SELL" and ticker in portfolio.positions:
                position = portfolio.positions[ticker]
                shares = position.shares
                proceeds = portfolio.sell(ticker, price)
                db.save_trade(timestamp, ticker, "SELL", shares, price, proceeds)
            elif (result["signal"] == "BUY"
                  and ticker not in portfolio.positions
                  and len(portfolio.positions) < settings.max_positions):
                slots = settings.max_positions - len(portfolio.positions)
                amount = portfolio.cash / slots if slots else 0
                if portfolio.buy(ticker, price, amount):
                    shares = amount / price
                    db.save_trade(timestamp, ticker, "BUY", shares, price, amount)
        except (ValueError, KeyError) as error:
            print(f"{ticker:6} ERROR {error}")

    db.save_portfolio(portfolio.cash, portfolio.positions)
    db.close()
    print(f"Paper trade complete: cash=${portfolio.cash:,.2f}, "
          f"positions={len(portfolio.positions)}")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Stock market analysis robot")
    subparsers = parser.add_subparsers(dest='command')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan S&P 500 stocks')
    scan_parser.add_argument('--limit', type=int, help='Limit number of stocks to scan')
    
    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Backtest strategy')
    backtest_parser.add_argument('--ticker', default='AAPL', help='Stock ticker')
    backtest_parser.add_argument('--period', default='5y', help='Historical period')
    backtest_parser.add_argument('--snapshots', help='Point-in-time snapshot JSON')
    backtest_parser.add_argument('--snapshot-dir', help='Directory of ticker snapshot JSON files')
    backtest_parser.add_argument(
        '--full-system', action='store_true',
        help='Backtest valuation, scoring, signals, and paper execution'
    )

    paper_parser = subparsers.add_parser('paper-trade', help='Execute paper trades')
    paper_parser.add_argument('--limit', type=int, help='Limit number of stocks')
    
    # Dashboard command
    subparsers.add_parser('dashboard', help='Launch Flask dashboard')
    
    args = parser.parse_args()
    settings = Settings.from_env()
    
    if args.command == 'scan':
        run_scan(settings, args.limit)
    elif args.command == 'backtest':
        from .backtest import (full_system_backtest, full_system_universe_backtest,
                                moving_average_backtest)
        if args.full_system:
            if args.snapshot_dir:
                result = full_system_universe_backtest(
                    sp500_tickers(), args.snapshot_dir, args.period, settings
                )
            elif args.snapshots:
                result = full_system_backtest(
                    args.ticker, args.snapshots, args.period, settings
                )
            else:
                parser.error('--full-system requires --snapshots or --snapshot-dir')
        else:
            result = moving_average_backtest(
                args.ticker, args.period, args.snapshots
            )
        print(result)
    elif args.command == 'paper-trade':
        run_paper_trade(settings, args.limit)
    else:
        # Default: run dashboard
        app = create_app(settings.db_path)
        app.run(host=settings.dashboard_host, port=settings.dashboard_port)


if __name__ == '__main__':
    main()
