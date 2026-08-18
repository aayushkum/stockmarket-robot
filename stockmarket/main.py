"""Stock market analysis CLI entry point."""
import argparse
from typing import Optional

from .config import Settings
from .analyzer import analyze
from .db import Database
from .universe import sp500_tickers
from .dashboard import create_app


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
            result = analyze(ticker)
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
    
    # Dashboard command
    subparsers.add_parser('dashboard', help='Launch Flask dashboard')
    
    args = parser.parse_args()
    settings = Settings.from_env()
    
    if args.command == 'scan':
        run_scan(settings, args.limit)
    elif args.command == 'backtest':
        from .backtest import moving_average_backtest
        result = moving_average_backtest(args.ticker, args.period)
        print(result)
    else:
        # Default: run dashboard
        app = create_app(settings.db_path)
        app.run(host=settings.dashboard_host, port=settings.dashboard_port)


if __name__ == '__main__':
    main()
