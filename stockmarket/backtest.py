import math

import numpy as np
import pandas as pd
import yfinance as yf


def _annualized_return(equity_curve):
    if len(equity_curve) < 2:
        return 0.0

    start = float(equity_curve.iloc[0])
    end = float(equity_curve.iloc[-1])

    if start <= 0 or end <= 0:
        return 0.0

    days = (equity_curve.index[-1] - equity_curve.index[0]).days

    if days <= 0:
        return 0.0

    years = days / 365.25

    return (end / start) ** (1.0 / years) - 1.0


def _max_drawdown(equity_curve):
    if equity_curve.empty:
        return 0.0

    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1.0

    return float(drawdown.min())


def _sharpe_ratio(equity_curve):
    returns = equity_curve.pct_change().dropna()

    if len(returns) < 2:
        return 0.0

    volatility = returns.std()

    if volatility == 0 or not math.isfinite(volatility):
        return 0.0

    return float(
        np.sqrt(252.0)
        * returns.mean()
        / volatility
    )


def moving_average_backtest(
    ticker,
    period="5y",
    starting_cash=100_000.0,
):
    """
    Simple moving-average crossover benchmark.

    IMPORTANT:
    This is a benchmark strategy, NOT a backtest of the full
    StockMarket Robot valuation model.

    Strategy:
        BUY when 50-day MA > 200-day MA.
        HOLD while the condition remains true.
        Otherwise stay in cash.

    Signals are shifted by one trading day so that today's closing
    price cannot be used to pretend we traded at that same close.
    """

    ticker_obj = yf.Ticker(ticker)

    df = ticker_obj.history(
        period=period,
        auto_adjust=True,
    )

    if df.empty:
        raise ValueError(
            f"No historical data available for {ticker}"
        )

    if "Close" not in df.columns:
        raise ValueError(
            f"Historical data for {ticker} has no Close column"
        )

    close = df["Close"].dropna().astype(float)

    if len(close) < 210:
        raise ValueError(
            f"Not enough historical data for {ticker}; "
            f"need at least 210 trading days."
        )

    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()

    # The raw strategy signal is based on the closing price.
    raw_signal = (ma50 > ma200).astype(float)

    # Shift the signal one trading day.
    #
    # This prevents the backtest from seeing today's close and then
    # magically buying at today's close.
    position = raw_signal.shift(1).fillna(0.0)

    daily_returns = close.pct_change().fillna(0.0)

    strategy_returns = position * daily_returns

    equity_curve = (
        starting_cash
        * (1.0 + strategy_returns).cumprod()
    )

    benchmark_curve = (
        starting_cash
        * (1.0 + daily_returns).cumprod()
    )

    cagr = _annualized_return(equity_curve)
    max_drawdown = _max_drawdown(equity_curve)
    sharpe = _sharpe_ratio(equity_curve)

    benchmark_cagr = _annualized_return(benchmark_curve)
    benchmark_drawdown = _max_drawdown(benchmark_curve)

    return {
        "ticker": ticker,
        "strategy": "50/200 moving-average crossover",
        "period": period,
        "starting_cash": float(starting_cash),
        "ending_value": float(equity_curve.iloc[-1]),
        "cagr": float(cagr),
        "max_drawdown": float(max_drawdown),
        "sharpe": float(sharpe),
        "buy_and_hold_ending_value": float(
            benchmark_curve.iloc[-1]
        ),
        "buy_and_hold_cagr": float(benchmark_cagr),
        "buy_and_hold_max_drawdown": float(
            benchmark_drawdown
        ),
    }
