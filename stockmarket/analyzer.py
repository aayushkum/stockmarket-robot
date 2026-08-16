from datetime import datetime, timezone
from .data import fetch_snapshot, price_history
from .valuation import summarize
from .scoring import master_score, signal, momentum_score

def analyze(ticker):
    s=fetch_snapshot(ticker); hist=price_history(ticker,"1y"); v=summarize(s)
    m=momentum_score(hist["Close"])
    score,components=master_score(s,v,m)
    return {"ticker":ticker,"analyzed_at":datetime.now(timezone.utc).isoformat(),"price":s.price,"sector":s.sector,
            "fair_value":v.fair_value,"upside":v.upside,"valuation":v.to_dict(),"master_score":score,
            "components":components,"signal":signal(score),"snapshot":s.to_dict()}
