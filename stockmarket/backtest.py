"""Historical backtest of moving average strategy."""
from typing import Dict, Any
import numpy as np
import yfinance as yf


def moving_average_backtest(ticker: str, period: str = "5y") -> Dict[str, Any]:
    """Backtest a simple 50/200 moving average crossover strategy.
    
    Strategy:
    - BUY: 50-day MA > 200-day MA
    - SELL: 50-day MA < 200-day MA
    
    Args:
        ticker: Stock ticker to backtest.
        period: Historical period (e.g., '5y', '1y', 'max').
        
    Returns:
        Dictionary with backtest results:
        - strategy_return: Total return of strategy
        - benchmark_return: Total return of buy-and-hold
        - cagr: Compound annual growth rate
        - max_drawdown: Maximum drawdown
        - sharpe: Sharpe ratio
        - observations: Number of trading days
        
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
    
    if len(close) < 200:
        raise ValueError(f"Insufficient data for backtest (need 200+ days, got {len(close)})")
    
    # Calculate moving averages
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()
    
    # Generate signals (1 = long, 0 = cash)
    signal = (ma50 > ma200).astype(int).shift(1).fillna(0)
    
    # Calculate daily returns
    daily_returns = close.pct_change().fillna(0)
    
    # Strategy returns (only when signal is 1)
    strategy_returns = signal * daily_returns
    
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
        "strategy_return": float(strategy_equity.iloc[-1] - 1),
        "benchmark_return": float(benchmark_equity.iloc[-1] - 1),
        "cagr": float(cagr),
        "max_drawdown": float(max_drawdown),
        "sharpe": float(sharpe),
        "observations": int(len(close))
    }
