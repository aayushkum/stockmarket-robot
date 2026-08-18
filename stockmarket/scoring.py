import math
from typing import Optional

def clamp(x: Optional[float], lo: float = 0, hi: float = 100) -> float:
    """Clamp a value between lo and hi, handling None/NaN/inf."""
    if x is None or not math.isfinite(x):
        return (lo + hi) / 2
    return max(lo, min(hi, x))

def valuation_score(v) -> float:
    """Score based on valuation upside."""
    return 50 if v.upside is None else clamp(50+v.upside*100)

def growth_score(s) -> float:
    """Score based on revenue and earnings growth rates.
    
    Args:
        s: Snapshot with growth data.
        
    Returns:
        Score 0-100 based on growth metrics.
    """
    growth_rates = [x for x in (s.revenue_growth, s.earnings_growth) if x is not None]
    if not growth_rates:
        return 50
    avg_growth = sum(growth_rates) / len(growth_rates)
    return clamp(50 + avg_growth * 150)

def quality_score(s) -> float:
    """Score based on profitability metrics.
    
    Args:
        s: Snapshot with profitability data.
        
    Returns:
        Score 0-100 based on profit margins and ROE.
    """
    scores = []
    if s.profit_margin is not None:
        scores.append(clamp(50 + s.profit_margin * 200))
    if s.operating_margin is not None:
        scores.append(clamp(50 + s.operating_margin * 150))
    if s.return_on_equity is not None:
        scores.append(clamp(50 + s.return_on_equity * 100))
    
    return sum(scores) / len(scores) if scores else 50

def risk_score(s) -> float:
    """Score based on financial risk metrics.
    
    Args:
        s: Snapshot with risk data.
        
    Returns:
        Score 0-100, higher is lower risk.
    """
    scores = []
    if s.beta is not None:
        # Higher beta = higher volatility = lower score
        scores.append(clamp(100 - max(0, s.beta - 1) * 35))
    if s.debt_to_equity is not None:
        # Higher debt = higher risk = lower score
        scores.append(clamp(100 - max(0, s.debt_to_equity - 50) * 0.5))
    if s.current_ratio is not None:
        # Higher current ratio = better liquidity = higher score
        scores.append(clamp(40 + s.current_ratio * 30))
    
    return sum(scores) / len(scores) if scores else 50

def momentum_score(series) -> float:
    """Score based on price momentum (50/200 day moving averages).
    
    Args:
        series: pandas Series with close prices.
        
    Returns:
        Score 0-100, higher for uptrend.
    """
    if len(series) < 200:
        return 50
    
    now = float(series.iloc[-1])
    ma50 = float(series.tail(50).mean())
    ma200 = float(series.tail(200).mean())
    
    # Score improves with price above moving averages
    uptrend_50 = (now / ma50 - 1) * 150
    uptrend_200 = (now / ma200 - 1) * 150
    
    return clamp(50 + uptrend_50 + uptrend_200)

def master_score(s, v, momentum: float = 50) -> tuple:
    """Calculate master score from all component scores.
    
    Args:
        s: Snapshot with financial data.
        v: ValuationSummary with valuation results.
        momentum: Momentum score (0-100).
        
    Returns:
        Tuple of (master_score, components_dict).
    """
    components = {
        "valuation": valuation_score(v),
        "growth": growth_score(s),
        "quality": quality_score(s),
        "momentum": momentum,
        "risk": risk_score(s)
    }
    
    weights = {
        "valuation": 0.30,
        "growth": 0.20,
        "quality": 0.20,
        "momentum": 0.15,
        "risk": 0.15
    }
    
    master = sum(components[k] * weights[k] for k in weights)
    return master, components

def signal(score: float) -> str:
    """Convert master score to trading signal.
    
    Args:
        score: Master score 0-100.
        
    Returns:
        'BUY' if score >= 70, 'SELL' if score <= 40, else 'HOLD'.
    """
    if score >= 70:
        return "BUY"
    elif score <= 40:
        return "SELL"
    else:
        return "HOLD"
