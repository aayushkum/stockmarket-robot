import argparse
from .config import Settings
from .analyzer import analyze
from .db import Database
from .universe import sp500_tickers
from .dashboard import create_app

def run_scan(settings,limit=None):
    db=Database(settings.db_path); tickers=sp500_tickers()[:limit] if limit else sp500_tickers()
    for ticker in tickers:
        try:
            r=analyze(ticker); db.save_analysis(ticker,r['analyzed_at'],r)
            print(f"{ticker:6} {r['signal']:4} score={r['master_score']:5.1f} price=${r['price']:9.2f} fair=${r['fair_value'] or 0:9.2f}")
        except Exception as e: print(f"{ticker:6} ERROR {e}")
    db.close()

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='command'); scan=sub.add_parser('scan'); scan.add_argument('--limit',type=int)
    bt=sub.add_parser('backtest'); bt.add_argument('--ticker',default='AAPL'); bt.add_argument('--period',default='5y'); sub.add_parser('dashboard'); a=p.parse_args(); s=Settings.from_env()
    if a.command=='scan': run_scan(s,a.limit)
    elif a.command=='backtest': from .backtest import moving_average_backtest; print(moving_average_backtest(a.ticker,a.period))
    else: create_app(s.db_path).run(host=s.dashboard_host,port=s.dashboard_port)
if __name__=='__main__': main()
