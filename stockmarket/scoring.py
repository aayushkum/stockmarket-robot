import math
import numpy as np


def clamp(value, low=0.0, high=100.0):
    if value is None:
        return 50.0

    try:
        value = float(value)
    except (TypeError, ValueError):
        return 50.0

    if not math.isfinite(value):
        return 50.0

    return max(low, min(high, value))


def _growth_score(value):
    if value is None:
        return 50.0

    try:
        value = float(value)
    except (TypeError, ValueError):
        return 50.0

    if not math.isfinite(value):
        return 50.0

    score = 50.0 + value * 200.0

    return clamp(score)


def valuation_score(upside):
    if upside is None:
        return 50.0

    try:
        upside = float(upside)
    except (TypeError, ValueError):
        return 50.0

    if not math.isfinite(upside):
        return 50.0
    score = 50.0 + upside * 150.0

    return clamp(score)


def quality_score(snapshot):
    scores = []

    if snapshot.roe is not None:
        try:
            roe = float(snapshot.roe)
            if math.isfinite(roe):
                scores.append(clamp(50.0 + roe * 100.0))
        except (TypeError, ValueError):
            pass

    if snapshot.profit_margin is not None:
        try:
            margin = float(snapshot.profit_margin)
            if math.isfinite(margin):
                scores.append(clamp(50.0 + margin * 200.0))
        except (TypeError, ValueError):
            pass

    if snapshot.operating_margin is not None:
        try:
            margin = float(snapshot.operating_margin)
            if math.isfinite(margin):
                scores.append(clamp(50.0 + margin * 150.0))
        except (TypeError, ValueError):
            pass

    if not scores:
        return 50.0

    return float(np.mean(scores))


def risk_score(snapshot):
    scores = []

    if snapshot.debt_to_equity is not None:
        try:
            de = float(snapshot.debt_to_equity)

            if math.isfinite(de):
                score = 80.0 - max(0.0, de - 50.0) * 0.35
                scores.append(clamp(score))
        except (TypeError, ValueError):
            pass

    if snapshot.current_ratio is not None:
        try:
            current_ratio = float(snapshot.current_ratio)

            if math.isfinite(current_ratio):
                score = 50.0 + (current_ratio - 1.0) * 20.0
                scores.append(clamp(score))
        except (TypeError, ValueError):
            pass

    if snapshot.beta is not None:
        try:
            beta = float(snapshot.beta)

            if math.isfinite(beta):
                score = 70.0 - abs(beta - 1.0) * 25.0
                scores.append(clamp(score))
        except (TypeError, ValueError):
            pass

    if not scores:
        return 50.0

    return float(np.mean(scores))


def momentum_score(close):
    if close is None or len(close) < 200:
        return 50.0

    series = close.dropna()

    if len(series) < 200:
        return 50.0

    now = float(series.iloc[-1])
    ma50 = float(series.iloc[-50:].mean())
    ma200 = float(series.iloc[-200:].mean())

    if now <= 0 or ma50 <= 0 or ma200 <= 0:
        return 50.0

    short_term = now / ma50 - 1.0
    long_term = now / ma200 - 1.0

    score = 50.0 + short_term * 100.0 + long_term * 100.0

    return clamp(score)


def master_score(snapshot, valuation, momentum):

    v = valuation_score(valuation.upside)

    earnings_growth = snapshot.earnings_growth
    revenue_growth = snapshot.revenue_growth

    growth_values = [
        x for x in (earnings_growth, revenue_growth)
        if x is not None and math.isfinite(float(x))
    ]

    if growth_values:
        growth = float(np.mean(growth_values))
        g = _growth_score(growth)
    else:
        g = 50.0

    q = quality_score(snapshot)
    m = clamp(momentum)
    r = risk_score(snapshot)

    score = (
        0.35 * v
        + 0.20 * g
        + 0.15 * q
        + 0.10 * m
        + 0.20 * r
    )

    components = {
        "valuation": round(v, 2),
        "growth": round(g, 2),
        "quality": round(q, 2),
        "momentum": round(m, 2),
        "risk": round(r, 2),
    }

    return round(clamp(score), 2), components


def signal(score):
    if score >= 75:
        return "BUY"

    if score <= 40:
        return "SELL"

    return "HOLD"
