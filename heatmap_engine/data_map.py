"""
heatmap_engine/data_map.py
Static Sector & Industry mapping for the heatmap engine.
In production, this would be dynamically fetched from Angel One / Yahoo metadata.
"""

SECTOR_MAP = {
    # US Tech / Growth
    "AAPL": {"sector": "Technology", "industry": "Consumer Electronics", "market_cap": 3000},
    "MSFT": {"sector": "Technology", "industry": "Software", "market_cap": 2800},
    "NVDA": {"sector": "Technology", "industry": "Semiconductors", "market_cap": 2200},
    "TSLA": {"sector": "Consumer Cyclical", "industry": "Auto Manufacturers", "market_cap": 600},
    "AMZN": {"sector": "Consumer Cyclical", "industry": "Internet Retail", "market_cap": 1800},
    "META": {"sector": "Communication Services", "industry": "Internet Content", "market_cap": 1200},
    "GOOGL": {"sector": "Communication Services", "industry": "Internet Content", "market_cap": 1700},
    
    # Nifty 50 (Subset)
    "RELIANCE.NS": {"sector": "Energy", "industry": "Oil & Gas", "market_cap": 200},
    "TCS.NS": {"sector": "Technology", "industry": "IT Services", "market_cap": 150},
    "HDFCBANK.NS": {"sector": "Financial Services", "industry": "Banks", "market_cap": 130},
    "INFY.NS": {"sector": "Technology", "industry": "IT Services", "market_cap": 80},
    "ICICIBANK.NS": {"sector": "Financial Services", "industry": "Banks", "market_cap": 90},
    "ITC.NS": {"sector": "Consumer Defensive", "industry": "Tobacco", "market_cap": 60},
    "SBIN.NS": {"sector": "Financial Services", "industry": "Banks", "market_cap": 70},
    "LART.NS": {"sector": "Industrials", "industry": "Engineering & Construction", "market_cap": 50},
    "BAJFINANCE.NS": {"sector": "Financial Services", "industry": "Credit Services", "market_cap": 45},
    "BHARTIARTL.NS": {"sector": "Communication Services", "industry": "Telecom", "market_cap": 65},
    
    # Crypto (Delta Exchange pseudo-sectors)
    "BTCUSDT": {"sector": "Crypto", "industry": "Layer 1", "market_cap": 1400},
    "ETHUSDT": {"sector": "Crypto", "industry": "Layer 1", "market_cap": 400},
    "SOLUSDT": {"sector": "Crypto", "industry": "Layer 1", "market_cap": 60},
}

def get_metadata(symbol: str):
    return SECTOR_MAP.get(symbol, {"sector": "Unknown", "industry": "Unknown", "market_cap": 1})
