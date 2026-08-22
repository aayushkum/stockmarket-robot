"""Main analysis pipeline combining all valuation and scoring models."""
from datetime import datetime, timezone
from typing import Dict, Any

from .data import fetch_snapshot, price_history
from .valuation import summarize
from .scoring import master_score, signal, momentum_score
from .config import Settings


def analyze_snapshot(ticker: str, snapshot: Any, history: Any,
                     settings: Settings | None = None) -> Dict[str, Any]:
    """Analyze already-fetched data using configured signal thresholds."""
    settings = settings or Settings()
    valuation = summarize(snapshot)
    momentum = momentum_score(history["Close"])
    score, components = master_score(snapshot, valuation, momentum)

    return {
        "ticker": ticker,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "price": snapshot.price,
        "sector": snapshot.sector,
        "fair_value": valuation.fair_value,
        "upside": valuation.upside,
        "valuation": valuation.to_dict(),
        "master_score": score,
        "components": components,
        "signal": signal(score, settings.min_score_to_buy, settings.sell_score),
        "snapshot": snapshot.to_dict(),
    }


def analyze(ticker: str, settings: Settings | None = None) -> Dict[str, Any]:
    """Perform complete analysis on a stock ticker.
    
    Combines current financial data, valuation models, and price momentum
    to produce a comprehensive investment signal.
    
    Args:
        ticker: Stock ticker symbol.
        
    Returns:
        Dictionary containing:
        - ticker: Stock symbol
        - analyzed_at: ISO timestamp
        - price: Current price
        - sector: Business sector
        - fair_value: Estimated fair value
        - upside: Potential upside percentage
        - valuation: Detailed valuation summary
        - master_score: Overall score 0-100
        - components: Individual component scores
        - signal: BUY/HOLD/SELL
        - snapshot: Complete financial snapshot
        
    Raises:
        ValueError: If stock data unavailable.
    """
    settings = settings or Settings()
    snapshot = fetch_snapshot(ticker, settings)
    history = price_history(ticker, "1y", settings)
    return analyze_snapshot(ticker, snapshot, history, settings)
