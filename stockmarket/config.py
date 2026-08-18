"""Configuration settings for the stock market robot."""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Frozen dataclass containing all configuration settings.
    
    Can be loaded from environment variables using from_env().
    
    Attributes:
        starting_cash: Initial portfolio cash in dollars.
        risk_profile: Risk tolerance level (1-10).
        max_positions: Maximum number of concurrent stock positions.
        min_score_to_buy: Minimum master score to trigger BUY signal.
        sell_score: Maximum master score to trigger SELL signal.
        cache_hours: How long to cache market data.
        db_path: Path to SQLite database file.
        dashboard_host: Flask dashboard host address.
        dashboard_port: Flask dashboard port number.
    """
    starting_cash: float = 100_000.0
    risk_profile: int = 5
    max_positions: int = 20
    min_score_to_buy: float = 70.0
    sell_score: float = 40.0
    cache_hours: float = 6.0
    db_path: str = "data/stockmarket.db"
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 5000

    @classmethod
    def from_env(cls) -> 'Settings':
        """Create Settings instance from environment variables.
        
        Environment variables (with defaults):
        - STARTING_CASH: Portfolio starting cash (default: 100000)
        - RISK_PROFILE: Risk tolerance 1-10 (default: 5)
        - MAX_POSITIONS: Max positions (default: 20)
        - MIN_SCORE_TO_BUY: Buy threshold (default: 70)
        - SELL_SCORE: Sell threshold (default: 40)
        - DATA_CACHE_HOURS: Cache duration (default: 6)
        - DB_PATH: Database path (default: data/stockmarket.db)
        - DASHBOARD_HOST: Flask host (default: 127.0.0.1)
        - DASHBOARD_PORT: Flask port (default: 5000)
        
        Returns:
            Settings instance with values from environment or defaults.
        """
        return cls(
            starting_cash=float(os.getenv("STARTING_CASH", cls.starting_cash)),
            risk_profile=int(os.getenv("RISK_PROFILE", cls.risk_profile)),
            max_positions=int(os.getenv("MAX_POSITIONS", cls.max_positions)),
            min_score_to_buy=float(os.getenv("MIN_SCORE_TO_BUY", cls.min_score_to_buy)),
            sell_score=float(os.getenv("SELL_SCORE", cls.sell_score)),
            cache_hours=float(os.getenv("DATA_CACHE_HOURS", cls.cache_hours)),
            db_path=os.getenv("DB_PATH", cls.db_path),
            dashboard_host=os.getenv("DASHBOARD_HOST", cls.dashboard_host),
            dashboard_port=int(os.getenv("DASHBOARD_PORT", cls.dashboard_port)),
        )
