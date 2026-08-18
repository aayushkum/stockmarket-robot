import math

import numpy as np
import pytest

from stockmarket.data import Snapshot
from stockmarket.scoring import (
    clamp,
    valuation_score,
    quality_score,
    risk_score,
    momentum_score,
    master_score,
    signal,
)


def make_snapshot(**overrides):
    """Create a test Snapshot with sensible defaults matching the actual Snapshot dataclass."""
    values = {
        "ticker": "TEST",
        "price": 100.0,
        "eps": 5.0,
        "forward_eps": 5.5,
        "revenue": 100_000_000_000.0,
        "free_cash_flow": 4_000_000_000.0,
        "shares": 1_000_000_000.0,
        "beta": 1.0,
        "pe": 20.0,
        "forward_pe": 18.18,
        "profit_margin": 0.20,
        "operating_margin": 0.25,
        "return_on_equity": 0.25,
        "revenue_growth": 0.10,
        "earnings_growth": 0.10,
        "debt_to_equity": 50.0,
        "current_ratio": 1.5,
        "market_cap": 100_000_000_000.0,
        "sector": "Technology",
    }

    values.update(overrides)

    return Snapshot(**values)


class FakeValuation:
    def __init__(self, upside):
        self.upside = upside


# ============================================================
# CLAMP
# ============================================================


def test_clamp_keeps_normal_values():
    assert clamp(50) == 50


def test_clamp_limits_high_values():
    assert clamp(150) == 100


def test_clamp_limits_low_values():
    assert clamp(-50) == 0


def test_clamp_handles_none():
    assert clamp(None) == 50


def test_clamp_handles_nan():
    assert clamp(float("nan")) == 50


def test_clamp_handles_infinity():
    assert clamp(float("inf")) == 50


# ============================================================
# VALUATION SCORE
# ============================================================


def test_valuation_score_is_neutral_at_zero_upside():
    score = valuation_score(FakeValuation(0.0))

    assert score == pytest.approx(50.0)


def test_positive_upside_improves_score():
    neutral = valuation_score(FakeValuation(0.0))
    positive = valuation_score(FakeValuation(0.20))

    assert positive > neutral


def test_negative_upside_reduces_score():
    neutral = valuation_score(FakeValuation(0.0))
    negative = valuation_score(FakeValuation(-0.20))

    assert negative < neutral


def test_valuation_score_is_bounded():
    for upside in [-10, -1, -0.5, 0, 0.5, 1, 10]:
        score = valuation_score(FakeValuation(upside))

        assert 0 <= score <= 100


def test_extreme_upside_does_not_exceed_100():
    assert valuation_score(FakeValuation(10.0)) == 100


def test_extreme_downside_does_not_go_below_zero():
    assert valuation_score(FakeValuation(-10.0)) == 0


def test_missing_upside_is_neutral():
    assert valuation_score(FakeValuation(None)) == 50


# ============================================================
# GROWTH / QUALITY
# ============================================================


def test_quality_score_is_neutral_with_missing_data():
    snapshot = make_snapshot(
        return_on_equity=None,
        profit_margin=None,
        operating_margin=None,
    )

    assert quality_score(snapshot) == 50


def test_better_profitability_improves_quality_score():
    weak = make_snapshot(
        return_on_equity=0.05,
        profit_margin=0.05,
        operating_margin=0.05,
    )

    strong = make_snapshot(
        return_on_equity=0.30,
        profit_margin=0.30,
        operating_margin=0.30,
    )

    assert quality_score(strong) > quality_score(weak)


def test_quality_score_is_bounded():
    snapshot = make_snapshot(
        return_on_equity=10.0,
        profit_margin=10.0,
        operating_margin=10.0,
    )

    score = quality_score(snapshot)

    assert 0 <= score <= 100


# ============================================================
# RISK
# ============================================================


def test_risk_score_is_neutral_without_data():
    snapshot = make_snapshot(
        debt_to_equity=None,
        current_ratio=None,
        beta=None,
    )

    assert risk_score(snapshot) == 50


def test_lower_debt_generally_improves_risk_score():
    low_debt = make_snapshot(
        debt_to_equity=20.0,
        current_ratio=1.5,
        beta=1.0,
    )

    high_debt = make_snapshot(
        debt_to_equity=300.0,
        current_ratio=1.5,
        beta=1.0,
    )

    assert risk_score(low_debt) > risk_score(high_debt)


def test_extreme_debt_cannot_make_risk_negative():
    snapshot = make_snapshot(
        debt_to_equity=10_000.0,
        current_ratio=1.5,
        beta=1.0,
    )

    score = risk_score(snapshot)

    assert score >= 0


def test_reasonable_beta_is_not_penalized_heavily():
    snapshot = make_snapshot(
        beta=1.0,
    )

    score = risk_score(snapshot)

    assert score > 50


# ============================================================
# MOMENTUM
# ============================================================


def test_momentum_is_neutral_with_insufficient_data():
    close = np.array([100.0] * 100)

    score = momentum_score(
        # pandas Series is expected by the implementation
        __import__("pandas").Series(close)
    )

    assert score == 50


def test_strong_uptrend_has_positive_momentum():
    import pandas as pd

    close = pd.Series(
        np.linspace(50.0, 150.0, 250)
    )

    score = momentum_score(close)

    assert score > 50


def test_strong_downtrend_has_negative_momentum():
    import pandas as pd

    close = pd.Series(
        np.linspace(150.0, 50.0, 250)
    )

    score = momentum_score(close)

    assert score < 50


def test_momentum_is_bounded():
    import pandas as pd

    close = pd.Series(
        np.linspace(1.0, 10_000.0, 250)
    )

    score = momentum_score(close)

    assert 0 <= score <= 100


# ============================================================
# MASTER SCORE
# ============================================================


def test_master_score_returns_score_and_components():
    snapshot = make_snapshot()

    valuation = FakeValuation(
        upside=0.20
    )

    score, components = master_score(
        snapshot,
        valuation,
        momentum=50,
    )

    assert isinstance(score, float)
    assert isinstance(components, dict)


def test_master_score_contains_all_components():
    snapshot = make_snapshot()

    valuation = FakeValuation(
        upside=0.20
    )

    score, components = master_score(
        snapshot,
        valuation,
        momentum=50,
    )

    expected = {
        "valuation",
        "growth",
        "quality",
        "momentum",
        "risk",
    }

    assert set(components.keys()) == expected


def test_master_score_is_bounded():
    snapshot = make_snapshot()

    valuation = FakeValuation(
        upside=100.0
    )

    score, _ = master_score(
        snapshot,
        valuation,
        momentum=100,
    )

    assert 0 <= score <= 100


def test_master_score_with_missing_data_does_not_crash():
    snapshot = make_snapshot(
        revenue_growth=None,
        earnings_growth=None,
        return_on_equity=None,
        profit_margin=None,
        operating_margin=None,
        debt_to_equity=None,
        current_ratio=None,
        beta=None,
    )

    valuation = FakeValuation(
        upside=None
    )

    score, components = master_score(
        snapshot,
        valuation,
        momentum=50,
    )

    assert 0 <= score <= 100
    assert isinstance(components, dict)


def test_better_valuation_improves_master_score():
    snapshot = make_snapshot()

    cheap = FakeValuation(
        upside=0.30
    )

    expensive = FakeValuation(
        upside=-0.30
    )

    cheap_score, _ = master_score(
        snapshot,
        cheap,
        momentum=50,
    )

    expensive_score, _ = master_score(
        snapshot,
        expensive,
        momentum=50,
    )

    assert cheap_score > expensive_score


def test_better_momentum_improves_master_score():
    snapshot = make_snapshot()

    valuation = FakeValuation(
        upside=0.10
    )

    weak_score, _ = master_score(
        snapshot,
        valuation,
        momentum=20,
    )

    strong_score, _ = master_score(
        snapshot,
        valuation,
        momentum=80,
    )

    assert strong_score > weak_score


def test_poor_risk_reduces_master_score():
    valuation = FakeValuation(
        upside=0.20
    )

    safe = make_snapshot(
        debt_to_equity=20.0,
        current_ratio=2.0,
        beta=1.0,
    )

    risky = make_snapshot(
        debt_to_equity=500.0,
        current_ratio=0.5,
        beta=2.0,
    )

    safe_score, _ = master_score(
        safe,
        valuation,
        momentum=50,
    )

    risky_score, _ = master_score(
        risky,
        valuation,
        momentum=50,
    )

    assert safe_score > risky_score


# ============================================================
# SIGNAL
# ============================================================


def test_signal_buy_threshold():
    assert signal(75) == "BUY"
    assert signal(100) == "BUY"


def test_signal_hold_range():
    # HOLD range is between BUY threshold (>=70) and SELL threshold (<=40)
    # So valid HOLD range is (40, 70)
    assert signal(40.01) == "HOLD"
    assert signal(50) == "HOLD"
    assert signal(69.99) == "HOLD"


def test_signal_sell_threshold():
    assert signal(40) == "SELL"
    assert signal(0) == "SELL"


def test_signal_boundaries_are_deterministic():
    # BUY threshold is >= 70
    assert signal(70) == "BUY"
    assert signal(69.999) == "HOLD"

    # SELL threshold is <= 40
    assert signal(40) == "SELL"
    assert signal(40.001) == "HOLD"


# ============================================================
# EXTREME INPUTS
# ============================================================


def test_master_score_handles_extreme_inputs():
    snapshot = make_snapshot(
        revenue_growth=100.0,
        earnings_growth=100.0,
        return_on_equity=100.0,
        profit_margin=100.0,
        operating_margin=100.0,
        debt_to_equity=100_000.0,
        current_ratio=0.001,
        beta=100.0,
    )

    valuation = FakeValuation(
        upside=100.0
    )

    score, components = master_score(
        snapshot,
        valuation,
        momentum=100,
    )

    assert math.isfinite(score)
    assert 0 <= score <= 100

    for value in components.values():
        assert math.isfinite(value)
        assert 0 <= value <= 100