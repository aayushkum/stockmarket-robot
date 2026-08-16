# StockMarket Robot

Explainable S&P 500 research, valuation, backtesting, and paper-trading system. 

## Features
- yfinance market/fundamental data
- SQLite persistence
- Multiple valuation models with arithmetic-mean fair value
- Explainable 0–100 master score
- BUY / HOLD / SELL signals
- Paper portfolio engine
- Historical backtesting
- Lightweight Flask dashboard

> Research/paper trading only. No live-money order execution.

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
python -m stockmarket scan --limit 10
python -m stockmarket backtest --ticker AAPL --period 5y
python -m stockmarket
```
