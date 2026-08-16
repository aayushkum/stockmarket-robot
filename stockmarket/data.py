from dataclasses import dataclass, asdict
from typing import Optional
import numpy as np
import pandas as pd
import yfinance as yf

@dataclass
class Snapshot:
    ticker: str; price: float; eps: Optional[float]; forward_eps: Optional[float]
    revenue: Optional[float]; free_cash_flow: Optional[float]; shares: Optional[float]
    beta: Optional[float]; pe: Optional[float]; forward_pe: Optional[float]
    profit_margin: Optional[float]; operating_margin: Optional[float]; return_on_equity: Optional[float]
    revenue_growth: Optional[float]; earnings_growth: Optional[float]; debt_to_equity: Optional[float]
    current_ratio: Optional[float]; market_cap: Optional[float]; sector: str
    def to_dict(self): return asdict(self)

def num(x):
    try:
        v=float(x)
        return v if np.isfinite(v) else None
    except (TypeError, ValueError): return None

def fetch_snapshot(ticker):
    t=yf.Ticker(ticker); info=t.info; fast=t.fast_info
    price=num(fast.get("lastPrice")) or num(info.get("currentPrice"))
    if not price or price<=0: raise ValueError(f"No current price available for {ticker}")
    return Snapshot(ticker, price, num(info.get("trailingEps")), num(info.get("forwardEps")),
        num(info.get("totalRevenue")), num(info.get("freeCashflow")), num(info.get("sharesOutstanding")),
        num(info.get("beta")), num(info.get("trailingPE")), num(info.get("forwardPE")),
        num(info.get("profitMargins")), num(info.get("operatingMargins")), num(info.get("returnOnEquity")),
        num(info.get("revenueGrowth")), num(info.get("earningsGrowth")), num(info.get("debtToEquity")),
        num(info.get("currentRatio")), num(info.get("marketCap")), info.get("sector") or "Unknown")

def price_history(ticker, period="1y"):
    df=yf.Ticker(ticker).history(period=period, auto_adjust=True)
    if df.empty: raise ValueError(f"No price history for {ticker}")
    return df
