"""Tests for the analyzer module."""
import pytest
from unittest.mock import Mock, patch
from stockmarket.analyzer import analyze


def create_mock_snapshot():
    """Create a properly mocked snapshot with all required fields."""
    mock = Mock()
    mock.price = 100.0
    mock.sector = "Technology"
    # Valuation data
    mock.eps = 5.0
    mock.forward_eps = 5.5
    mock.revenue = 1e11
    mock.free_cash_flow = 1e10
    mock.shares = 1e9
    mock.beta = 1.2
    mock.pe = 30
    mock.forward_pe = 27
    # Scoring data
    mock.profit_margin = 0.25
    mock.operating_margin = 0.30
    mock.return_on_equity = 0.20
    mock.revenue_growth = 0.10
    mock.earnings_growth = 0.15
    mock.debt_to_equity = 50
    mock.current_ratio = 1.5
    return mock


@patch('stockmarket.analyzer.fetch_snapshot')
@patch('stockmarket.analyzer.price_history')
def test_analyze_returns_dict_structure(mock_price_history, mock_fetch_snapshot):
    """Test that analyze returns properly structured result."""
    # Mock snapshot with all required fields
    mock_snapshot = create_mock_snapshot()
    mock_fetch_snapshot.return_value = mock_snapshot
    
    # Mock price history
    import pandas as pd
    import numpy as np
    dates = pd.date_range('2023-01-01', periods=250)
    close = pd.Series(np.linspace(100, 120, 250), index=dates)
    mock_history = pd.DataFrame({"Close": close})
    mock_price_history.return_value = mock_history
    
    result = analyze("TEST")
    
    # Verify structure
    assert isinstance(result, dict)
    assert result["ticker"] == "TEST"
    assert "analyzed_at" in result
    assert "price" in result
    assert "sector" in result
    assert "fair_value" in result
    assert "upside" in result
    assert "master_score" in result
    assert "signal" in result
    assert "snapshot" in result
    assert "components" in result
    assert "valuation" in result


@patch('stockmarket.analyzer.fetch_snapshot')
def test_analyze_propagates_fetch_errors(mock_fetch_snapshot):
    """Test that analyze propagates data fetch errors."""
    mock_fetch_snapshot.side_effect = ValueError("No price available")
    
    with pytest.raises(ValueError, match="No price available"):
        analyze("INVALID")


@patch('stockmarket.analyzer.fetch_snapshot')
@patch('stockmarket.analyzer.price_history')
def test_analyze_includes_components(mock_price_history, mock_fetch_snapshot):
    """Test that analyze calculates all component scores."""
    # Mock snapshot with data
    mock_snapshot = create_mock_snapshot()
    mock_fetch_snapshot.return_value = mock_snapshot
    
    # Mock price history
    import pandas as pd
    import numpy as np
    dates = pd.date_range('2023-01-01', periods=250)
    close = pd.Series(np.linspace(100, 120, 250), index=dates)
    mock_history = pd.DataFrame({"Close": close})
    mock_price_history.return_value = mock_history
    
    result = analyze("TEST")
    
    # Verify components exist
    components = result["components"]
    assert "valuation" in components
    assert "growth" in components
    assert "quality" in components
    assert "momentum" in components
    assert "risk" in components
    
    # Verify they're all in valid range
    for score in components.values():
        assert 0 <= score <= 100
