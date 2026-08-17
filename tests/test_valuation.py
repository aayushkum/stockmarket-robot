import math

import pytest

from stockmarket.data import Snapshot
from stockmarket.valuation import (
    ValuationResult,
    ValuationSummary,
    dcf_value,
    summarize,
)


def make_snapshot(**overrides):
    """
    Build a complete Snapshot with sensible defaults.

    Individual tests can override only the fields relevant to them.
    """

    values = {
        "ticker": "TEST",
        "price": 100.0,

        # Per-share fundamentals
        "eps": 5.0,
        "forward_eps": 5.5,
        "free_cash_flow_per_share": 4.0,

        # Company-level fundamentals
        "revenue": 100_000_000_000.0,
        "free_cash_flow": 4_000_000_000.0,
        "shares": 1_000_000_000.0,
        "market_cap": 100_000_000_000.0,

        # Valuation / risk
        "beta": 1.0,
        "pe": 20.0,
        "forward_pe": 18.18,

        # Profitability
        "profit_margin": 0.20,
        "operating_margin": 0.25,
        "return_on_equity": 0.25,

        # Growth
        "revenue_growth": 0.10,
        "earnings_growth": 0.10,

        # Balance sheet
        "debt_to_equity": 50.0,
        "current_ratio": 1.5,

        "sector": "Technology",
    }

    values.update(overrides)

    return Snapshot(**values)


# ============================================================
# BASIC DCF TESTS
# ============================================================


def test_dcf_returns_positive_value_for_positive_fcf():
    value = dcf_value(
        fcf_per_share=5.0,
        growth=0.05,
    )

    assert value is not None
    assert value > 0
    assert math.isfinite(value)


def test_dcf_zero_growth_is_actually_zero_growth():
    zero_growth = dcf_value(
        fcf_per_share=5.0,
        growth=0.0,
    )

    explicit_zero_growth = dcf_value(
        fcf_per_share=5.0,
        growth=0,
    )

    assert zero_growth == pytest.approx(
        explicit_zero_growth
    )


def test_dcf_growth_is_capped():
    normal = dcf_value(
        fcf_per_share=5.0,
        growth=0.10,
    )

    extreme = dcf_value(
        fcf_per_share=5.0,
        growth=1.00,
    )

    assert extreme == pytest.approx(normal)


def test_dcf_terminal_growth_is_below_discount_rate():
    value = dcf_value(
        fcf_per_share=5.0,
        growth=0.05,
        discount_rate=0.09,
        terminal_growth=0.09,
    )

    assert value is not None
    assert math.isfinite(value)
    assert value > 0


def test_dcf_rejects_negative_fcf():
    value = dcf_value(
        fcf_per_share=-5.0,
        growth=0.05,
    )

    assert value is None


def test_dcf_rejects_zero_fcf():
    value = dcf_value(
        fcf_per_share=0.0,
        growth=0.05,
    )

    assert value is None


def test_dcf_rejects_missing_fcf():
    value = dcf_value(
        fcf_per_share=None,
        growth=0.05,
    )

    assert value is None


def test_dcf_handles_missing_growth():
    """
    Missing growth should fall back to 0%, not crash.
    """

    value = dcf_value(
        fcf_per_share=5.0,
        growth=None,
    )

    assert value is not None
    assert value > 0


# ============================================================
# SNAPSHOT / PER-SHARE TESTS
# ============================================================


def test_snapshot_has_correct_fcf_per_share():
    snapshot = make_snapshot(
        free_cash_flow=10_000_000_000.0,
        shares=2_000_000_000.0,
        free_cash_flow_per_share=5.0,
    )

    assert snapshot.free_cash_flow_per_share == pytest.approx(
        snapshot.free_cash_flow / snapshot.shares
    )


def test_fcf_per_share_is_not_company_level_fcf():
    """
    This test protects against accidentally feeding total company FCF
    into a per-share valuation model.
    """

    snapshot = make_snapshot(
        free_cash_flow=10_000_000_000.0,
        shares=2_000_000_000.0,
        free_cash_flow_per_share=5.0,
    )

    assert snapshot.free_cash_flow != (
        snapshot.free_cash_flow_per_share
    )


# ============================================================
# SUMMARY TESTS
# ============================================================


def test_summary_returns_valuation_summary():
    snapshot = make_snapshot()

    result = summarize(snapshot)

    assert isinstance(
        result,
        ValuationSummary,
    )


def test_summary_contains_estimates():
    snapshot = make_snapshot()

    result = summarize(snapshot)

    assert len(result.estimates) >= 3


def test_summary_contains_dcf():
    snapshot = make_snapshot()

    result = summarize(snapshot)

    models = [
        estimate.model
        for estimate in result.estimates
    ]

    assert "DCF" in models


def test_summary_contains_eps_model():
    snapshot = make_snapshot()

    result = summarize(snapshot)

    models = [
        estimate.model
        for estimate in result.estimates
    ]

    assert "Forward EPS × P/E" in models


def test_summary_contains_fcf_model():
    snapshot = make_snapshot()

    result = summarize(snapshot)

    models = [
        estimate.model
        for estimate in result.estimates
    ]

    assert "FCF/share × Multiple" in models


def test_summary_contains_historical_eps_model():
    snapshot = make_snapshot()

    result = summarize(snapshot)

    models = [
        estimate.model
        for estimate in result.estimates
    ]

    assert "Historical EPS × 18" in models


# ============================================================
# FAIR VALUE / UPSIDE TESTS
# ============================================================


def test_fair_value_is_positive():
    snapshot = make_snapshot()

    result = summarize(snapshot)

    assert result.fair_value is not None
    assert result.fair_value > 0


def test_upside_is_calculated_from_price():
    snapshot = make_snapshot(
        price=100.0,
    )

    result = summarize(snapshot)

    assert result.fair_value is not None
    assert result.upside is not None

    expected = (
        result.fair_value / snapshot.price
        - 1.0
    )

    assert result.upside == pytest.approx(
        expected
    )


def test_valuation_range_contains_fair_value():
    snapshot = make_snapshot()

    result = summarize(snapshot)

    assert result.low_value is not None
    assert result.high_value is not None
    assert result.fair_value is not None

    assert result.low_value <= result.fair_value
    assert result.fair_value <= result.high_value


def test_valuation_range_is_ordered():
    snapshot = make_snapshot()

    result = summarize(snapshot)

    assert result.low_value <= result.high_value


# ============================================================
# IMPORTANT REGRESSION TEST:
# PER-SHARE DCF
# ============================================================


def test_dcf_uses_fcf_per_share_not_total_fcf():

    snapshot = make_snapshot(
        free_cash_flow=10_000_000_000.0,
        shares=2_000_000_000.0,
        free_cash_flow_per_share=5.0,
    )

    result = summarize(snapshot)

    dcf_estimate = next(
        estimate
        for estimate in result.estimates
        if estimate.model == "DCF"
    )

    expected = dcf_value(
        fcf_per_share=5.0,
        growth=0.10,
        discount_rate=0.09,
        terminal_growth=0.025,
        years=5,
    )

    assert dcf_estimate.fair_value == pytest.approx(
        expected
    )


def test_dcf_would_be_completely_different_for_total_fcf():

    per_share = dcf_value(
        fcf_per_share=5.0,
        growth=0.05,
    )

    company_level = dcf_value(
        fcf_per_share=10_000_000_000.0,
        growth=0.05,
    )

    assert company_level > per_share * 1_000_000


# ============================================================
# MISSING-DATA TESTS
# ============================================================


def test_missing_fcf_does_not_crash_summary():
    snapshot = make_snapshot(
        free_cash_flow=None,
        free_cash_flow_per_share=None,
    )

    result = summarize(snapshot)

    assert isinstance(
        result,
        ValuationSummary,
    )


def test_missing_forward_eps_does_not_crash_summary():
    snapshot = make_snapshot(
        forward_eps=None,
    )

    result = summarize(snapshot)

    assert isinstance(
        result,
        ValuationSummary,
    )


def test_missing_historical_eps_does_not_crash_summary():
    snapshot = make_snapshot(
        eps=None,
    )

    result = summarize(snapshot)

    assert isinstance(
        result,
        ValuationSummary,
    )


def test_missing_growth_does_not_crash_summary():
    snapshot = make_snapshot(
        revenue_growth=None,
        earnings_growth=None,
    )

    result = summarize(snapshot)

    assert isinstance(
        result,
        ValuationSummary,
    )


# ============================================================
# EXTREME / INVALID DATA TESTS
# ============================================================


def test_nan_fcf_is_rejected():
    value = dcf_value(
        fcf_per_share=float("nan"),
        growth=0.05,
    )

    assert value is None


def test_infinite_fcf_is_rejected():
    value = dcf_value(
        fcf_per_share=float("inf"),
        growth=0.05,
    )

    assert value is None


def test_nan_growth_does_not_crash():
    value = dcf_value(
        fcf_per_share=5.0,
        growth=float("nan"),
    )

    assert value is not None
    assert math.isfinite(value)


# ============================================================
# SERIALIZATION TESTS
# ============================================================


def test_valuation_result_to_dict():
    result = ValuationResult(
        model="Test",
        fair_value=100.0,
        note="Test valuation",
    )

    data = result.to_dict()

    assert data["model"] == "Test"
    assert data["fair_value"] == 100.0
    assert data["note"] == "Test valuation"


def test_valuation_summary_to_dict():
    snapshot = make_snapshot()

    result = summarize(snapshot)
    data = result.to_dict()

    assert "estimates" in data
    assert "fair_value" in data
    assert "upside" in data
    assert "low_value" in data
    assert "high_value" in data

    assert isinstance(
        data["estimates"],
        list,
    )
