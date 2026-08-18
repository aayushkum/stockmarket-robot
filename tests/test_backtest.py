"""Tests for the point-in-time strategy backtest."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from stockmarket.analyzer import analyze_snapshot
from stockmarket.backtest import (
    BacktestConfig,
    backtest_with_snapshots,
)
from stockmarket.data import Snapshot


def make_snapshot(
    ticker="TEST",
    price=100.0,
):

    return Snapshot(
        ticker=ticker,
        price=price,

        eps=5.0,
        forward_eps=5.5,

        revenue=1_000_000.0,
        free_cash_flow=100_000.0,
        shares=10_000.0,

        beta=1.0,

        pe=20.0,
        forward_pe=18.0,

        profit_margin=0.10,
        operating_margin=0.15,
        return_on_equity=0.15,

        revenue_growth=0.08,
        earnings_growth=0.10,

        debt_to_equity=40.0,
        current_ratio=1.5,

        market_cap=1_000_000.0,

        sector="Technology",
    )


def make_prices(
    n=240,
):
    dates = pd.date_range(
        "2020-01-01",
        periods=n,
        freq="B",
    )

    close = pd.Series(
        np.linspace(
            100.0,
            120.0,
            n,
        ),
        index=dates,
        name="Close",
    )

    return pd.DataFrame(
        {
            "Close": close
        }
    )


def test_analyze_snapshot_is_shared_decision_engine():
    prices = make_prices()["Close"]

    snapshot = make_snapshot(
        price=float(prices.iloc[-1])
    )

    result = analyze_snapshot(
        snapshot,
        prices,
    )

    assert result["ticker"] == "TEST"

    assert result["price"] == snapshot.price

    assert 0 <= result["master_score"] <= 100

    assert result["signal"] in {
        "BUY",
        "HOLD",
        "SELL",
    }


def test_backtest_uses_only_snapshot_for_each_historical_date():
    prices = make_prices(205)

    snapshots = {
        prices.index[i]: make_snapshot(
            price=float(prices.iloc[i])
        )
        for i in range(
            200,
            len(prices) - 1,
        )
    }

    seen = []

    def fake_analyze(
        snapshot,
        history,
    ):
        seen.append(
            (
                snapshot.price,
                history.index[-1],
            )
        )

        return {
            "signal": "BUY"
        }

    with patch(
        "stockmarket.backtest.analyze_snapshot",
        side_effect=fake_analyze,
    ):

        result = backtest_with_snapshots(
            "TEST",
            prices,
            snapshots,
        )

    assert seen[0] == (
        float(prices.iloc[200]),
        prices.index[200],
    )

    assert len(seen) == len(prices) - 201

    assert result["trade_count"] == 1

    assert (
        result["trades"][0]["signal"]
        == "BUY"
    )

    assert (
        result["skipped_observations"]
        == 0
    )


def test_hold_keeps_existing_position():
    prices = make_prices(207)

    snapshots = {
        prices.index[200]: make_snapshot(
            price=float(prices.iloc[200])
        ),
        prices.index[201]: make_snapshot(
            price=float(prices.iloc[201])
        ),
        prices.index[202]: make_snapshot(
            price=float(prices.iloc[202])
        ),
    }

    signals = iter(
        [
            "BUY",
            "HOLD",
            "HOLD",
        ]
    )

    def fake_analyze(
        snapshot,
        history,
    ):
        return {
            "signal": next(signals)
        }

    with patch(
        "stockmarket.backtest.analyze_snapshot",
        side_effect=fake_analyze,
    ):

        result = backtest_with_snapshots(
            "TEST",
            prices,
            snapshots,
        )

    assert result["trade_count"] == 1

    assert (
        result["trades"][0]["position"]
        == 1
    )

    assert (
        result["final_equity"]
        > result["initial_capital"]
    )


def test_transaction_cost_reduces_result():
    prices = make_prices(202)

    snapshots = {
        prices.index[200]: make_snapshot(
            price=float(prices.iloc[200])
        )
    }

    def fake_analyze(
        snapshot,
        history,
    ):
        return {
            "signal": "BUY"
        }

    with patch(
        "stockmarket.backtest.analyze_snapshot",
        side_effect=fake_analyze,
    ):

        no_cost = backtest_with_snapshots(
            "TEST",
            prices,
            snapshots,
            BacktestConfig(
                transaction_cost_bps=0
            ),
        )

        with_cost = backtest_with_snapshots(
            "TEST",
            prices,
            snapshots,
            BacktestConfig(
                transaction_cost_bps=100
            ),
        )

    assert (
        with_cost["final_equity"]
        < no_cost["final_equity"]
    )


def test_backtest_rejects_insufficient_history():
    prices = make_prices(100)

    with pytest.raises(
        ValueError,
        match="Insufficient data",
    ):
        backtest_with_snapshots(
            "TEST",
            prices,
            {},
        )
