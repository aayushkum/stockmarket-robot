"""Tests for the paper trading portfolio engine."""
import pytest
from stockmarket.config import Settings
from stockmarket.paper import PaperPortfolio, Position


@pytest.fixture
def portfolio():
    """Create a test portfolio."""
    return PaperPortfolio(Settings(starting_cash=100_000))


class TestPaperPortfolioBuy:
    """Tests for buy functionality."""
    
    def test_buy_single_position(self, portfolio):
        """Test buying a single stock position."""
        assert portfolio.buy('ABC', 100, 1000)
        assert portfolio.cash == 99000
        assert 'ABC' in portfolio.positions
        assert portfolio.positions['ABC'].shares == 10
    
    def test_buy_multiple_shares(self, portfolio):
        """Test buying multiple share quantities."""
        assert portfolio.buy('XYZ', 50, 5000)
        assert portfolio.positions['XYZ'].shares == 100
        assert portfolio.cash == 95000
    
    def test_buy_rejects_insufficient_cash(self, portfolio):
        """Test that buy is rejected when insufficient cash."""
        assert not portfolio.buy('ABC', 100, 150_000)
        assert portfolio.cash == 100_000
        assert 'ABC' not in portfolio.positions
    
    def test_buy_rejects_zero_amount(self, portfolio):
        """Test that buy is rejected with zero amount."""
        assert not portfolio.buy('ABC', 100, 0)
        assert portfolio.cash == 100_000
    
    def test_buy_rejects_negative_amount(self, portfolio):
        """Test that buy is rejected with negative amount."""
        assert not portfolio.buy('ABC', 100, -1000)
        assert portfolio.cash == 100_000
    
    def test_buy_rejects_zero_price(self, portfolio):
        """Test that buy is rejected with zero price."""
        assert not portfolio.buy('ABC', 0, 1000)
        assert portfolio.cash == 100_000
    
    def test_buy_rejects_negative_price(self, portfolio):
        """Test that buy is rejected with negative price."""
        assert not portfolio.buy('ABC', -100, 1000)
        assert portfolio.cash == 100_000
    
    def test_buy_adds_to_existing_position(self, portfolio):
        """Test adding to existing position updates average cost."""
        portfolio.buy('ABC', 100, 1000)  # 10 shares @ $100
        portfolio.buy('ABC', 110, 1100)  # 10 shares @ $110
        
        pos = portfolio.positions['ABC']
        assert pos.shares == 20
        # Average cost should be (1000 + 1100) / 20 = 105
        assert pos.avg_cost == 105.0


class TestPaperPortfolioSell:
    """Tests for sell functionality."""
    
    def test_sell_entire_position(self, portfolio):
        """Test selling entire position."""
        portfolio.buy('ABC', 100, 1000)
        proceeds = portfolio.sell('ABC', 110)
        
        assert proceeds == 1100
        assert portfolio.cash == 100_100
        assert 'ABC' not in portfolio.positions
    
    def test_sell_partial_position(self, portfolio):
        """Test selling partial position."""
        portfolio.buy('ABC', 100, 1000)
        proceeds = portfolio.sell('ABC', 110, fraction=0.5)
        
        assert proceeds == 550
        assert portfolio.cash == 99_550
        assert portfolio.positions['ABC'].shares == 5
    
    def test_sell_nonexistent_position(self, portfolio):
        """Test selling position that doesn't exist."""
        proceeds = portfolio.sell('XYZ', 100)
        assert proceeds == 0
        assert portfolio.cash == 100_000
    
    def test_sell_rejects_zero_price(self, portfolio):
        """Test that sell is rejected with zero price."""
        portfolio.buy('ABC', 100, 1000)
        proceeds = portfolio.sell('ABC', 0)
        assert proceeds == 0
        assert portfolio.positions['ABC'].shares == 10
    
    def test_sell_rejects_negative_price(self, portfolio):
        """Test that sell is rejected with negative price."""
        portfolio.buy('ABC', 100, 1000)
        proceeds = portfolio.sell('ABC', -100)
        assert proceeds == 0
        assert portfolio.positions['ABC'].shares == 10
    
    def test_sell_with_invalid_fraction(self, portfolio):
        """Test sell with fraction clipped to 0-1."""
        portfolio.buy('ABC', 100, 1000)
        
        # Fraction > 1 should be clipped to 1
        proceeds = portfolio.sell('ABC', 110, fraction=2.0)
        assert proceeds == 1100
        assert 'ABC' not in portfolio.positions
    
    def test_sell_removes_tiny_positions(self, portfolio):
        """Test that position is removed when shares < 1e-10."""
        portfolio.buy('ABC', 100, 1000)
        portfolio.sell('ABC', 110, fraction=1.0)
        assert 'ABC' not in portfolio.positions


class TestPaperPortfolioEquity:
    """Tests for equity calculation."""
    
    def test_equity_only_cash(self, portfolio):
        """Test equity calculation with only cash."""
        assert portfolio.equity({}) == 100_000
    
    def test_equity_with_positions(self, portfolio):
        """Test equity calculation with positions."""
        portfolio.buy('ABC', 100, 1000)  # 10 shares @ $100
        
        prices = {'ABC': 110}
        equity = portfolio.equity(prices)
        
        # Cash: 99000, Position value: 10 * 110 = 1100
        assert equity == 100_100
    
    def test_equity_position_gain(self, portfolio):
        """Test equity with unrealized gain."""
        portfolio.buy('ABC', 100, 1000)  # 10 shares @ $100
        
        prices = {'ABC': 120}
        equity = portfolio.equity(prices)
        
        # Cash: 99000, Position value: 10 * 120 = 1200
        assert equity == 99000 + 1200
    
    def test_equity_position_loss(self, portfolio):
        """Test equity with unrealized loss."""
        portfolio.buy('ABC', 100, 1000)  # 10 shares @ $100
        
        prices = {'ABC': 80}
        equity = portfolio.equity(prices)
        
        # Cash: 99000, Position value: 10 * 80 = 800
        assert equity == 99000 + 800
    
    def test_equity_uses_avg_cost_fallback(self, portfolio):
        """Test equity uses avg_cost when price not provided."""
        portfolio.buy('ABC', 100, 1000)  # 10 shares @ $100
        
        # Don't provide price in prices dict
        equity = portfolio.equity({})
        
        # Should use avg cost of 100
        assert equity == 100_000
    
    def test_equity_multiple_positions(self, portfolio):
        """Test equity with multiple positions."""
        portfolio.buy('ABC', 100, 1000)  # 10 shares @ $100
        portfolio.buy('XYZ', 50, 5000)   # 100 shares @ $50
        
        prices = {'ABC': 120, 'XYZ': 60}
        equity = portfolio.equity(prices)
        
        # Cash: 94000, ABC: 10*120=1200, XYZ: 100*60=6000
        assert equity == 94000 + 1200 + 6000
        assert equity == 101_200


class TestPaperPortfolioIntegration:
    """Integration tests for portfolio operations."""
    
    def test_buy_sell_buy_cycle(self, portfolio):
        """Test buy-sell-buy cycle."""
        # Buy
        portfolio.buy('ABC', 100, 1000)
        assert portfolio.cash == 99000
        
        # Sell at profit
        portfolio.sell('ABC', 120)
        assert portfolio.cash == 100_200
        assert 'ABC' not in portfolio.positions
        
        # Buy again with profits
        portfolio.buy('ABC', 110, 1100)
        assert portfolio.cash == 99100
        assert portfolio.positions['ABC'].shares == 10
        assert portfolio.positions['ABC'].avg_cost == 110
    
    def test_portfolio_with_multiple_trades(self, portfolio):
        """Test portfolio with multiple simultaneous positions."""
        portfolio.buy('AAPL', 150, 3000)
        portfolio.buy('MSFT', 300, 3000)
        portfolio.buy('GOOG', 2500, 5000)
        
        assert portfolio.cash == 89000
        assert len(portfolio.positions) == 3
        
        # Sell one position at profit
        portfolio.sell('AAPL', 160)  # 20 shares * $160 = $3200
        assert portfolio.cash == 92_200
        assert len(portfolio.positions) == 2
