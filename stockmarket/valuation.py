"""Valuation models for stock fair value estimation."""
from dataclasses import dataclass, asdict
import math
from typing import Optional, List

from .data import Snapshot


@dataclass
class ValuationResult:
    """Result of a single valuation model.
    
    Attributes:
        model: Name of the valuation model.
        fair_value: Estimated fair value per share, or None if unavailable.
        note: Human-readable explanation of the calculation.
    """
    model: str
    fair_value: Optional[float]
    note: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ValuationSummary:
    """Summary of all valuation estimates.
    
    Attributes:
        estimates: List of individual model results.
        fair_value: Arithmetic mean of valid estimates, or None if all invalid.
        upside: Potential upside as (fair_value / current_price - 1), or None.
    """
    estimates: List[ValuationResult]
    fair_value: Optional[float]
    upside: Optional[float]
    
    def to_dict(self) -> dict:
        """Convert to dictionary with nested estimate dicts."""
        return {
            "estimates": [x.to_dict() for x in self.estimates],
            "fair_value": self.fair_value,
            "upside": self.upside
        }


def earnings_multiple(snapshot: Snapshot) -> ValuationResult:
    """Estimate fair value using forward earnings and normalized P/E ratio.
    
    Uses forward EPS and adjusts P/E based on earnings growth.
    
    Args:
        snapshot: Financial snapshot data.
        
    Returns:
        ValuationResult with fair value or error message.
    """
    if not snapshot.forward_eps or snapshot.forward_eps <= 0:
        return ValuationResult(
            "earnings_multiple",
            None,
            "Forward EPS unavailable/non-positive"
        )
    
    growth = snapshot.earnings_growth or 0.05
    pe = min(25, max(10, 15 + growth * 100 * 0.35))
    fair_value = snapshot.forward_eps * pe
    return ValuationResult(
        "earnings_multiple",
        fair_value,
        f"Forward EPS x normalized P/E {pe:.1f}"
    )


def revenue_multiple(snapshot: Snapshot) -> ValuationResult:
    """Estimate fair value using revenue per share and P/S ratio.
    
    Args:
        snapshot: Financial snapshot data.
        
    Returns:
        ValuationResult with fair value or error message.
    """
    if (not snapshot.revenue or not snapshot.shares or
            snapshot.revenue <= 0 or snapshot.shares <= 0):
        return ValuationResult(
            "revenue_multiple",
            None,
            "Revenue/shares unavailable"
        )
    
    growth = snapshot.revenue_growth or 0.05
    price_to_sales = min(8, max(0.8, 2 + growth * 100 * 0.06))
    fair_value = (snapshot.revenue / snapshot.shares) * price_to_sales
    return ValuationResult(
        "revenue_multiple",
        fair_value,
        f"Revenue/share x P/S {price_to_sales:.2f}"
    )


def fcf_multiple(snapshot: Snapshot) -> ValuationResult:
    """Estimate fair value using free cash flow per share.
    
    Args:
        snapshot: Financial snapshot data.
        
    Returns:
        ValuationResult with fair value or error message.
    """
    if (not snapshot.free_cash_flow or not snapshot.shares or
            snapshot.free_cash_flow <= 0 or snapshot.shares <= 0):
        return ValuationResult(
            "fcf_multiple",
            None,
            "FCF/shares unavailable"
        )
    
    growth = snapshot.earnings_growth or snapshot.revenue_growth or 0.05
    multiple = min(30, max(10, 18 + growth * 100 * 0.4))
    fair_value = (snapshot.free_cash_flow / snapshot.shares) * multiple
    return ValuationResult(
        "fcf_multiple",
        fair_value,
        f"FCF/share x multiple {multiple:.1f}"
    )


def historical_pe(snapshot: Snapshot) -> ValuationResult:
    """Estimate fair value using trailing EPS and normalized P/E of 18.
    
    Args:
        snapshot: Financial snapshot data.
        
    Returns:
        ValuationResult with fair value or error message.
    """
    if not snapshot.eps or snapshot.eps <= 0:
        return ValuationResult(
            "historical_pe",
            None,
            "EPS unavailable/non-positive"
        )
    
    return ValuationResult(
        "historical_pe",
        snapshot.eps * 18,
        "Normalized long-run P/E proxy of 18"
    )


def dcf_proxy(snapshot: Snapshot) -> ValuationResult:
    """Estimate fair value using 5-year discounted cash flow model.
    
    Calculates present value of projected FCF over 5 years plus terminal value.
    
    Args:
        snapshot: Financial snapshot data.
        
    Returns:
        ValuationResult with fair value or error message.
    """
    if (not snapshot.free_cash_flow or not snapshot.shares or
            snapshot.free_cash_flow <= 0 or snapshot.shares <= 0):
        return ValuationResult(
            "dcf",
            None,
            "FCF/shares unavailable"
        )
    
    fcf_per_share = snapshot.free_cash_flow / snapshot.shares
    growth = min(0.10, max(0.02, snapshot.revenue_growth or
                                 snapshot.earnings_growth or 0.05))
    discount_rate = 0.09 + max(0, (snapshot.beta or 1) - 1) * 0.02
    terminal_growth = min(0.035, growth)
    
    # Project FCF over 5 years and discount to present
    value = 0
    for year in range(1, 6):
        fcf_per_share *= (1 + growth)
        value += fcf_per_share / ((1 + discount_rate) ** year)
    
    # Add terminal value
    terminal_value = (fcf_per_share * (1 + terminal_growth) /
                     max(0.02, discount_rate - terminal_growth))
    value += terminal_value / ((1 + discount_rate) ** 5)
    
    return ValuationResult(
        "dcf",
        value,
        f"5-year DCF proxy; growth {growth:.1%}, discount {discount_rate:.1%}"
    )


def summarize(snapshot: Snapshot) -> ValuationSummary:
    """Summarize valuation using all models and calculate arithmetic mean.
    
    Args:
        snapshot: Financial snapshot data.
        
    Returns:
        ValuationSummary with all model estimates and mean fair value.
    """
    models = [dcf_proxy, earnings_multiple, fcf_multiple, revenue_multiple, historical_pe]
    estimates = [model(snapshot) for model in models]
    
    # Filter to valid, finite, positive values only
    valid_values = [
        x.fair_value for x in estimates
        if x.fair_value is not None and math.isfinite(x.fair_value) and x.fair_value > 0
    ]
    
    fair_value = sum(valid_values) / len(valid_values) if valid_values else None
    upside = (fair_value / snapshot.price - 1) if fair_value else None
    
    return ValuationSummary(estimates, fair_value, upside)
