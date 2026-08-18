"""Tests for the database module."""
import pytest
import tempfile
import json
from pathlib import Path
from stockmarket.db import Database


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        yield db
        db.close()


def test_database_creates_file(temp_db):
    """Test that database creates SQLite file."""
    # Get the database path from the connection before closing
    db_list = temp_db.conn.execute("PRAGMA database_list").fetchall()
    db_file = db_list[0][2]
    
    # Close the connection
    temp_db.conn.close()
    
    # File should exist after creation
    assert Path(db_file).exists()


def test_save_and_retrieve_analysis(temp_db):
    """Test saving and retrieving an analysis."""
    test_data = {
        "ticker": "AAPL",
        "price": 150.0,
        "master_score": 75.5,
        "signal": "BUY"
    }
    
    temp_db.save_analysis("AAPL", "2024-01-01T12:00:00Z", test_data)
    
    analyses = temp_db.latest_analyses(limit=1)
    assert len(analyses) == 1
    assert analyses[0]["ticker"] == "AAPL"
    assert analyses[0]["price"] == 150.0
    assert analyses[0]["signal"] == "BUY"


def test_get_specific_analysis(temp_db):
    """Test retrieving specific analysis by ticker."""
    test_data = {
        "ticker": "MSFT",
        "price": 300.0,
        "master_score": 65.0,
        "signal": "HOLD"
    }
    
    temp_db.save_analysis("MSFT", "2024-01-01T12:00:00Z", test_data)
    
    result = temp_db.get_analysis("MSFT")
    assert result is not None
    assert result["ticker"] == "MSFT"
    assert result["price"] == 300.0


def test_get_nonexistent_analysis(temp_db):
    """Test retrieving analysis that doesn't exist."""
    result = temp_db.get_analysis("NONEXISTENT")
    assert result is None


def test_latest_analyses_limit(temp_db):
    """Test that limit parameter works."""
    # Save 5 analyses
    for i in range(5):
        data = {"ticker": f"TEST{i}", "price": 100.0 + i}
        temp_db.save_analysis(f"TEST{i}", "2024-01-01T12:00:00Z", data)
    
    # Request only 2
    analyses = temp_db.latest_analyses(limit=2)
    assert len(analyses) == 2


def test_save_overwrites_previous(temp_db):
    """Test that saving with same ticker overwrites."""
    data1 = {"ticker": "AAPL", "price": 150.0}
    data2 = {"ticker": "AAPL", "price": 160.0}
    
    temp_db.save_analysis("AAPL", "2024-01-01T12:00:00Z", data1)
    temp_db.save_analysis("AAPL", "2024-01-02T12:00:00Z", data2)
    
    analyses = temp_db.latest_analyses()
    # Should only have one AAPL entry
    aapl_analyses = [a for a in analyses if a["ticker"] == "AAPL"]
    assert len(aapl_analyses) == 1
    assert aapl_analyses[0]["price"] == 160.0


def test_analyses_ordered_by_date(temp_db):
    """Test that analyses are returned newest first."""
    for i in range(3):
        data = {"ticker": f"TEST{i}", "index": i}
        temp_db.save_analysis(
            f"TEST{i}",
            f"2024-01-0{i+1}T12:00:00Z",
            data
        )
    
    analyses = temp_db.latest_analyses(limit=3)
    # Should be newest first (TEST2, TEST1, TEST0)
    assert analyses[0]["index"] == 2
    assert analyses[1]["index"] == 1
    assert analyses[2]["index"] == 0


def test_database_serializes_complex_objects(temp_db):
    """Test that complex nested objects are serialized."""
    test_data = {
        "ticker": "AAPL",
        "valuation": {
            "estimates": [
                {"model": "dcf", "fair_value": 150.0},
                {"model": "pe", "fair_value": 155.0}
            ],
            "fair_value": 152.5
        },
        "components": {
            "valuation": 75.0,
            "growth": 70.0,
            "quality": 80.0
        }
    }
    
    temp_db.save_analysis("AAPL", "2024-01-01T12:00:00Z", test_data)
    
    result = temp_db.get_analysis("AAPL")
    assert result["valuation"]["fair_value"] == 152.5
    assert len(result["valuation"]["estimates"]) == 2
    assert result["components"]["valuation"] == 75.0
