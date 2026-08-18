# Point-in-time backtesting for the stock analysis decision engine.

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import pandas as pd

from .analyzer import analyze_snapshot
from .data import Snapshot


@dataclass(frozen=True)
class BacktestConfig:
    """Configuration for the portfolio simulation."""

    initial_capital: float = 10_000.0
    transaction_cost_bps: float = 10.0
    min_history_days: int = 200


def load_snapshot_history(
    path: str | Path,
) -> Dict[pd.Timestamp, Snapshot]:
    """Load point-in-time snapshots from a JSON file.

    Expected format:

        {
          "2023-01-03": {
            "ticker": "AAPL",
            "price": 125.07,
            "eps": 6.11,
            ...
          },
          "2023-02-01": {
            ...
          }
        }
    """
    file_path = Path(path)

    try:
        payload = json.loads(
            file_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Failed to read snapshot history: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError(
            "Snapshot history must be a JSON object keyed by date"
        )

    snapshots: Dict[pd.Timestamp, Snapshot] = {}

    for date_text, values in payload.items():

        if not isinstance(values, dict):
            raise ValueError(
                f"Snapshot for {date_text!r} must be an object"
            )

        try:
            date = pd.Timestamp(date_text).normalize()
        except Exception as exc:
            raise ValueError(
                f"Invalid snapshot date {date_text!r}"
            ) from exc

        try:
            snapshots[date] = Snapshot(**values)
        except TypeError as exc:
            raise ValueError(
                f"Invalid Snapshot fields for "
                f"{date_text!r}: {exc}"
            ) from exc

    return snapshots


def _validate_prices(prices: pd.DataFrame) -> pd.Series:
    """Validate and normalize historical closing prices."""

    if not isinstance(prices, pd.DataFrame):
        raise ValueError(
            "prices must be a DataFrame"
        )

    if "Close" not in prices.columns:
        raise ValueError(
            "prices must be a DataFrame containing "
            "a 'Close' column"
        )

    close = pd.to_numeric(
        prices["Close"],
        errors="coerce",
    ).dropna()

    close = close[close > 0]

    if close.empty:
        raise ValueError(
            "No valid closing prices available"
        )

    if not close.index.is_monotonic_increasing:
        close = close.sort_index()

    return close


def _snapshot_for_date(
    snapshots: Mapping,
    date: pd.Timestamp,
) -> Optional[Snapshot]:
    """Find the snapshot exactly matching the analysis date."""

    candidates = [
        date,
        date.normalize(),
    ]

    if hasattr(date, "date"):
        candidates.append(date.date())

    for candidate in candidates:
        snapshot = snapshots.get(candidate)

        if snapshot is not None:
            return snapshot

    return None


def backtest_with_snapshots(
    ticker: str,
    prices: pd.DataFrame,
    snapshots: Mapping,
    config: Optional[BacktestConfig] = None,
) -> Dict[str, Any]:
    """Backtest the actual robot using point-in-time snapshots.

    The decision on day *t* uses:

      1. fundamentals from the snapshot dated *t*;
      2. prices through *t* only.

    A BUY enters a long position.

    A SELL exits it.

    HOLD preserves the previous position.

    Any trade is executed at the close of *t*, and the resulting position
    earns the return from *t* to the next trading day.

    Missing snapshots are skipped rather than replaced with current data.
    """

    config = config or BacktestConfig()

    if config.initial_capital <= 0:
        raise ValueError(
            "initial_capital must be positive"
        )

    if config.transaction_cost_bps < 0:
        raise ValueError(
            "transaction_cost_bps cannot be negative"
        )

    if config.min_history_days < 1:
        raise ValueError(
            "min_history_days must be positive"
        )

    close = _validate_prices(prices)

    if len(close) < config.min_history_days + 1:
        raise ValueError(
            f"Insufficient data for backtest "
            f"(need at least "
            f"{config.min_history_days + 1} "
            f"valid prices, got {len(close)})"
        )

    equity = float(config.initial_capital)

    # 0 = cash
    # 1 = fully invested long
    position = 0

    equity_curve = []
    trades = []

    skipped = 0

    for i in range(
        config.min_history_days,
        len(close) - 1,
    ):

        date = close.index[i]
        next_date = close.index[i + 1]

        snapshot = _snapshot_for_date(
            snapshots,
            date,
        )

        # Never substitute current fundamentals.
        if snapshot is None:
            skipped += 1

            equity_curve.append(
                (date, equity, position)
            )

            continue

        if snapshot.ticker.upper() != ticker.upper():
            raise ValueError(
                f"Snapshot ticker "
                f"{snapshot.ticker!r} "
                f"does not match "
                f"{ticker!r}"
            )

        if snapshot.price <= 0:
            skipped += 1

            equity_curve.append(
                (date, equity, position)
            )

            continue

        # IMPORTANT:
        #
        # The historical price series ends at the current
        # backtest date. Therefore the decision cannot see
        # tomorrow's price.
        history = close.iloc[: i + 1]

        # This is the exact same decision engine used by
        # live analysis.
        analysis = analyze_snapshot(
            snapshot,
            history,
        )

        decision = analysis["signal"]

        # HOLD means maintain the existing position.
        target_position = position

        if decision == "BUY":
            target_position = 1

        elif decision == "SELL":
            target_position = 0

        # Execute trade at today's close.
        if target_position != position:

            cost = (
                equity
                * (config.transaction_cost_bps / 10_000)
            )

            equity -= cost

            trades.append(
                {
                    "date": date.isoformat(),
                    "signal": decision,
                    "position": target_position,
                    "transaction_cost": float(cost),
                }
            )

            position = target_position

        # The new position captures only the NEXT
        # day's return.
        daily_return = float(
            close.iloc[i + 1]
            / close.iloc[i]
            - 1
        )

        if position:
            equity *= 1 + daily_return

        equity_curve.append(
            (
                next_date,
                equity,
                position,
            )
        )

    if not equity_curve:
        raise ValueError(
            "No backtest observations were produced"
        )

    curve = pd.Series(
        [row[1] for row in equity_curve],
        index=pd.DatetimeIndex(
            [row[0] for row in equity_curve]
        ),
        dtype=float,
    )

    returns = curve.pct_change().fillna(0.0)

    # Buy-and-hold benchmark starting on the same
    # first day that the strategy starts recording returns.
    benchmark = (
        config.initial_capital
        * (
            close
            / close.iloc[config.min_history_days]
        )
    )

    benchmark = benchmark.loc[
        curve.index
    ].astype(float)

    years = max(
        (
            curve.index[-1]
            - curve.index[0]
        ).days / 365.25,
        1 / 365.25,
    )

    strategy_return = (
        curve.iloc[-1]
        / config.initial_capital
        - 1
    )

    benchmark_return = (
        benchmark.iloc[-1]
        / benchmark.iloc[0]
        - 1
    )

    cagr = (
        curve.iloc[-1]
        / config.initial_capital
    ) ** (1 / years) - 1

    drawdown = (
        curve
        / curve.cummax()
        - 1
    )

    volatility = (
        returns.std(ddof=1)
        * math.sqrt(252)
    )

    sharpe = (
        returns.mean()
        * 252
        / volatility
        if volatility > 0
        else 0.0
    )

    return {
        "ticker": ticker,
        "start_date": curve.index[0].isoformat(),
        "end_date": curve.index[-1].isoformat(),

        "initial_capital": float(
            config.initial_capital
        ),

        "final_equity": float(
            curve.iloc[-1]
        ),

        "strategy_return": float(
            strategy_return
        ),

        "benchmark_return": float(
            benchmark_return
        ),

        "cagr": float(cagr),

        "max_drawdown": float(
            drawdown.min()
        ),

        "sharpe": float(sharpe),

        "observations": int(
            len(curve)
        ),

        "trades": trades,

        "trade_count": len(trades),

        "skipped_observations": skipped,

        "equity_curve": {
            timestamp.isoformat(): float(value)
            for timestamp, value in curve.items()
        },
    }
