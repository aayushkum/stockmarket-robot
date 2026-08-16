from stockmarket.data import Snapshot
from stockmarket.valuation import summarize

def test_average_of_valid_models():
    s=Snapshot('TEST',100,5,6,1000,100,10,1,20,16,.1,.12,.15,.08,.1,40,1.5,1000,'Test')
    v=summarize(s); vals=[x.fair_value for x in v.estimates if x.fair_value is not None]
    assert len(vals)>=3 and v.fair_value==sum(vals)/len(vals)
