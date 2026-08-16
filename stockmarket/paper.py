from dataclasses import dataclass
@dataclass
class Position:
    shares: float
    avg_cost: float
class PaperPortfolio:
    def __init__(self,settings): self.settings=settings; self.cash=settings.starting_cash; self.positions={}
    def buy(self,ticker,price,amount):
        if amount<=0 or price<=0 or amount>self.cash: return False
        shares=amount/price; old=self.positions.get(ticker)
        if old:
            total=old.shares+shares; old.avg_cost=(old.shares*old.avg_cost+amount)/total; old.shares=total
        else: self.positions[ticker]=Position(shares,price)
        self.cash-=amount; return True
    def sell(self,ticker,price,fraction=1):
        pos=self.positions.get(ticker)
        if not pos or price<=0: return 0
        shares=pos.shares*max(0,min(1,fraction)); proceeds=shares*price; pos.shares-=shares; self.cash+=proceeds
        if pos.shares<1e-10: del self.positions[ticker]
        return proceeds
    def equity(self,prices): return self.cash+sum(p.shares*prices.get(t,p.avg_cost) for t,p in self.positions.items())
