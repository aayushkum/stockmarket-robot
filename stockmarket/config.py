from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
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
    def from_env(cls):
        return cls(
            starting_cash=float(os.getenv("STARTING_CASH", cls.starting_cash)),
            risk_profile=int(os.getenv("RISK_PROFILE", cls.risk_profile)),
            max_positions=int(os.getenv("MAX_POSITIONS", cls.max_positions)),
            min_score_to_buy=float(os.getenv("MIN_SCORE_TO_BUY", cls.min_score_to_buy)),
            sell_score=float(os.getenv("SELL_SCORE", cls.sell_score)),
            cache_hours=float(os.getenv("DATA_CACHE_HOURS", cls.cache_hours)),
        )
