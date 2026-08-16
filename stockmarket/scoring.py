def clamp(x,lo=0,hi=100): return max(lo,min(hi,x))
def valuation_score(v): return 50 if v.upside is None else clamp(50+v.upside*100)
def growth_score(s):
    v=[x for x in (s.revenue_growth,s.earnings_growth) if x is not None]
    return clamp(50+(sum(v)/len(v))*150) if v else 50
def quality_score(s):
    p=[]
    if s.profit_margin is not None: p.append(clamp(50+s.profit_margin*200))
    if s.operating_margin is not None: p.append(clamp(50+s.operating_margin*150))
    if s.return_on_equity is not None: p.append(clamp(50+s.return_on_equity*100))
    return sum(p)/len(p) if p else 50
def risk_score(s):
    p=[]
    if s.beta is not None: p.append(clamp(100-max(0,s.beta-1)*35))
    if s.debt_to_equity is not None: p.append(clamp(100-max(0,s.debt_to_equity-50)*.5))
    if s.current_ratio is not None: p.append(clamp(40+s.current_ratio*30))
    return sum(p)/len(p) if p else 50
def momentum_score(series):
    if len(series)<200: return 50
    now=float(series.iloc[-1]); ma50=float(series.tail(50).mean()); ma200=float(series.tail(200).mean())
    return clamp(50+(now/ma50-1)*150+(now/ma200-1)*150)
def master_score(s,v,momentum=50):
    c={"valuation":valuation_score(v),"growth":growth_score(s),"quality":quality_score(s),"momentum":momentum,"risk":risk_score(s)}
    w={"valuation":.30,"growth":.20,"quality":.20,"momentum":.15,"risk":.15}
    return sum(c[k]*w[k] for k in w),c
def signal(score): return "BUY" if score>=70 else "SELL" if score<=40 else "HOLD"
