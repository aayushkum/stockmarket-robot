import pandas as pd
URL="https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
def sp500_tickers():
    symbols=pd.read_html(URL)[0]["Symbol"].astype(str).tolist()
    return [x.replace(".","-") for x in symbols]
