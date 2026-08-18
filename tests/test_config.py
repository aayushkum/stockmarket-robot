"""Tests for the config module."""
import pytest
import os
from stockmarket.config import Settings


def test_config_defaults():
    """Test that Settings has correct default values."""
    settings = Settings()
    
    assert settings.starting_cash == 100_000.0
    assert settings.risk_profile == 5
    assert settings.max_positions == 20
    assert settings.min_score_to_buy == 70.0
    assert settings.sell_score == 40.0
    assert settings.cache_hours == 6.0
    assert settings.db_path == "data/stockmarket.db"
    assert settings.dashboard_host == "127.0.0.1"
    assert settings.dashboard_port == 5000


def test_config_from_env_uses_defaults(monkeypatch):
    """Test that from_env uses defaults when env vars not set."""
    # Clear any existing env vars
    monkeypatch.delenv("STARTING_CASH", raising=False)
    monkeypatch.delenv("RISK_PROFILE", raising=False)
    
    settings = Settings.from_env()
    assert settings.starting_cash == 100_000.0
    assert settings.risk_profile == 5


def test_config_from_env_reads_starting_cash(monkeypatch):
    """Test that from_env reads STARTING_CASH."""
    monkeypatch.setenv("STARTING_CASH", "50000")
    settings = Settings.from_env()
    assert settings.starting_cash == 50000.0


def test_config_from_env_reads_risk_profile(monkeypatch):
    """Test that from_env reads RISK_PROFILE."""
    monkeypatch.setenv("RISK_PROFILE", "8")
    settings = Settings.from_env()
    assert settings.risk_profile == 8


def test_config_from_env_reads_max_positions(monkeypatch):
    """Test that from_env reads MAX_POSITIONS."""
    monkeypatch.setenv("MAX_POSITIONS", "30")
    settings = Settings.from_env()
    assert settings.max_positions == 30


def test_config_from_env_reads_min_score_to_buy(monkeypatch):
    """Test that from_env reads MIN_SCORE_TO_BUY."""
    monkeypatch.setenv("MIN_SCORE_TO_BUY", "75")
    settings = Settings.from_env()
    assert settings.min_score_to_buy == 75.0


def test_config_from_env_reads_sell_score(monkeypatch):
    """Test that from_env reads SELL_SCORE."""
    monkeypatch.setenv("SELL_SCORE", "35")
    settings = Settings.from_env()
    assert settings.sell_score == 35.0


def test_config_from_env_reads_cache_hours(monkeypatch):
    """Test that from_env reads DATA_CACHE_HOURS."""
    monkeypatch.setenv("DATA_CACHE_HOURS", "12")
    settings = Settings.from_env()
    assert settings.cache_hours == 12.0


def test_config_from_env_reads_db_path(monkeypatch):
    """Test that from_env reads DB_PATH."""
    monkeypatch.setenv("DB_PATH", "/custom/path/stockmarket.db")
    settings = Settings.from_env()
    assert settings.db_path == "/custom/path/stockmarket.db"


def test_config_from_env_reads_dashboard_host(monkeypatch):
    """Test that from_env reads DASHBOARD_HOST."""
    monkeypatch.setenv("DASHBOARD_HOST", "0.0.0.0")
    settings = Settings.from_env()
    assert settings.dashboard_host == "0.0.0.0"


def test_config_from_env_reads_dashboard_port(monkeypatch):
    """Test that from_env reads DASHBOARD_PORT."""
    monkeypatch.setenv("DASHBOARD_PORT", "8080")
    settings = Settings.from_env()
    assert settings.dashboard_port == 8080


def test_config_is_frozen():
    """Test that Settings is immutable (frozen)."""
    settings = Settings()
    
    with pytest.raises(AttributeError):
        settings.starting_cash = 200_000.0


def test_config_all_env_vars_together(monkeypatch):
    """Test reading all environment variables together."""
    monkeypatch.setenv("STARTING_CASH", "75000")
    monkeypatch.setenv("RISK_PROFILE", "9")
    monkeypatch.setenv("MAX_POSITIONS", "25")
    monkeypatch.setenv("MIN_SCORE_TO_BUY", "72")
    monkeypatch.setenv("SELL_SCORE", "38")
    monkeypatch.setenv("DATA_CACHE_HOURS", "8")
    monkeypatch.setenv("DB_PATH", "/tmp/sm.db")
    monkeypatch.setenv("DASHBOARD_HOST", "localhost")
    monkeypatch.setenv("DASHBOARD_PORT", "3000")
    
    settings = Settings.from_env()
    
    assert settings.starting_cash == 75000.0
    assert settings.risk_profile == 9
    assert settings.max_positions == 25
    assert settings.min_score_to_buy == 72.0
    assert settings.sell_score == 38.0
    assert settings.cache_hours == 8.0
    assert settings.db_path == "/tmp/sm.db"
    assert settings.dashboard_host == "localhost"
    assert settings.dashboard_port == 3000
