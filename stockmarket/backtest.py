"""Historical backtest of moving average strategy."""
import json
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import yfinance as yf
from .data import Snapshot
from .scoring import master_score, signal, momentum_score
from .valuation import summarize
from .analyzer import analyze_snapshot
from .config import Settings
from .paper import PaperPortfolio


def load_snapshot_history(path: str | Path) -> Dict[str, Snapshot]:
    """Load date-keyed snapshots from a builder output JSON file."""
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_snapshots = document.get("snapshots", document)
    return {
        date_key: Snapshot(**snapshot)
        for date_key, snapshot in raw_snapshots.items()
        if isinstance(snapshot, dict) and "price" in snapshot
    }


def full_system_backtest(
    ticker: str, snapshots: str | Path, period: str = "5y",
    settings: Optional[Settings] = None,
) -> Dict[str, Any]:
    """Backtest valuation, scoring, signals, and paper execution together.

    Decisions use the latest snapshot and price history available before the
    next trading day's close. Orders are then executed at that next close,
    avoiding same-day lookahead. This single-ticker mode invests available cash
    on BUY and exits the position on SELL.
    """
    settings = settings or Settings()
    snapshot_history = load_snapshot_history(snapshots)
    if not snapshot_history:
        raise ValueError("Snapshot history is empty")
    try:
        df = yf.Ticker(ticker).history(period=period, auto_adjust=True)
    except Exception as error:
        raise ValueError(f"Failed to fetch backtest data for {ticker}: {error}") from error
    if df.empty or "Close" not in df:
        raise ValueError(f"No usable price history available for {ticker}")

    close = df["Close"].dropna()
    dated_snapshots = sorted(
        (pd.Timestamp(key).tz_localize(None), value)
        for key, value in snapshot_history.items()
    )
    portfolio = PaperPortfolio(settings)
    equity = []
    trades = 0

    for index in range(1, len(close)):
        decision_date = pd.Timestamp(close.index[index - 1]).tz_localize(None)
        available = [item for item in dated_snapshots if item[0] <= decision_date]
        if not available:
            equity.append(portfolio.cash)
            continue
        decision_price = float(close.iloc[index - 1])
        execution_price = float(close.iloc[index])
        dated_snapshot = available[-1][1]
        decision_snapshot = Snapshot(**{
            **dated_snapshot.to_dict(), "price": decision_price
        })
        history = close.iloc[:index]
        result = analyze_snapshot(
            ticker, decision_snapshot, pd.DataFrame({"Close": history}), settings
        )
        if result["signal"] == "BUY" and ticker not in portfolio.positions:
            if portfolio.buy(ticker, execution_price, portfolio.cash):
                trades += 1
        elif result["signal"] == "SELL" and ticker in portfolio.positions:
            portfolio.sell(ticker, execution_price)
            trades += 1
        equity.append(portfolio.equity({ticker: execution_price}))

    equity_series = pd.Series(equity, index=close.index[1:])
    initial = settings.starting_cash
    final = float(equity_series.iloc[-1]) if not equity_series.empty else initial
    years = max((close.index[-1] - close.index[0]).days / 365.25, 1 / 365.25)
    daily_returns = equity_series.pct_change().fillna(0)
    volatility = daily_returns.std() * np.sqrt(252)
    return {
        "ticker": ticker,
        "period": period,
        "strategy": "full_system",
        "starting_cash": initial,
        "ending_equity": final,
        "strategy_return": final / initial - 1,
        "benchmark_return": float(close.iloc[-1] / close.iloc[0] - 1),
        "cagr": float((final / initial) ** (1 / years) - 1),
        "max_drawdown": float((equity_series / equity_series.cummax() - 1).min()) if not equity_series.empty else 0.0,
        "sharpe": float(daily_returns.mean() * 252 / volatility) if volatility > 0 else 0.0,
        "observations": int(len(close)),
        "trade_count": trades,
    }


def full_system_universe_backtest(
    tickers: list[str], snapshot_dir: str | Path, period: str = "5y",
    settings: Optional[Settings] = None,
) -> Dict[str, Any]:
    """Run the full-system backtest for every ticker with dated snapshots.

    Each ticker must have ``<ticker>.json`` in ``snapshot_dir``. Missing files
    are reported and skipped rather than replaced with current fundamentals.
    """
    results: Dict[str, Any] = {}
    missing: list[str] = []
    directory = Path(snapshot_dir)
    for ticker in tickers:
        snapshot_path = directory / f"{ticker.lower()}_snapshots.json"
        if not snapshot_path.exists():
            missing.append(ticker)
            continue
        results[ticker] = full_system_backtest(
            ticker, snapshot_path, period, settings
        )

    valid = list(results.values())
    return {
        "period": period,
        "strategy": "full_system",
        "requested_tickers": len(tickers),
        "completed_tickers": len(valid),
        "missing_snapshot_tickers": missing,
        "results": results,
        "average_return": float(np.mean([r["strategy_return"] for r in valid])) if valid else None,
        "average_benchmark_return": float(np.mean([r["benchmark_return"] for r in valid])) if valid else None,
        "average_cagr": float(np.mean([r["cagr"] for r in valid])) if valid else None,
        "average_sharpe": float(np.mean([r["sharpe"] for r in valid])) if valid else None,
    }


def moving_average_backtest(
    ticker: str, period: str = "5y", snapshots: Optional[str] = None,
    fast_window: int = 30, slow_window: int = 200
) -> Dict[str, Any]:
    """Backtest a long-only moving average crossover strategy.
    
    Default strategy:
    - BUY: fast moving average > slow moving average
    - SELL: fast moving average < slow moving average

    The default 30/200 windows reduce the lag observed in the previous
    50/200 baseline while retaining a long-term trend filter.
    
    Args:
        ticker: Stock ticker to backtest.
        period: Historical period (e.g., '5y', '1y', 'max').
        snapshots: Optional point-in-time snapshot JSON file.
        fast_window: Number of days for the fast moving average.
        slow_window: Number of days for the slow moving average.
        
    Returns:
        Dictionary with backtest results:
        - strategy_return: Total return of strategy
        - benchmark_return: Total return of buy-and-hold
        - cagr: Compound annual growth rate
        - max_drawdown: Maximum drawdown
        - sharpe: Sharpe ratio
        - observations: Number of trading days
        - trade_count: Number of position transitions
        
    Raises:
        ValueError: If no historical data available.
    """
    try:
        df = yf.Ticker(ticker).history(period=period, auto_adjust=True)
    except Exception as e:
        raise ValueError(f"Failed to fetch backtest data for {ticker}: {e}")
    
    if df.empty:
        raise ValueError(f"No history available for {ticker} in period {period}")
    
    close = df["Close"].dropna()
    
    if fast_window <= 0 or slow_window <= fast_window:
        raise ValueError("Moving-average windows must be positive and slow > fast")
    if len(close) < slow_window:
        raise ValueError(
            f"Insufficient data for backtest (need {slow_window}+ days, "
            f"got {len(close)})"
        )
    
    # Calculate moving averages
    fast_average = close.rolling(fast_window).mean()
    slow_average = close.rolling(slow_window).mean()
    
    # Use point-in-time fundamental signals when supplied; otherwise use MA.
    if snapshots:
        snapshot_history = load_snapshot_history(snapshots)
        dated_snapshots = sorted(
            (pd.Timestamp(key), value) for key, value in snapshot_history.items()
        )
        positions = []
        for index in range(len(close)):
            current_date = pd.Timestamp(close.index[index]).tz_localize(None)
            available = [item for item in dated_snapshots if item[0] <= current_date]
            if not available:
                positions.append(0)
                continue
            snapshot = available[-1][1]
            momentum = momentum_score(close.iloc[:index + 1])
            score, _ = master_score(snapshot, summarize(snapshot), momentum)
            positions.append(int(signal(score) == "BUY"))
        strategy_signal = pd.Series(positions, index=close.index).shift(1).fillna(0)
    else:
        strategy_signal = (fast_average > slow_average).astype(int).shift(1).fillna(0)
    
    # Calculate daily returns
    daily_returns = close.pct_change().fillna(0)
    
    # Strategy returns (only when signal is 1)
    strategy_returns = strategy_signal * daily_returns
    
    # Cumulative returns
    strategy_equity = (1 + strategy_returns).cumprod()
    benchmark_equity = (1 + daily_returns).cumprod()
    
    # Performance metrics
    years = max((close.index[-1] - close.index[0]).days / 365.25, 1 / 365.25)
    cagr = strategy_equity.iloc[-1] ** (1 / years) - 1
    max_drawdown = (strategy_equity / strategy_equity.cummax() - 1).min()
    volatility = strategy_returns.std() * np.sqrt(252)
    sharpe = (strategy_returns.mean() * 252 / volatility) if volatility > 0 else 0
    
    return {
        "ticker": ticker,
        "period": period,
        "fast_window": fast_window,
        "slow_window": slow_window,
        "strategy_return": float(strategy_equity.iloc[-1] - 1),
        "benchmark_return": float(benchmark_equity.iloc[-1] - 1),
        "cagr": float(cagr),
        "max_drawdown": float(max_drawdown),
        "sharpe": float(sharpe),
        "observations": int(len(close)),
        "trade_count": int(strategy_signal.diff().abs().fillna(0).sum()),
    }
