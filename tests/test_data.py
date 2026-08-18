"""Tests for the data module."""
import pytest
from unittest.mock import Mock, patch
import numpy as np
import pandas as pd
from stockmarket.data import Snapshot, num, fetch_snapshot, price_history


class TestNum:
    """Tests for the num() conversion function."""
    
    def test_num_converts_valid_float(self):
        """Test converting valid float value."""
        assert num(100.5) == 100.5
        assert num("200.75") == 200.75
        assert num(300) == 300.0
    
    def test_num_handles_zero(self):
        """Test that zero is handled correctly."""
        assert num(0) == 0.0
        assert num(0.0) == 0.0
    
    def test_num_handles_negative(self):
        """Test that negative values work."""
        assert num(-50.5) == -50.5
        assert num("-100") == -100.0
    
    def test_num_returns_none_on_invalid_string(self):
        """Test that invalid strings return None."""
        assert num("abc") is None
        assert num("") is None
    
    def test_num_returns_none_on_type_error(self):
        """Test that type errors return None."""
        assert num(None) is None
        assert num([1, 2, 3]) is None
    
    def test_num_returns_none_on_nan(self):
        """Test that NaN returns None."""
        assert num(float('nan')) is None
    
    def test_num_returns_none_on_infinity(self):
        """Test that infinity returns None."""
        assert num(float('inf')) is None
        assert num(float('-inf')) is None
    
    def test_num_handles_very_large_numbers(self):
        """Test handling of very large numbers."""
        large = 1e308
        assert num(large) == large
    
    def test_num_handles_very_small_numbers(self):
        """Test handling of very small numbers."""
        small = 1e-308
        assert num(small) == small


class TestSnapshot:
    """Tests for Snapshot dataclass."""
    
    def test_snapshot_creation(self):
        """Test creating a snapshot."""
        snapshot = Snapshot(
            ticker="AAPL",
            price=150.0,
            eps=5.0,
            forward_eps=5.5,
            revenue=1e11,
            free_cash_flow=1e10,
            shares=1e9,
            beta=1.2,
            pe=30,
            forward_pe=27,
            profit_margin=0.25,
            operating_margin=0.30,
            return_on_equity=0.20,
            revenue_growth=0.10,
            earnings_growth=0.15,
            debt_to_equity=50,
            current_ratio=1.5,
            market_cap=1.5e11,
            sector="Technology"
        )
        
        assert snapshot.ticker == "AAPL"
        assert snapshot.price == 150.0
        assert snapshot.sector == "Technology"
    
    def test_snapshot_with_none_values(self):
        """Test snapshot with None values for optional fields."""
        snapshot = Snapshot(
            ticker="TEST",
            price=100.0,
            eps=None,
            forward_eps=None,
            revenue=None,
            free_cash_flow=None,
            shares=None,
            beta=None,
            pe=None,
            forward_pe=None,
            profit_margin=None,
            operating_margin=None,
            return_on_equity=None,
            revenue_growth=None,
            earnings_growth=None,
            debt_to_equity=None,
            current_ratio=None,
            market_cap=None,
            sector="Unknown"
        )
        
        assert snapshot.ticker == "TEST"
        assert snapshot.eps is None
    
    def test_snapshot_to_dict(self):
        """Test converting snapshot to dictionary."""
        snapshot = Snapshot(
            ticker="MSFT",
            price=300.0,
            eps=9.0,
            forward_eps=10.0,
            revenue=2e11,
            free_cash_flow=5e10,
            shares=2e9,
            beta=0.9,
            pe=33,
            forward_pe=30,
            profit_margin=0.35,
            operating_margin=0.40,
            return_on_equity=0.30,
            revenue_growth=0.12,
            earnings_growth=0.18,
            debt_to_equity=30,
            current_ratio=1.8,
            market_cap=6e11,
            sector="Technology"
        )
        
        snapshot_dict = snapshot.to_dict()
        assert isinstance(snapshot_dict, dict)
        assert snapshot_dict["ticker"] == "MSFT"
        assert snapshot_dict["price"] == 300.0
        assert snapshot_dict["sector"] == "Technology"


@patch('stockmarket.data.yf.Ticker')
def test_fetch_snapshot_success(mock_ticker):
    """Test successful snapshot fetch."""
    mock_info = {
        "currentPrice": 150.0,
        "trailingEps": 5.0,
        "forwardEps": 5.5,
        "totalRevenue": 1e11,
        "freeCashflow": 1e10,
        "sharesOutstanding": 1e9,
        "beta": 1.2,
        "trailingPE": 30,
        "forwardPE": 27,
        "profitMargins": 0.25,
        "operatingMargins": 0.30,
        "returnOnEquity": 0.20,
        "revenueGrowth": 0.10,
        "earningsGrowth": 0.15,
        "debtToEquity": 50,
        "currentRatio": 1.5,
        "marketCap": 1.5e11,
        "sector": "Technology"
    }
    
    mock_fast = {"lastPrice": 150.0}
    
    mock_ticker.return_value.info = mock_info
    mock_ticker.return_value.fast_info = mock_fast
    
    snapshot = fetch_snapshot("AAPL")
    
    assert snapshot.ticker == "AAPL"
    assert snapshot.price == 150.0
    assert snapshot.sector == "Technology"


@patch('stockmarket.data.yf.Ticker')
def test_fetch_snapshot_uses_fast_price(mock_ticker):
    """Test that fast_info price is preferred."""
    mock_info = {"currentPrice": 150.0}
    mock_fast = {"lastPrice": 151.0}
    
    mock_ticker.return_value.info = mock_info
    mock_ticker.return_value.fast_info = mock_fast
    
    snapshot = fetch_snapshot("AAPL")
    
    assert snapshot.price == 151.0


@patch('stockmarket.data.yf.Ticker')
def test_fetch_snapshot_fallback_to_info_price(mock_ticker):
    """Test fallback to info price when fast unavailable."""
    mock_info = {"currentPrice": 150.0}
    mock_fast = {}
    
    mock_ticker.return_value.info = mock_info
    mock_ticker.return_value.fast_info = mock_fast
    
    snapshot = fetch_snapshot("AAPL")
    
    assert snapshot.price == 150.0


@patch('stockmarket.data.yf.Ticker')
def test_fetch_snapshot_raises_on_no_price(mock_ticker):
    """Test error when price unavailable."""
    mock_ticker.return_value.info = {}
    mock_ticker.return_value.fast_info = {}
    
    with pytest.raises(ValueError, match="Invalid price"):
        fetch_snapshot("AAPL")


@patch('stockmarket.data.yf.Ticker')
def test_fetch_snapshot_raises_on_zero_price(mock_ticker):
    """Test error when price is zero."""
    mock_info = {"currentPrice": 0}
    mock_fast = {}
    
    mock_ticker.return_value.info = mock_info
    mock_ticker.return_value.fast_info = mock_fast
    
    with pytest.raises(ValueError, match="Invalid price"):
        fetch_snapshot("AAPL")


@patch('stockmarket.data.yf.Ticker')
def test_fetch_snapshot_raises_on_fetch_error(mock_ticker):
    """Test error when yfinance fetch fails."""
    mock_ticker.side_effect = Exception("Network error")
    
    with pytest.raises(ValueError, match="Failed to fetch data"):
        fetch_snapshot("AAPL")


@patch('stockmarket.data.yf.Ticker')
def test_price_history_success(mock_ticker):
    """Test successful price history fetch."""
    dates = pd.date_range('2023-01-01', periods=252)
    close = pd.Series(np.linspace(100, 120, 252), index=dates)
    
    mock_df = pd.DataFrame({'Close': close})
    mock_ticker.return_value.history.return_value = mock_df
    
    history = price_history("AAPL", "1y")
    
    assert len(history) == 252
    assert "Close" in history.columns


@patch('stockmarket.data.yf.Ticker')
def test_price_history_default_period(mock_ticker):
    """Test that default period is '1y'."""
    dates = pd.date_range('2023-01-01', periods=252)
    close = pd.Series(np.linspace(100, 120, 252), index=dates)
    
    mock_df = pd.DataFrame({'Close': close})
    mock_ticker.return_value.history.return_value = mock_df
    
    price_history("AAPL")
    
    mock_ticker.return_value.history.assert_called_once_with(period="1y", auto_adjust=True)


@patch('stockmarket.data.yf.Ticker')
def test_price_history_raises_on_empty(mock_ticker):
    """Test error when history is empty."""
    mock_ticker.return_value.history.return_value = pd.DataFrame()
    
    with pytest.raises(ValueError, match="No price history available"):
        price_history("AAPL", "1y")


@patch('stockmarket.data.yf.Ticker')
def test_price_history_raises_on_fetch_error(mock_ticker):
    """Test error when yfinance fetch fails."""
    mock_ticker.return_value.history.side_effect = Exception("Network error")
    
    with pytest.raises(ValueError, match="Failed to fetch price history"):
        price_history("AAPL", "1y")
