"""Data fetching and snapshot collection from yfinance."""
from dataclasses import dataclass, asdict
from typing import Optional
import numpy as np
import pandas as pd
import yfinance as yf


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


def fetch_snapshot(ticker: str) -> Snapshot:
    """Fetch current financial snapshot for a ticker.
    
    Args:
        ticker: Stock ticker symbol.
        
    Returns:
        Snapshot with current financial data.
        
    Raises:
        ValueError: If current price is unavailable or non-positive.
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        fast = ticker_obj.fast_info
    except Exception as e:
        raise ValueError(f"Failed to fetch data for {ticker}: {e}")
    
    # Prioritize fast_info for price, fall back to info
    price = num(fast.get("lastPrice")) or num(info.get("currentPrice"))
    if not price or price <= 0:
        raise ValueError(f"Invalid price for {ticker}: {price}")
    
    return Snapshot(
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


def price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch historical price data for a ticker.
    
    Args:
        ticker: Stock ticker symbol.
        period: Historical period (e.g., '1y', '5y', 'max').
        
    Returns:
        DataFrame with OHLCV data, auto-adjusted for splits/dividends.
        
    Raises:
        ValueError: If no price history is available.
    """
    try:
        df = yf.Ticker(ticker).history(period=period, auto_adjust=True)
    except Exception as e:
        raise ValueError(f"Failed to fetch price history for {ticker}: {e}")
    
    if df.empty:
        raise ValueError(f"No price history available for {ticker} in period {period}")
    
    return df
