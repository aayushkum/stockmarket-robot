# StockMarket Robot

This is a personal project I'm building to make a stock-trading robot. It includes explainable S&P 500 research, valuation, backtesting, and a paper-trading system. 

The basic idea is an algorithm that, through publically avalible financial data, estimates what a stock is actually worth, compares that estimate to the current price, then use that to decide whether the stock looks like a BUY, HOLD, or SELL. For each stock, it looks at things like: Valuation, Earnings, Revenue growth, Free Cash Flow, Profitability, Momentum and Risk. Before a final trade, it goes through a risk-management algorithm, to ensure the bot stays within the realm of possibility. It is not currently connected to a real trading algorithm, merely serving to do paper trading. I'm building this as a learning project, so the goal isn't to make some magical formula that predicts the stock market, nor to actually make real money.


## Features
- yfinance market/fundamental data
- SQLite persistence
- Multiple valuation models with arithmetic-mean fair value
- Explainable 0–100 master score
- BUY / HOLD / SELL signals
- Paper portfolio engine
- Historical backtesting

## Architecture

The project is split into a few main parts:

- `data/` - gets and stores market data
- `valuation/` - calculates fair-value estimates
- `scoring/` - combines the different signals
- `portfolio/` - manages the paper portfolio
- `backtesting/` - tests strategies against historical data
- `dashboard/` - displays results
- `database/` - handles persistent data

## Project Status
This is still very much a work in progress. The current version is the foundation of the project. There are a lot of things I still want to improve, especially the valuation models. 

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
