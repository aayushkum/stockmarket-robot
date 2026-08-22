"""Data fetching and snapshot collection from yfinance."""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import threading
import time
from typing import Callable, Optional, TypeVar
import numpy as np
import pandas as pd
import yfinance as yf
from .config import Settings

T = TypeVar("T")


class _RequestLimiter:
    """Serialize requests and enforce a minimum interval between them."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_request = 0.0

    def wait(self, interval: float) -> None:
        """Wait until the next request is allowed."""
        if interval <= 0:
            return
        with self._lock:
            elapsed = time.monotonic() - self._last_request
            if elapsed < interval:
                time.sleep(interval - elapsed)
            self._last_request = time.monotonic()


_REQUEST_LIMITER = _RequestLimiter()


def _request(operation: Callable[[], T], settings: Optional[Settings],
             description: str) -> T:
    """Run a yfinance operation with pacing and bounded exponential backoff."""
    attempts = max(0, settings.max_retries) + 1 if settings else 1
    for attempt in range(attempts):
        if settings:
            _REQUEST_LIMITER.wait(settings.request_delay_seconds)
        try:
            return operation()
        except Exception as error:
            if attempt == attempts - 1:
                raise ValueError(f"Failed to fetch {description}: {error}") from error
            if settings:
                time.sleep(max(0, settings.retry_backoff_seconds) * (2 ** attempt))
    raise RuntimeError("Request loop exited unexpectedly")


@dataclass
class Snapshot:
    """Financial data snapshot for a single stock.
    
    Attributes:
        ticker: Stock ticker symbol.
        price: Current stock price.
        eps: Trailing earnings per share.
        forward_eps: Forward earnings per share.
        revenue: Total annual revenue.
        free_cash_flow: Annual free cash flow.
        shares: Shares outstanding.
        beta: Stock beta (volatility relative to market).
        pe: Trailing price-to-earnings ratio.
        forward_pe: Forward P/E ratio.
        profit_margin: Net profit margin.
        operating_margin: Operating profit margin.
        return_on_equity: Return on equity.
        revenue_growth: Annual revenue growth rate.
        earnings_growth: Annual earnings growth rate.
        debt_to_equity: Debt-to-equity ratio.
        current_ratio: Current ratio (current assets / current liabilities).
        market_cap: Total market capitalization.
        sector: Business sector.
    """
    ticker: str
    price: float
    eps: Optional[float]
    forward_eps: Optional[float]
    revenue: Optional[float]
    free_cash_flow: Optional[float]
    shares: Optional[float]
    beta: Optional[float]
    pe: Optional[float]
    forward_pe: Optional[float]
    profit_margin: Optional[float]
    operating_margin: Optional[float]
    return_on_equity: Optional[float]
    revenue_growth: Optional[float]
    earnings_growth: Optional[float]
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    market_cap: Optional[float]
    sector: str
    
    def to_dict(self) -> dict:
        """Convert snapshot to dictionary."""
        return asdict(self)


def num(value) -> Optional[float]:
    """Convert value to float, returning None if invalid or non-finite.
    
    Args:
        value: Value to convert.
        
    Returns:
        Float value if valid and finite, None otherwise.
    """
    try:
        num_val = float(value)
        return num_val if np.isfinite(num_val) else None
    except (TypeError, ValueError):
        return None


def fetch_snapshot(ticker: str, settings: Optional[Settings] = None) -> Snapshot:
    """Fetch current financial snapshot for a ticker.
    
    Args:
        ticker: Stock ticker symbol.
        
    Returns:
        Snapshot with current financial data.
        
    Raises:
        ValueError: If current price is unavailable or non-positive.
    """
    cache_path = None
    if settings is not None and settings.cache_hours > 0:
        cache_path = Path(settings.db_path).parent / "cache" / f"{ticker}.json"
        if cache_path.exists():
            try:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
                fetched_at = datetime.fromisoformat(cached["fetched_at"])
                if datetime.now(timezone.utc) - fetched_at < timedelta(hours=settings.cache_hours):
                    return Snapshot(**cached["snapshot"])
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                pass

    def fetch() -> tuple[dict, dict]:
        ticker_obj = yf.Ticker(ticker)
        return ticker_obj.info, ticker_obj.fast_info

    info, fast = _request(fetch, settings, f"data for {ticker}")
    
    # Prioritize fast_info for price, fall back to info
    price = num(fast.get("lastPrice")) or num(info.get("currentPrice"))
    if not price or price <= 0:
        raise ValueError(f"Invalid price for {ticker}: {price}")
    
    snapshot = Snapshot(
        ticker=ticker,
        price=price,
        eps=num(info.get("trailingEps")),
        forward_eps=num(info.get("forwardEps")),
        revenue=num(info.get("totalRevenue")),
        free_cash_flow=num(info.get("freeCashflow")),
        shares=num(info.get("sharesOutstanding")),
        beta=num(info.get("beta")),
        pe=num(info.get("trailingPE")),
        forward_pe=num(info.get("forwardPE")),
        profit_margin=num(info.get("profitMargins")),
        operating_margin=num(info.get("operatingMargins")),
        return_on_equity=num(info.get("returnOnEquity")),
        revenue_growth=num(info.get("revenueGrowth")),
        earnings_growth=num(info.get("earningsGrowth")),
        debt_to_equity=num(info.get("debtToEquity")),
        current_ratio=num(info.get("currentRatio")),
        market_cap=num(info.get("marketCap")),
        sector=info.get("sector") or "Unknown"
    )
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "snapshot": snapshot.to_dict(),
        }), encoding="utf-8")
    return snapshot


def price_history(ticker: str, period: str = "1y",
                  settings: Optional[Settings] = None) -> pd.DataFrame:
    """Fetch historical price data for a ticker.
    
    Args:
        ticker: Stock ticker symbol.
        period: Historical period (e.g., '1y', '5y', 'max').
        
    Returns:
        DataFrame with OHLCV data, auto-adjusted for splits/dividends.
        
    Raises:
        ValueError: If no price history is available.
    """
    cache_path = None
    if settings is not None and settings.cache_hours > 0:
        cache_path = (Path(settings.db_path).parent / "cache" /
                      f"{ticker}_{period}_history.json")
        if cache_path.exists():
            try:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
                fetched_at = datetime.fromisoformat(cached["fetched_at"])
                if datetime.now(timezone.utc) - fetched_at < timedelta(hours=settings.cache_hours):
                    return pd.read_json(cached["data"], orient="split")
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                pass

    df = _request(
        lambda: yf.Ticker(ticker).history(period=period, auto_adjust=True),
        settings,
        f"price history for {ticker}",
    )
    
    if df.empty:
        raise ValueError(f"No price history available for {ticker} in period {period}")
    
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "data": df.to_json(orient="split", date_format="iso"),
        }), encoding="utf-8")
    return df
