import json, sqlite3
from pathlib import Path

class Database:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS analyses(ticker TEXT PRIMARY KEY, analyzed_at TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, ticker TEXT NOT NULL, side TEXT NOT NULL, shares REAL NOT NULL, price REAL NOT NULL, value REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS portfolio(id INTEGER PRIMARY KEY CHECK(id=1), cash REAL NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS positions(ticker TEXT PRIMARY KEY, shares REAL NOT NULL, avg_cost REAL NOT NULL);
        """)
        self.conn.commit()
    def save_analysis(self, ticker, analyzed_at, payload):
        self.conn.execute("INSERT OR REPLACE INTO analyses VALUES(?,?,?)", (ticker, analyzed_at, json.dumps(payload)))
        self.conn.commit()
    def latest_analyses(self, limit=50):
        rows=self.conn.execute("SELECT payload FROM analyses ORDER BY analyzed_at DESC LIMIT ?",(limit,)).fetchall()
        return [json.loads(r[0]) for r in rows]
    def close(self): self.conn.close()
