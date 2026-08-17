import json
import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row

        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS analyses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                analyzed_at TEXT NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_analyses_ticker_time
            ON analyses(ticker, analyzed_at DESC);

            CREATE INDEX IF NOT EXISTS idx_analyses_time
            ON analyses(analyzed_at DESC);

            CREATE TABLE IF NOT EXISTS trades(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                ticker TEXT NOT NULL,
                side TEXT NOT NULL,
                shares REAL NOT NULL,
                price REAL NOT NULL,
                value REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS portfolio(
                id INTEGER PRIMARY KEY CHECK(id=1),
                cash REAL NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS positions(
                ticker TEXT PRIMARY KEY,
                shares REAL NOT NULL,
                avg_cost REAL NOT NULL
            );
            """
        )

        self.conn.commit()

    # ------------------------------------------------------------
    # ANALYSES
    # ------------------------------------------------------------

    def save_analysis(self, ticker, analyzed_at, payload):
        """
        Append a new analysis.

        IMPORTANT:
        This does NOT overwrite previous analysis records.
        Historical observations are necessary for later research
        and backtesting.
        """
        self.conn.execute(
            """
            INSERT INTO analyses(ticker, analyzed_at, payload)
            VALUES (?, ?, ?)
            """,
            (
                ticker,
                analyzed_at,
                json.dumps(payload),
            ),
        )

        self.conn.commit()

    def latest_analyses(self, limit=50):
        rows = self.conn.execute(
            """
            SELECT a.payload
            FROM analyses a
            INNER JOIN (
                SELECT ticker, MAX(analyzed_at) AS latest
                FROM analyses
                GROUP BY ticker
            ) latest
            ON a.ticker = latest.ticker
            AND a.analyzed_at = latest.latest
            ORDER BY a.analyzed_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [json.loads(row["payload"]) for row in rows]

    def analyses_for_ticker(self, ticker, limit=500):
        rows = self.conn.execute(
            """
            SELECT payload
            FROM analyses
            WHERE ticker = ?
            ORDER BY analyzed_at DESC
            LIMIT ?
            """,
            (ticker, limit),
        ).fetchall()

        return [json.loads(row["payload"]) for row in rows]

    def analysis_count(self, ticker=None):
        if ticker is None:
            row = self.conn.execute(
                "SELECT COUNT(*) AS count FROM analyses"
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT COUNT(*) AS count FROM analyses WHERE ticker = ?",
                (ticker,),
            ).fetchone()

        return int(row["count"])

    # ------------------------------------------------------------
    # PORTFOLIO
    # ------------------------------------------------------------

    def save_portfolio(self, cash, updated_at):
        self.conn.execute(
            """
            INSERT INTO portfolio(id, cash, updated_at)
            VALUES(1, ?, ?)
            ON CONFLICT(id)
            DO UPDATE SET
                cash=excluded.cash,
                updated_at=excluded.updated_at
            """,
            (cash, updated_at),
        )

        self.conn.commit()

    def load_portfolio(self):
        row = self.conn.execute(
            """
            SELECT cash, updated_at
            FROM portfolio
            WHERE id=1
            """
        ).fetchone()

        if row is None:
            return None

        return {
            "cash": float(row["cash"]),
            "updated_at": row["updated_at"],
        }

    def save_position(self, ticker, shares, avg_cost):
        if shares <= 0:
            self.conn.execute(
                "DELETE FROM positions WHERE ticker = ?",
                (ticker,),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO positions(ticker, shares, avg_cost)
                VALUES (?, ?, ?)
                ON CONFLICT(ticker)
                DO UPDATE SET
                    shares=excluded.shares,
                    avg_cost=excluded.avg_cost
                """,
                (ticker, shares, avg_cost),
            )

        self.conn.commit()

    def load_positions(self):
        rows = self.conn.execute(
            """
            SELECT ticker, shares, avg_cost
            FROM positions
            ORDER BY ticker
            """
        ).fetchall()

        return {
            row["ticker"]: {
                "shares": float(row["shares"]),
                "avg_cost": float(row["avg_cost"]),
            }
            for row in rows
        }

    def save_trade(
        self,
        timestamp,
        ticker,
        side,
        shares,
        price,
        value,
    ):
        self.conn.execute(
            """
            INSERT INTO trades(
                timestamp,
                ticker,
                side,
                shares,
                price,
                value
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                ticker,
                side,
                shares,
                price,
                value,
            ),
        )

        self.conn.commit()

    def trades(self, limit=100):
        rows = self.conn.execute(
            """
            SELECT
                id,
                timestamp,
                ticker,
                side,
                shares,
                price,
                value
            FROM trades
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [dict(row) for row in rows]

    def close(self):
        self.conn.close()
