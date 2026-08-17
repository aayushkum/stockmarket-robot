from dataclasses import dataclass


@dataclass
class Position:
    shares: float
    avg_cost: float


class PaperPortfolio:
    """
    Simple paper-trading portfolio.

    This class is intentionally independent of a brokerage API.
    It handles accounting only.
    """

    def __init__(self, settings, database=None):
        self.settings = settings
        self.database = database

        self.cash = float(settings.starting_cash)
        self.positions = {}

        if self.database is not None:
            self._load()

    def _load(self):
        """
        Restore the portfolio from SQLite if a saved portfolio exists.
        """
        saved = self.database.load_portfolio()

        if saved is not None:
            self.cash = saved["cash"]

        saved_positions = self.database.load_positions()

        self.positions = {
            ticker: Position(
                shares=data["shares"],
                avg_cost=data["avg_cost"],
            )
            for ticker, data in saved_positions.items()
        }

    def _persist(self, timestamp=None):
        if self.database is None:
            return

        if timestamp is None:
            from datetime import datetime, timezone

            timestamp = datetime.now(timezone.utc).isoformat()

        self.database.save_portfolio(
            cash=self.cash,
            updated_at=timestamp,
        )

        for ticker, position in self.positions.items():
            self.database.save_position(
                ticker=ticker,
                shares=position.shares,
                avg_cost=position.avg_cost,
            )

    def buy(self, ticker, price, amount, timestamp=None):
        """
        Buy a dollar amount of a stock.

        Returns True if the order was accepted.
        """
        try:
            price = float(price)
            amount = float(amount)
        except (TypeError, ValueError):
            return False

        if price <= 0:
            return False

        if amount <= 0:
            return False

        if amount > self.cash:
            return False

        shares = amount / price

        old = self.positions.get(ticker)

        if old is None:
            self.positions[ticker] = Position(
                shares=shares,
                avg_cost=price,
            )
        else:
            total_shares = old.shares + shares

            old.avg_cost = (
                old.shares * old.avg_cost
                + shares * price
            ) / total_shares

            old.shares = total_shares

        self.cash -= amount

        if self.database is not None:
            self.database.save_trade(
                timestamp=timestamp or self._timestamp(),
                ticker=ticker,
                side="BUY",
                shares=shares,
                price=price,
                value=amount,
            )

        self._persist(timestamp)

        return True

    def sell(self, ticker, price, fraction=1.0, timestamp=None):
        try:
            price = float(price)
            fraction = float(fraction)
        except (TypeError, ValueError):
            return 0.0

        position = self.positions.get(ticker)

        if position is None:
            return 0.0

        if price <= 0:
            return 0.0

        fraction = max(0.0, min(1.0, fraction))

        shares = position.shares * fraction

        if shares <= 0:
            return 0.0

        proceeds = shares * price

        position.shares -= shares
        self.cash += proceeds

        if position.shares < 1e-10:
            del self.positions[ticker]

        if self.database is not None:
            self.database.save_trade(
                timestamp=timestamp or self._timestamp(),
                ticker=ticker,
                side="SELL",
                shares=shares,
                price=price,
                value=proceeds,
            )

            self.database.save_position(
                ticker=ticker,
                shares=position.shares if ticker in self.positions else 0.0,
                avg_cost=(
                    self.positions[ticker].avg_cost
                    if ticker in self.positions
                    else 0.0
                ),
            )

        self._persist(timestamp)

        return proceeds

    def equity(self, prices):
        total = self.cash

        for ticker, position in self.positions.items():
            price = prices.get(ticker)

            if price is None:
                price = position.avg_cost

            total += position.shares * price

        return total

    def position_value(self, ticker, price):
        position = self.positions.get(ticker)

        if position is None:
            return 0.0

        return position.shares * price

    def portfolio_weights(self, prices):
        total = self.equity(prices)

        if total <= 0:
            return {}

        weights = {}

        for ticker, position in self.positions.items():
            price = prices.get(ticker, position.avg_cost)
            weights[ticker] = position.shares * price / total

        return weights

    def _timestamp(self):
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
