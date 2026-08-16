from dataclasses import dataclass, asdict
import math
from .data import Snapshot

@dataclass
class ValuationResult:
    model: str; fair_value: float|None; note: str
    def to_dict(self): return asdict(self)
@dataclass
class ValuationSummary:
    estimates: list[ValuationResult]; fair_value: float|None; upside: float|None
    def to_dict(self): return {"estimates":[x.to_dict() for x in self.estimates],"fair_value":self.fair_value,"upside":self.upside}

def earnings_multiple(s):
    if not s.forward_eps or s.forward_eps<=0: return ValuationResult("earnings_multiple",None,"Forward EPS unavailable/non-positive")
    g=s.earnings_growth or .05; pe=min(25,max(10,15+g*100*.35))
    return ValuationResult("earnings_multiple",s.forward_eps*pe,f"Forward EPS x normalized P/E {pe:.1f}")
def revenue_multiple(s):
    if not s.revenue or not s.shares or s.revenue<=0 or s.shares<=0: return ValuationResult("revenue_multiple",None,"Revenue/shares unavailable")
    g=s.revenue_growth or .05; ps=min(8,max(.8,2+g*100*.06))
    return ValuationResult("revenue_multiple",s.revenue/s.shares*ps,f"Revenue/share x P/S {ps:.2f}")
def fcf_multiple(s):
    if not s.free_cash_flow or not s.shares or s.free_cash_flow<=0 or s.shares<=0: return ValuationResult("fcf_multiple",None,"FCF/shares unavailable")
    g=s.earnings_growth or s.revenue_growth or .05; m=min(30,max(10,18+g*100*.4))
    return ValuationResult("fcf_multiple",s.free_cash_flow/s.shares*m,f"FCF/share x multiple {m:.1f}")
def historical_pe(s):
    if not s.eps or s.eps<=0: return ValuationResult("historical_pe",None,"EPS unavailable/non-positive")
    return ValuationResult("historical_pe",s.eps*18,"Normalized long-run P/E proxy of 18")
def dcf_proxy(s):
    if not s.free_cash_flow or not s.shares or s.free_cash_flow<=0 or s.shares<=0: return ValuationResult("dcf",None,"FCF/shares unavailable")
    f=s.free_cash_flow/s.shares; g=min(.10,max(.02,s.revenue_growth or s.earnings_growth or .05)); r=.09+max(0,(s.beta or 1)-1)*.02; tg=min(.035,g); value=0
    for year in range(1,6):
        f*=1+g; value+=f/(1+r)**year
    value += f*(1+tg)/max(.02,r-tg)/(1+r)**5
    return ValuationResult("dcf",value,f"5-year DCF proxy; growth {g:.1%}, discount {r:.1%}")
def summarize(s):
    estimates=[f(s) for f in (dcf_proxy,earnings_multiple,fcf_multiple,revenue_multiple,historical_pe)]
    valid=[x.fair_value for x in estimates if x.fair_value is not None and math.isfinite(x.fair_value) and x.fair_value>0]
    fair=sum(valid)/len(valid) if valid else None
    return ValuationSummary(estimates,fair,(fair/s.price-1) if fair else None)
