"""Paper trading portfolio engine for simulated trading."""
from dataclasses import dataclass
from typing import Dict, Optional

from .config import Settings


@dataclass
class Position:
    """Current position in a single stock.
    
    Attributes:
        shares: Number of shares held.
        avg_cost: Average cost per share.
    """
    shares: float
    avg_cost: float


class PaperPortfolio:
    """Simulated paper trading portfolio.
    
    Tracks cash, positions, and executes buy/sell trades at given prices
    without real money or execution.
    """
    
    def __init__(self, settings: Settings) -> None:
        """Initialize portfolio with starting cash.
        
        Args:
            settings: Configuration with starting_cash.
        """
        self.settings = settings
        self.cash = settings.starting_cash
        self.positions: Dict[str, Position] = {}
    
    def buy(self, ticker: str, price: float, amount: float) -> bool:
        """Execute a buy order.
        
        Args:
            ticker: Stock ticker to buy.
            price: Price per share.
            amount: Dollar amount to spend.
            
        Returns:
            True if buy successful, False if insufficient cash or invalid price.
        """
        if amount <= 0 or price <= 0 or amount > self.cash:
            return False
        
        shares = amount / price
        existing = self.positions.get(ticker)
        
        if existing:
            # Update existing position
            total_shares = existing.shares + shares
            existing.avg_cost = (existing.shares * existing.avg_cost + amount) / total_shares
            existing.shares = total_shares
        else:
            # New position
            self.positions[ticker] = Position(shares, price)
        
        self.cash -= amount
        return True
    
    def sell(self, ticker: str, price: float, fraction: float = 1.0) -> float:
        """Execute a sell order.
        
        Args:
            ticker: Stock ticker to sell.
            price: Price per share.
            fraction: Fraction of position to sell (0-1).
            
        Returns:
            Dollar amount received from sale.
        """
        position = self.positions.get(ticker)
        if not position or price <= 0:
            return 0
        
        # Sell fraction of position
        sell_fraction = max(0, min(1, fraction))
        shares_to_sell = position.shares * sell_fraction
        proceeds = shares_to_sell * price
        
        position.shares -= shares_to_sell
        self.cash += proceeds
        
        # Remove position if completely sold
        if position.shares < 1e-10:
            del self.positions[ticker]
        
        return proceeds
    
    def equity(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio equity.
        
        Args:
            prices: Dict mapping ticker to current price.
            
        Returns:
            Total equity (cash + position values).
        """
        position_value = sum(
            pos.shares * prices.get(ticker, pos.avg_cost)
            for ticker, pos in self.positions.items()
        )
        return self.cash + position_value
