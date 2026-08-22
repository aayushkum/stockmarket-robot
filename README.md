# StockMarket Robot

This is a personal project I've been working on, essentially creating a stock-trading robot that attempts to systematically identify  mispriced stocks within the S&P 500, and exploit those misprices. The project has been inspired by the prevalance of trading bots in the modern stock market, and the hypothesis that a company's underlying financial performance should, over a sufficiently long period, be reflected in its market valuation. It's a mix of computer science and economic principles, built by stock analysis methods used across the industry.

## Summary

**Core Mission**: Identify overvalued and undervalued stocks in the S&P 500 by comparing estimated fair values to current market prices, then acting upon it by selling or buying said stock.

**How It Works**:
1. **Data Collection**: Fetches 19 financial metrics per stock (price, earnings, revenue, cash flow, margins, volatility, etc.) from yfinance
2. **Fair Value Estimation**: Calculates fair value using 5 independent models (DCF, earnings multiple, revenue multiple, FCF multiple, historical P/E) and takes the average
3. **Composite Scoring**: Grades each stock 0-100 based on 5 components:
   - **Valuation** (30%): Is it cheap relative to fair value?
   - **Growth** (20%): Are revenues/earnings increasing?
   - **Quality** (20%): Profitable with strong margins and ROE?
   - **Momentum** (15%): Is price trending up?
   - **Risk** (15%): Low debt, stable, reasonable volatility?
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
- **Historical Backtesting**: Configurable moving-average strategy plus full-system valuation, scoring, and paper-execution mode
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
- **`main.py`** - CLI entry point with `scan`, `backtest`, `paper-trade`, and `dashboard` subcommands
- **`dashboard.py`** - Flask web application for results visualization
- **`db.py`** - SQLite persistence layer for analyses, trades, portfolio, and positions
- **`config.py`** - Configuration management with environment variable support
- **`universe.py`** - S&P 500 ticker list management

### Data Flow
```
yfinance → fetch_snapshot() → analyzer → [valuation, scoring, momentum] 
        → master_score() → signal() → db → dashboard
```

## Code Quality
- Full type annotations and docstrings across the application
- Input validation and informative errors around external market data
- Optional file-backed snapshot cache controlled by `DATA_CACHE_HOURS`
- Shared yfinance request limiter with configurable exponential-backoff retries
- 117 automated tests covering the analysis, trading, data, and persistence layers

Test breakdown:
- `test_analyzer.py` (3) - Analysis pipeline
- `test_backtest.py` (8) - Backtesting engine, including full-system mode
- `test_config.py` (10) - Configuration management
- `test_data.py` (18) - Data fetching and validation
- `test_db.py` (9) - Database operations
- `test_paper.py` (23) - Paper portfolio simulation
- `test_scoring.py` (66) - Scoring functions and edge cases
- `test_valuation.py` (1) - Valuation models

## Project Status
The analysis and paper-trading foundation is complete and tested. The system is not connected to a brokerage and must not be treated as financial advice or as evidence of profitable trading.

Current focus areas for improvement:
- Analyzing how well the bot performs
- Performance optimization for large-scale scanning
- Additional technical indicators and signals

## Backtest Data Limitation

Price history comes from yfinance. `snapshot_builder.py` records the best available current snapshot for
each requested date and repeats it. Results using `data/aapl_snapshots.json`
are a pipeline demonstration, not a bias-free historical performance claim.

## Real Backtest Results

These results were refreshed on August 21, 2026 using five years of adjusted
daily prices from yfinance. The results are rounded for readability.

### Full-System Results: Five Stocks

This run used the complete bot: current fundamentals fed into the five
valuation models, the weighted score, the BUY/HOLD/SELL signal, and the paper
portfolio execution. Each stock was tested separately with $100,000 starting
cash. Buy and hold is the comparison where the same $100,000 stays invested
from the first price to the last price.

| Stock | Full bot ending money | Buy-and-hold ending money | Full bot return | Buy-and-hold return | Difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| AAPL | $211,978 | $211,850 | +111.98% | +111.85% | +$127 |
| MSFT | $186,108 | $165,278 | +86.11% | +65.28% | +$20,830 |
| JPM | $252,701 | $254,265 | +152.70% | +154.27% | -$1,564 |
| XOM | $355,384 | $358,296 | +255.38% | +258.30% | -$2,913 |
| GOOGL | $246,265 | $248,410 | +146.27% | +148.41% | -$2,145 |

**Result:** The full bot finished ahead on AAPL and MSFT, but behind
buy and hold on JPM, XOM, and GOOGL. Across the five separate $100,000 tests,
the full bot ended with a combined $1,252,436, compared with $1,238,099 for
buy and hold. That is $14,337 more overall, or about 1.16% above the
buy-and-hold total. This combined figure is only a simple sum of separate
single-stock tests, not a diversified portfolio result.

| Stock | Full bot CAGR | Max drawdown | Sharpe ratio | Trades |
| --- | ---: | ---: | ---: | ---: |
| AAPL | 16.24% | -33.36% | 0.68 | 1 |
| MSFT | 13.25% | -34.50% | 0.61 | 1 |
| JPM | 20.40% | -38.77% | 0.88 | 1 |
| XOM | 28.91% | -20.51% | 1.09 | 1 |
| GOOGL | 19.78% | -44.32% | 0.72 | 1 |

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
- Added configurable signal thresholds, snapshot caching, paper-trade persistence, and CI
- Preparing for further research and optional future broker integration


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

# Run a backtest using the generated snapshot fixture
python -m stockmarket backtest --ticker AAPL --period 5y --snapshots data/aapl_snapshots.json

# Analyze stocks and execute simulated trades only
python -m stockmarket paper-trade --limit 10

# Start web dashboard (also available at /portfolio)
python -m stockmarket dashboard

# Run the full-system test for every ticker with a snapshot file
python -m stockmarket.main backtest --full-system --snapshot-dir data/snapshots
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

All 115 tests pass in approximately 4 seconds covering:
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
$env:RISK_PROFILE = "5"
$env:MAX_POSITIONS = "10"
$env:MIN_SCORE_TO_BUY = "70"
$env:SELL_SCORE = "40"

# Cache and storage
$env:DATA_CACHE_HOURS = "6"
$env:DB_PATH = "./data/stockmarket.db"

# yfinance traffic controls
$env:YFINANCE_REQUEST_DELAY = "1.5"
$env:YFINANCE_MAX_RETRIES = "2"
$env:YFINANCE_RETRY_BACKOFF = "5"

# Dashboard settings
$env:DASHBOARD_HOST = "127.0.0.1"
$env:DASHBOARD_PORT = "5000"

python -m stockmarket
```

All settings have sensible defaults and are optional. The database directory is created automatically when the application starts.
