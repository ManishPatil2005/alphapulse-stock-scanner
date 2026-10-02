"""
stock_lists.py
Curated and comprehensive stock universe definitions for US and Indian markets.
"""

# US Mega-Cap Titans (Top liquid US market leaders)
MEGA_CAPS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "ORCL",
    "AMD", "NFLX", "QCOM", "COST", "ADBE", "CSCO", "INTC", "TXN", "AMAT",
    "MU", "PANW", "SNPS", "CDNS", "CRWD", "PLTR", "UBER", "ABNB", "NOW",
    "JPM", "V", "MA", "UNH", "XOM", "LLY", "WMT", "HD", "PG", "JNJ", "ABBV"
]

# NASDAQ 100 components
NASDAQ_100 = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "AVGO",
    "COST", "ASML", "PEP", "NFLX", "AMD", "AZN", "LIN", "CSCO", "TMUS", "ADBE",
    "QCOM", "TXN", "AMGN", "INTU", "HON", "AMAT", "ISRG", "CMCSA", "BKNG",
    "VRTX", "PANW", "SBUX", "GILD", "REGN", "MDLZ", "ADP", "LRCX", "ADI",
    "KLAC", "SNPS", "CDNS", "PDD", "MELI", "CRWD", "MAR", "PYPL", "ORLY",
    "CTAS", "NXPI", "CHTR", "PCAR", "MNST", "WDAY", "FTNT", "KDP", "MCHP",
    "PAYX", "ROST", "MRVL", "ADSK", "CPRT", "DXCM", "AEP", "ODFL", "IDXX",
    "EXC", "FAST", "CEG", "LULU", "BKR", "VRSK", "EA", "CSGP", "CTSH",
    "GEHC", "FANG", "XEL", "KHC", "CCEP", "TEAM", "DDOG", "ANSS", "ZS",
    "DLTR", "BIIB", "ILMN", "WBD", "MDB", "ON", "GFS", "ARM", "SMCI", "TTD"
]

# Dow Jones Industrial Average 30
DOW_30 = [
    "AAPL", "AMGN", "AMZN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX", "DIS",
    "GS", "HD", "HON", "IBM", "JNJ", "JPM", "KO", "MCD", "MMM", "MRK",
    "MSFT", "NKE", "NVDA", "PG", "SHW", "TRV", "UNH", "V", "VZ", "WMT"
]

# Top 100 S&P 500 Liquid Leaders
SP500_TOP100 = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "BRK-B", "TSLA", "AVGO",
    "JPM", "LLY", "V", "UNH", "XOM", "MA", "WMT", "COST", "PG", "HD", "JNJ",
    "BAC", "ABBV", "KO", "NFLX", "MRK", "ORCL", "CRM", "CVX", "AMD", "ADBE",
    "ACN", "LIN", "PEP", "TMO", "WFC", "CSCO", "MCD", "ABT", "GE", "QCOM",
    "TXN", "DHR", "INTU", "AMAT", "DIS", "CAT", "VZ", "PFE", "CMCSA", "NOW",
    "IBM", "UBER", "MS", "AXP", "PM", "COP", "ISRG", "RTX", "GS", "LOW",
    "HON", "SPGI", "AMGN", "T", "BKNG", "UNP", "SYK", "PLTR", "LRCX", "BLK",
    "VRTX", "PANW", "TJX", "DE", "REGN", "MDLZ", "PGR", "CI", "ADI", "CB",
    "BSX", "GILD", "MMC", "LMT", "KLAC", "SNPS", "C", "ETN", "FI", "CDNS",
    "AMT", "ADP", "SO", "DUK", "SCHW", "ZTS", "WM", "MO", "ICE", "SHW"
]

# Indian Nifty 50 (National Stock Exchange - NSE)
NIFTY_50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "BHARTIARTL.NS", "SBIN.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS",
    "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "ADANIENT.NS", "TATAMOTORS.NS", "KOTAKBANK.NS", "NTPC.NS", "ONGC.NS",
    "TITAN.NS", "AXISBANK.NS", "ADANIPORTS.NS", "POWERGRID.NS", "WIPRO.NS",
    "COALINDIA.NS", "ULTRACEMCO.NS", "BAJAJFINSV.NS", "M&M.NS", "ASIANPAINT.NS",
    "JSWSTEEL.NS", "TATASTEEL.NS", "SIEMENS.NS", "GRASIM.NS", "NESTLEIND.NS",
    "TECHM.NS", "HINDALCO.NS", "INDUSINDBK.NS", "BEL.NS", "CIPLA.NS",
    "SBILIFE.NS", "DRREDDY.NS", "BRITANNIA.NS", "BPCL.NS", "EICHERMOT.NS",
    "TATACONSUM.NS", "HDFCLIFE.NS", "APOLLOHOSP.NS", "DIVISLAB.NS", "HEROMOTOCO.NS"
]

# Nifty Next 50 (High Momentum Mid/Large Caps)
NIFTY_NEXT_50 = [
    "HAL.NS", "VBL.NS", "CHOLAFIN.NS", "DLF.NS", "PFC.NS",
    "RECLTD.NS", "IOC.NS", "TVSMOTOR.NS", "GAIL.NS", "ABB.NS",
    "BANKBARODA.NS", "ZYDUSLIFE.NS", "VEDL.NS", "TRENT.NS", "PIDILITIND.NS",
    "HAVELLS.NS", "AMBUJACEM.NS", "SRF.NS", "POLYCAB.NS", "LODHA.NS",
    "INDIGO.NS", "ICICIPRULI.NS", "BOSCHLTD.NS", "MOTHERSON.NS", "SHREECEM.NS",
    "CANBK.NS", "IRCTC.NS", "COLPAL.NS", "AUROPHARMA.NS", "LTIM.NS"
]

# Predefined dictionary for easy lookup in scanner
UNIVERSES = {
    "us_mega_caps": {
        "name": "US Mega-Caps (Top 38)",
        "market": "US",
        "symbols": MEGA_CAPS
    },
    "nasdaq_100": {
        "name": "NASDAQ 100 Tech & Growth",
        "market": "US",
        "symbols": NASDAQ_100
    },
    "sp500_top": {
        "name": "S&P 500 Top 100 Leaders",
        "market": "US",
        "symbols": SP500_TOP100
    },
    "dow_30": {
        "name": "Dow Jones 30 Bluechips",
        "market": "US",
        "symbols": DOW_30
    },
    "nifty_50": {
        "name": "India NIFTY 50 (NSE)",
        "market": "NSE",
        "symbols": NIFTY_50
    },
    "nifty_next_50": {
        "name": "India NIFTY Next 50 (NSE)",
        "market": "NSE",
        "symbols": NIFTY_NEXT_50
    },
    "market_indices": {
        "name": "Global & Indian Market Indices",
        "market": "INDEX",
        "symbols": ["^GSPC", "^IXIC", "^DJI", "^NSEI", "^NSEBANK", "^BSESN", "^CNXIT", "^VIX", "BTC-USD", "ETH-USD"]
    }
}
