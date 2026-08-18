"""S&P 500 universe definition and utilities."""
from typing import List
import pandas as pd


# URL for S&P 500 constituent list
S_AND_P_500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def sp500_tickers() -> List[str]:
    """Fetch current S&P 500 constituent ticker symbols.
    
    Retrieves the list from Wikipedia and converts dot-notation tickers
    (like BRK.A) to dash-notation (like BRK-A) for yfinance compatibility.
    
    Returns:
        List of S&P 500 ticker symbols.
        
    Raises:
        Exception: If unable to fetch or parse Wikipedia data.
    """
    # Parse S&P 500 table from Wikipedia
    tables = pd.read_html(S_AND_P_500_URL)
    symbols = tables[0]["Symbol"].astype(str).tolist()
    
    # Convert dot notation to dash notation for yfinance
    return [ticker.replace(".", "-") for ticker in symbols]
