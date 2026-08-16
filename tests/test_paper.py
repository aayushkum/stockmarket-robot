from stockmarket.config import Settings
from stockmarket.paper import PaperPortfolio
def test_buy_sell():
    p=PaperPortfolio(Settings()); assert p.buy('ABC',100,1000); assert p.cash==99000; assert p.positions['ABC'].shares==10
    assert p.sell('ABC',110)==1100; assert p.cash==100100
