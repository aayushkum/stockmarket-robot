# StockMarket Robot

This is a personal project I've been working on, essentially creating a stock-trading robot that attempts to systematically identify  mispriced stocks within the S&P 500, and exploit those misprices. The project has been inspired by the prevalance of trading bots in the modern stock market, and the hypothesis that a company's underlying financial performance should, over a sufficiently long period, be reflected in its market valuation. It's a mix of computer science and economic principles, built by stock analysis methods used across the industry.

## Summary

The basic idea is an algorithm that, through publically avalible financial data, estimates what a stock is actually worth, compares that estimate to the current price, then use that to decide whether the stock should be bought, held or sold. For each stock, it looks at things like: Valuation, Earnings, Revenue Growth, Free Cash Flow, Profitability, Volatility and Risk. These fundamentals are replenshied every few hours, and the stock market price is updated every minute, to allow for the bot to find discrepancies between the stock's predicted price and current price. Based on its confidence in the order, the difference in price, and avalibility in cash, it gives each stock a master score from 0-100. After doing this for all 500 stocks on the S&P 500, it can then decide to place a speculative order for buying/selling a certain number of whatever stock is performing the highest.

Before a final trade is made, it goes through a risk-management algorithm that is based around certain unalienable rules (stocks cannot be over a certain percent of the total portfolio, only a certain amount of stock can be traded daily etc.), to ensure the bot stays within the realm of possibility, and does not commit to rash actions. The risk-management algorithm serves to place the final trade offer, but not in real-life. It is not currently connected to a real trading algorithm that risks cash, instead, merely serving to do paper trading. I'm building this as a learning project, so the goal isn't to make real money.


## Features
- yfinance market/fundamental data
- SQLite 
- Multiple valuation models 
- 0–100 master score
- BUY / HOLD / SELL signals
- Paper portfolio engine
- Historical backtesting (Coming Soon)

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
