# StockMarket Robot

This is a personal project I've been working on, essentially creating a stock-trading robot that attempts to systematically identify  mispriced stocks within the S&P 500, and exploit those misprices. The project has been inspired by the prevalance of trading bots in the modern stock market, and the hypothesis that a company's underlying financial performance should, over a sufficiently long period, be reflected in its market valuation. It's a mix of computer science and economic principles, built by stock analysis methods used across the industry.

## Summary

**Core Mission**: Identify overvalued and undervalued stocks in the S&P 500 by comparing estimated fair values to current market prices, then acting upon it by selling or buying said stock.

**How It Works**:
1. **Data Collection**: Fetches 19 financial metrics per stock (price, earnings, revenue, cash flow, margins, volatility, etc.) from yfinance
2. **Fair Value Estimation**: Calculates fair value using 5 independent models (DCF, earnings multiple, revenue multiple, FCF multiple, historical P/E) and takes the average
3. **Composite Scoring**: Grades each stock 0-100 based on 5 components:
   - **Valuation** (30%): Is it cheap relative to fair value?
   - **Growth** (20%): Are revenues/earnings increasing (and by how much)?
   - **Quality** (20%): Is it profitable, with strong margins and ROE?
   - **Momentum** (15%): Is price trending up or down in the near past?
   - **Risk** (15%): Low debt, stock stability, reasonable volatility?
4. **Trading Signals**: Generates BUY (≥70), HOLD (40-69), or SELL (≤40) recommendations
5. **Paper Trading**: Simulates buy/sell execution with position tracking and equity calculation
6. **Risk Management**: Enforces portfolio constraints (position limits, max daily trades, etc.) to prevent rash decisions

**Current State**: Paper trading only. Built as a learning project focused on systematic stock analysis.


## Features
- **Market Data**: Real-time data via yfinance with validation and error handling
- **Valuation Models**: 5 different approaches (DCF proxy, earnings multiple, FCF multiple, revenue multiple, historical P/E)
- **Scoring Engine**: Composite 0-100 score from 5 components (valuation, growth, quality, momentum, risk)
- **Trading Signals**: BUY (≥70), HOLD (40-69), SELL (≤40)
- **Paper Trading**: Full portfolio simulation with position management and equity tracking
- **Historical Backtesting**: 50/200-day moving average crossover strategy with performance metrics
- **Persistent Storage**: SQLite database for analyses, trades, portfolio state
- **Web Dashboard**: Flask-based UI for viewing real-time analysis results
- **S&P 500 Support**: Automated analysis across all 500 constituents
- **Risk Management**: Portfolio constraints and position limits

## Architecture

The project uses the following modular architecture:

### Core Modules
- **`data.py`** - yfinance integration with `Snapshot` dataclass (19 financial metrics)
- **`valuation.py`** - Fair value estimation combining 5 independent models
- **`scoring.py`** - Component scoring (30% valuation, 20% growth, 20% quality, 15% momentum, 15% risk)
- **`analyzer.py`** - Main analysis pipeline combining all components
- **`paper.py`** - Paper portfolio engine with position tracking and equity calculation
- **`backtest.py`** - Historical strategy testing with performance analytics
- **`main.py`** - CLI entry point with `scan`, `backtest`, and `dashboard` subcommands
- **`dashboard.py`** - Flask web application for results visualization
- **`db.py`** - SQLite persistence layer with connection pooling
- **`config.py`** - Configuration management with environment variable support
- **`universe.py`** - S&P 500 ticker list management

### Data Flow
```
yfinance → fetch_snapshot() → analyzer → [valuation, scoring, momentum] 
        → master_score() → signal() → db → dashboard
```

## Architecture
  - `test_analyzer.py` (3 tests) - Analysis pipeline
  - `test_backtest.py` (6 tests) - Backtesting engine
  - `test_config.py` (10 tests) - Configuration management
  - `test_data.py` (17 tests) - Data fetching and validation
  - `test_db.py` (9 tests) - Database operations
  - `test_paper.py` (23 tests) - Paper portfolio simulation
  - `test_scoring.py` (66 tests) - Scoring functions and edge cases
  - `test_valuation.py` (1 test) - Valuation models

## Project Status
While this is still a work in progress, major parts have already been completed throughout, including stock analysis, tests for the code, and connection to real-time markets.

Current focus areas for improvement:
- Analyzing how well the bot performs
- Performance optimization for large-scale scanning
- Additional technical indicators and signals

## Timeline
#### July 2026: Research and Planning
- Sparked by the $15 billion loss from Jane Street Situational Awareness, began researching the architecture of stock trading bots.
- Analyzed the mechanics behind major trading algorithms across quantitative finance industries.
- Designed a high-level system architecture, creating the fundamentals for what would become my trading bot.

#### July 28th - August 15th 2026: Local Development
- Initiated bot development locally using Python and VS Code.
- Built out core features, focusing on valuation models and integration of key components.
- Mastered yfinance and related topics to optimize the bot.

#### August 15th 2026 - Present: Production Hardening & Documentation
- Standardized codebase quality metrics
- Updated documentation to reflect all architectural improvements
- Preparing for real trading integration and autonomous operation


## Windows setup
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m stockmarket
```
Open http://127.0.0.1:5000.

## Commands
```powershell
# Scan S&P 500 for investment opportunities (limited to 10 stocks)
python -m stockmarket scan --limit 10

# Run historical backtest on specific ticker
python -m stockmarket backtest --ticker AAPL --period 5y

# Start web dashboard
python -m stockmarket
```

## Testing

Run the complete test suite:
```powershell
python -m pytest tests/ -v
```

Run specific test file:
```powershell
python -m pytest tests/test_scoring.py -v
```

Run tests with coverage:
```powershell
python -m pytest tests/ --cov=stockmarket --cov-report=html
```

All 112 tests pass in ~6.67 seconds covering:
- Data fetching and validation
- Valuation model accuracy
- Scoring functions and edge cases
- Portfolio management and trades
- Configuration management
- Database operations
- Analysis pipeline integration

## Configuration

Configure via environment variables:

```powershell
# Trading parameters
$env:STARTING_CASH = "100000"
$env:RISK_PROFILE = "moderate"
$env:MAX_POSITIONS = "10"
$env:MIN_SCORE_TO_BUY = "70"
$env:SELL_SCORE = "40"

# Cache and storage
$env:DATA_CACHE_HOURS = "6"
$env:DB_PATH = "./data/stockmarket.db"

# Dashboard settings
$env:DASHBOARD_HOST = "127.0.0.1"
$env:DASHBOARD_PORT = "5000"

python -m stockmarket
```

All settings have defaults created for a reasonable environment, and are optional, they may be changed by the user to fit specifications.
