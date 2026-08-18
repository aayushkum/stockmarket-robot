"""SQLite database persistence layer."""
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional


class Database:
    """SQLite database for storing analyses and trades.
    
    Tables:
    - analyses: Master analysis results
    - trades: Individual trade execution history
    - portfolio: Current portfolio cash
    - positions: Current stock positions
    """
    
    def __init__(self, path: str) -> None:
        """Initialize database connection and create tables if needed.
        
        Args:
            path: Path to SQLite database file.
        """
        # Create directory if it doesn't exist
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        
        # Create tables
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS analyses (
            ticker TEXT PRIMARY KEY,
            analyzed_at TEXT NOT NULL,
            payload TEXT NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ticker TEXT NOT NULL,
            side TEXT NOT NULL,
            shares REAL NOT NULL,
            price REAL NOT NULL,
            value REAL NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY CHECK(id=1),
            cash REAL NOT NULL,
            updated_at TEXT NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS positions (
            ticker TEXT PRIMARY KEY,
            shares REAL NOT NULL,
            avg_cost REAL NOT NULL
        );
        """)
        self.conn.commit()
    
    def save_analysis(self, ticker: str, analyzed_at: str, payload: Dict[str, Any]) -> None:
        """Save analysis result to database.
        
        Args:
            ticker: Stock ticker symbol.
            analyzed_at: ISO timestamp of analysis.
            payload: Analysis result dictionary.
        """
        self.conn.execute(
            "INSERT OR REPLACE INTO analyses VALUES (?, ?, ?)",
            (ticker, analyzed_at, json.dumps(payload))
        )
        self.conn.commit()
    
    def latest_analyses(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve latest analyses.
        
        Args:
            limit: Maximum number of analyses to return.
            
        Returns:
            List of analysis dictionaries, newest first.
        """
        rows = self.conn.execute(
            "SELECT payload FROM analyses ORDER BY analyzed_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [json.loads(r[0]) for r in rows]
    
    def get_analysis(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis for a specific ticker.
        
        Args:
            ticker: Stock ticker symbol.
            
        Returns:
            Analysis dictionary or None if not found.
        """
        row = self.conn.execute(
            "SELECT payload FROM analyses WHERE ticker = ?",
            (ticker,)
        ).fetchone()
        return json.loads(row[0]) if row else None
    
    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
