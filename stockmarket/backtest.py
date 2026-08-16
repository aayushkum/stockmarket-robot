import numpy as np
import yfinance as yf

def moving_average_backtest(ticker,period="5y"):
    df=yf.Ticker(ticker).history(period=period,auto_adjust=True)
    if df.empty: raise ValueError(f"No history for {ticker}")
    close=df["Close"].dropna(); ma50=close.rolling(50).mean(); ma200=close.rolling(200).mean()
    sig=(ma50>ma200).astype(int).shift(1).fillna(0); daily=close.pct_change().fillna(0); strat=sig*daily
    equity=(1+strat).cumprod(); benchmark=(1+daily).cumprod(); years=max((close.index[-1]-close.index[0]).days/365.25,1/365.25)
    cagr=equity.iloc[-1]**(1/years)-1; dd=(equity/equity.cummax()-1).min(); vol=strat.std()*np.sqrt(252); sharpe=strat.mean()*252/vol if vol>0 else 0
    return {"ticker":ticker,"period":period,"strategy_return":float(equity.iloc[-1]-1),"benchmark_return":float(benchmark.iloc[-1]-1),"cagr":float(cagr),"max_drawdown":float(dd),"sharpe":float(sharpe),"observations":int(len(close))}
