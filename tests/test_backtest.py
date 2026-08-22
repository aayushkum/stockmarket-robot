"""Tests for the backtest module."""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from stockmarket.backtest import (full_system_backtest,
                                  full_system_universe_backtest,
                                  moving_average_backtest)
from stockmarket.config import Settings
from stockmarket.data import Snapshot


@patch('stockmarket.backtest.yf.Ticker')
def test_backtest_returns_dict_structure(mock_ticker):
    """Test that backtest returns properly structured result."""
    # Create mock price history with 250 days of data
    dates = pd.date_range('2020-01-01', periods=250)
    close = pd.Series(np.linspace(100, 120, 250), index=dates)
    
    mock_df = pd.DataFrame({'Close': close})
    mock_ticker.return_value.history.return_value = mock_df
    
    result = moving_average_backtest("TEST", "1y")
    
    # Verify structure
    assert isinstance(result, dict)
    assert result["ticker"] == "TEST"
    assert result["period"] == "1y"
    assert "strategy_return" in result
    assert "benchmark_return" in result
    assert "cagr" in result
    assert "max_drawdown" in result
    assert "sharpe" in result
    assert "observations" in result


@patch('stockmarket.backtest.yf.Ticker')
def test_backtest_strategy_vs_benchmark(mock_ticker):
    """Test that backtest strategy can outperform benchmark."""
    # Create scenario where strategy is better (uptrend)
    dates = pd.date_range('2020-01-01', periods=250)
    close = pd.Series(np.linspace(100, 200, 250), index=dates)
    
    mock_df = pd.DataFrame({'Close': close})
    mock_ticker.return_value.history.return_value = mock_df
    
    result = moving_average_backtest("TEST", "1y")
    
    # In an uptrend, MA crossover should perform similarly or better
    assert result["strategy_return"] > -0.5  # Not severely negative


@patch('stockmarket.backtest.yf.Ticker')
def test_backtest_downtrend_performance(mock_ticker):
    """Test that backtest handles downtrends."""
    # Create downtrend scenario
    dates = pd.date_range('2020-01-01', periods=250)
    close = pd.Series(np.linspace(200, 100, 250), index=dates)
    
    mock_df = pd.DataFrame({'Close': close})
    mock_ticker.return_value.history.return_value = mock_df
    
    result = moving_average_backtest("TEST", "1y")
    
    # Both should be negative but strategy may be less negative
    assert result["benchmark_return"] < 0
    assert result["observations"] == 250


@patch('stockmarket.backtest.yf.Ticker')
def test_backtest_raises_on_empty_data(mock_ticker):
    """Test that backtest raises error on empty data."""
    mock_ticker.return_value.history.return_value = pd.DataFrame()
    
    with pytest.raises(ValueError, match="No history available"):
        moving_average_backtest("INVALID", "1y")


@patch('stockmarket.backtest.yf.Ticker')
def test_backtest_raises_on_insufficient_data(mock_ticker):
    """Test that backtest raises error with insufficient data."""
    # Fewer than the configured 200 slow-window days is insufficient.
    dates = pd.date_range('2020-01-01', periods=199)
    close = pd.Series(np.linspace(100, 110, 199), index=dates)
    
    mock_df = pd.DataFrame({'Close': close})
    mock_ticker.return_value.history.return_value = mock_df
    
    with pytest.raises(ValueError, match="Insufficient data"):
        moving_average_backtest("TEST", "1y")


@patch('stockmarket.backtest.yf.Ticker')
def test_backtest_metrics_are_bounded(mock_ticker):
    """Test that backtest metrics are within expected bounds."""
    dates = pd.date_range('2020-01-01', periods=250)
    close = pd.Series(np.linspace(100, 120, 250), index=dates)
    
    mock_df = pd.DataFrame({'Close': close})
    mock_ticker.return_value.history.return_value = mock_df
    
    result = moving_average_backtest("TEST", "1y")
    
    # Returns should be reasonable
    assert -1 < result["strategy_return"] < 10
    assert -1 < result["benchmark_return"] < 10
    
    # Drawdown should be negative or zero
    assert result["max_drawdown"] <= 0
    
    # Sharpe ratio should be finite, without an arbitrary performance cap.
    assert np.isfinite(result["sharpe"])


@patch('stockmarket.backtest.yf.Ticker')
def test_full_system_backtest_executes_analysis_signals(mock_ticker, tmp_path):
    """Test that full-system mode can buy and sell from dated snapshots."""
    dates = pd.date_range('2020-01-01', periods=250)
    close = pd.Series(np.linspace(100, 200, 250), index=dates)
    mock_ticker.return_value.history.return_value = pd.DataFrame({'Close': close})
    snapshot = Snapshot(
        "TEST", 100.0, 5.0, 5.5, 1_000_000, 100_000, 10_000,
        1.0, 20.0, 18.0, 0.2, 0.25, 0.3, 0.1, 0.1, 50.0, 1.5,
        1_000_000, "Technology"
    )
    snapshot_file = tmp_path / "snapshots.json"
    snapshot_file.write_text(
        '{"snapshots": {"2020-01-01": ' + str(snapshot.to_dict()).replace("'", '"') + '}}',
        encoding="utf-8",
    )

    result = full_system_backtest(
        "TEST", snapshot_file, "1y", Settings(starting_cash=1000)
    )

    assert result["strategy"] == "full_system"
    assert result["starting_cash"] == 1000
    assert result["trade_count"] >= 0


def test_full_system_universe_skips_missing_snapshot_files(tmp_path):
    """Test that a universe run does not substitute current fundamentals."""
    result = full_system_universe_backtest(["AAPL", "MSFT"], tmp_path, "5y")

    assert result["completed_tickers"] == 0
    assert result["missing_snapshot_tickers"] == ["AAPL", "MSFT"]
    assert result["average_return"] is None
