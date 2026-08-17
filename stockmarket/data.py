from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf


@dataclass
class Snapshot:
    ticker: str
    price: float

    # Per-share fundamentals
    eps: Optional[float]
    forward_eps: Optional[float]
    free_cash_flow_per_share: Optional[float]

    # Company-level fundamentals
    revenue: Optional[float]
    free_cash_flow: Optional[float]
    shares: Optional[float]
    market_cap: Optional[float]

    # Valuation / risk
    beta: Optional[float]
    pe: Optional[float]
    forward_pe: Optional[float]

    # Profitability
    profit_margin: Optional[float]
    operating_margin: Optional[float]
    return_on_equity: Optional[float]

    # Growth
    revenue_growth: Optional[float]
    earnings_growth: Optional[float]

    # Balance sheet
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]

    sector: str

    def to_dict(self):
        return asdict(self)


def num(x):
    try:
        value = float(x)

        if np.isfinite(value):
            return value

        return None

    except (TypeError, ValueError):
        return None


def fetch_snapshot(ticker):
    t = yf.Ticker(ticker)

    info = t.info
    fast = t.fast_info

    price = (
        num(fast.get("lastPrice"))
        or num(info.get("currentPrice"))
    )

    if price is None or price <= 0:
        raise ValueError(
            f"No current price available for {ticker}"
        )

    eps = num(info.get("trailingEps"))
    forward_eps = num(info.get("forwardEps"))

    revenue = num(info.get("totalRevenue"))
    free_cash_flow = num(info.get("freeCashflow"))
    shares = num(info.get("sharesOutstanding"))

    # ------------------------------------------------------------
    # FCF PER SHARE
    # ------------------------------------------------------------

    free_cash_flow_per_share = None

    if (
        free_cash_flow is not None
        and shares is not None
        and shares > 0
    ):
        free_cash_flow_per_share = (
            free_cash_flow / shares
        )

    return Snapshot(
        ticker=ticker,
        price=price,

        # Per-share fundamentals
        eps=eps,
        forward_eps=forward_eps,
        free_cash_flow_per_share=free_cash_flow_per_share,

        # Company-level fundamentals
        revenue=revenue,
        free_cash_flow=free_cash_flow,
        shares=shares,
        market_cap=num(info.get("marketCap")),

        # Valuation / risk
        beta=num(info.get("beta")),
        pe=num(info.get("trailingPE")),
        forward_pe=num(info.get("forwardPE")),

        # Profitability
        profit_margin=num(info.get("profitMargins")),
        operating_margin=num(info.get("operatingMargins")),
        return_on_equity=num(info.get("returnOnEquity")),

        # Growth
        revenue_growth=num(info.get("revenueGrowth")),
        earnings_growth=num(info.get("earningsGrowth")),

        # Balance sheet
        debt_to_equity=num(info.get("debtToEquity")),
        current_ratio=num(info.get("currentRatio")),

        sector=info.get("sector") or "Unknown",
    )


def price_history(ticker, period="1y"):
    """
    Download historical price data.
    """

    df = yf.Ticker(ticker).history(
        period=period,
        auto_adjust=True,
    )

    if df.empty:
        raise ValueError(
            f"No price history for {ticker}"
        )

    return df
