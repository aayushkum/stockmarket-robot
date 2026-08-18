"""Main analysis pipeline combining all valuation and scoring models."""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd

from .data import Snapshot, fetch_snapshot, price_history
from .scoring import master_score, momentum_score, signal
from .valuation import ValuationSummary, summarize


def analyze_snapshot(
    snapshot: Snapshot,
    history: pd.Series,
    analyzed_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    # Analyze a point-in-time snapshot using only price history available then.
    if not isinstance(snapshot, Snapshot):
        raise TypeError("snapshot must be a Snapshot")

    if not isinstance(history, pd.Series):
        raise TypeError("history must be a pandas Series")

    if history.empty:
        raise ValueError("history cannot be empty")

    history = pd.to_numeric(history, errors="coerce").dropna()

    if history.empty:
        raise ValueError("history contains no valid prices")

    valuation: ValuationSummary = summarize(snapshot)
    momentum = momentum_score(history)

    score, components = master_score(
        snapshot,
        valuation,
        momentum,
    )

    timestamp = analyzed_at or datetime.now(timezone.utc)

    return {
        "ticker": snapshot.ticker,
        "analyzed_at": timestamp.isoformat(),
        "price": snapshot.price,
        "sector": snapshot.sector,
        "fair_value": valuation.fair_value,
        "upside": valuation.upside,
        "valuation": valuation.to_dict(),
        "master_score": score,
        "components": components,
        "signal": signal(score),
        "snapshot": snapshot.to_dict(),
    }


def analyze(ticker: str) -> Dict[str, Any]:
    """Perform a live analysis using the latest available data."""
    snapshot = fetch_snapshot(ticker)
    history = price_history(ticker, "1y")

    return analyze_snapshot(
        snapshot,
        history["Close"],
    )
