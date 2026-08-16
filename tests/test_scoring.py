from stockmarket.scoring import signal
def test_boundaries():
    assert signal(70)=='BUY'; assert signal(69.9)=='HOLD'; assert signal(40)=='HOLD'; assert signal(39.9)=='SELL'
