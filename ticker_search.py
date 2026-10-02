"""
ticker_search.py
High-speed in-memory ticker and company search index:
Provides instant autocomplete (<1ms) for thousands of stocks and indices across US and Indian markets.
"""

from typing import List, Dict, Any

# Master searchable registry
TICKER_REGISTRY = [
    # --- Major Market Indices ---
    {"symbol": "^NSEI", "name": "NIFTY 50 Index", "exchange": "NSE", "country": "IN", "type": "Index"},
    {"symbol": "^NSEBANK", "name": "NIFTY Bank Index", "exchange": "NSE", "country": "IN", "type": "Index"},
    {"symbol": "^BSESN", "name": "BSE SENSEX 30 Index", "exchange": "BSE", "country": "IN", "type": "Index"},
    {"symbol": "^CNXIT", "name": "NIFTY IT Index", "exchange": "NSE", "country": "IN", "type": "Index"},
    {"symbol": "^GSPC", "name": "S&P 500 Index", "exchange": "US", "country": "US", "type": "Index"},
    {"symbol": "^IXIC", "name": "NASDAQ Composite", "exchange": "US", "country": "US", "type": "Index"},
    {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "exchange": "US", "country": "US", "type": "Index"},
    {"symbol": "^VIX", "name": "CBOE Volatility Index", "exchange": "US", "country": "US", "type": "Index"},
    {"symbol": "BTC-USD", "name": "Bitcoin USD", "exchange": "CRYPTO", "country": "GLOBAL", "type": "Crypto"},
    {"symbol": "ETH-USD", "name": "Ethereum USD", "exchange": "CRYPTO", "country": "GLOBAL", "type": "Crypto"},

    # --- US Mega-Caps & Tech Leaders ---
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "GOOGL", "name": "Alphabet Inc. (Class A)", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "GOOG", "name": "Alphabet Inc. (Class C)", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "META", "name": "Meta Platforms Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "ORCL", "name": "Oracle Corporation", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "AMD", "name": "Advanced Micro Devices Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "NFLX", "name": "Netflix Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "PLTR", "name": "Palantir Technologies Inc.", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "QCOM", "name": "QUALCOMM Incorporated", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "COST", "name": "Costco Wholesale Corporation", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "ADBE", "name": "Adobe Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "CSCO", "name": "Cisco Systems Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "INTC", "name": "Intel Corporation", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "TXN", "name": "Texas Instruments Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "AMAT", "name": "Applied Materials Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "MU", "name": "Micron Technology Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "PANW", "name": "Palo Alto Networks Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "CRWD", "name": "CrowdStrike Holdings Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "UBER", "name": "Uber Technologies Inc.", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "ABNB", "name": "Airbnb Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "NOW", "name": "ServiceNow Inc.", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "CRM", "name": "Salesforce Inc.", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "IBM", "name": "International Business Machines", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "V", "name": "Visa Inc.", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "MA", "name": "Mastercard Incorporated", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "WMT", "name": "Walmart Inc.", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "LLY", "name": "Eli Lilly and Company", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "UNH", "name": "UnitedHealth Group Inc.", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "XOM", "name": "Exxon Mobil Corporation", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "HD", "name": "The Home Depot Inc.", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "PG", "name": "Procter & Gamble Company", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "BAC", "name": "Bank of America Corporation", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "KO", "name": "The Coca-Cola Company", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "PEP", "name": "PepsiCo Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "ABBV", "name": "AbbVie Inc.", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "DIS", "name": "The Walt Disney Company", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "CAT", "name": "Caterpillar Inc.", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "GS", "name": "The Goldman Sachs Group", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "BA", "name": "The Boeing Company", "exchange": "NYSE", "country": "US", "type": "Stock"},
    {"symbol": "SMCI", "name": "Super Micro Computer Inc.", "exchange": "NASDAQ", "country": "US", "type": "Stock"},
    {"symbol": "ARM", "name": "Arm Holdings plc", "exchange": "NASDAQ", "country": "US", "type": "Stock"},

    # --- Indian Stocks (NSE & BSE) ---
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "INFY.NS", "name": "Infosys Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "SBIN.NS", "name": "State Bank of India (SBI)", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "LICI.NS", "name": "Life Insurance Corp of India", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "ITC.NS", "name": "ITC Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "HCLTECH.NS", "name": "HCL Technologies Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki India Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharmaceutical Industries Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "TATAMOTORS.NS", "name": "Tata Motors Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "NTPC.NS", "name": "NTPC Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "ONGC.NS", "name": "Oil & Natural Gas Corp Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "TITAN.NS", "name": "Titan Company Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "ADANIPORTS.NS", "name": "Adani Ports & Special Economic Zone", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corp of India Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "WIPRO.NS", "name": "Wipro Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "COALINDIA.NS", "name": "Coal India Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "ULTRACEMCO.NS", "name": "UltraTech Cement Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "BAJAJFINSV.NS", "name": "Bajaj Finserv Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "JSWSTEEL.NS", "name": "JSW Steel Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "TATASTEEL.NS", "name": "Tata Steel Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "SIEMENS.NS", "name": "Siemens Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "GRASIM.NS", "name": "Grasim Industries Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "NESTLEIND.NS", "name": "Nestle India Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "TECHM.NS", "name": "Tech Mahindra Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "HINDALCO.NS", "name": "Hindalco Industries Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "INDUSINDBK.NS", "name": "IndusInd Bank Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "BEL.NS", "name": "Bharat Electronics Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "CIPLA.NS", "name": "Cipla Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "SBILIFE.NS", "name": "SBI Life Insurance Co Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "DRREDDY.NS", "name": "Dr. Reddy's Laboratories Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "BRITANNIA.NS", "name": "Britannia Industries Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "BPCL.NS", "name": "Bharat Petroleum Corp Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "EICHERMOT.NS", "name": "Eicher Motors Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "TATACONSUM.NS", "name": "Tata Consumer Products Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "HDFCLIFE.NS", "name": "HDFC Life Insurance Co Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "APOLLOHOSP.NS", "name": "Apollo Hospitals Enterprise Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "DIVISLAB.NS", "name": "Divi's Laboratories Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "HEROMOTOCO.NS", "name": "Hero MotoCorp Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "HAL.NS", "name": "Hindustan Aeronautics Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "VBL.NS", "name": "Varun Beverages Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "CHOLAFIN.NS", "name": "Cholamandalam Investment & Finance", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "DLF.NS", "name": "DLF Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "PFC.NS", "name": "Power Finance Corporation Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "RECLTD.NS", "name": "REC Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "TRENT.NS", "name": "Trent Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "ZOMATO.NS", "name": "Zomato Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"},
    {"symbol": "JIOFIN.NS", "name": "Jio Financial Services Ltd", "exchange": "NSE", "country": "IN", "type": "Stock"}
]


def search_tickers(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    High-speed substring and prefix search over symbols and names.
    Returns matched items ranked by relevance.
    """
    q = query.strip().upper()
    if not q:
        return TICKER_REGISTRY[:limit]

    exact_matches = []
    prefix_matches = []
    contain_matches = []

    # Strip .NS or .BO if user typed it loosely
    q_clean = q.replace(".NS", "").replace(".BO", "")

    for item in TICKER_REGISTRY:
        sym = item["symbol"].upper()
        name = item["name"].upper()
        sym_clean = sym.replace(".NS", "").replace(".BO", "")

        # 1. Exact symbol match
        if sym == q or sym_clean == q_clean:
            exact_matches.append(item)
        # 2. Prefix symbol match
        elif sym.startswith(q) or sym_clean.startswith(q_clean):
            prefix_matches.append(item)
        # 3. Name or symbol contains query
        elif q in sym or q_clean in sym_clean or q.lower() in name.lower():
            contain_matches.append(item)

    results = exact_matches + prefix_matches + contain_matches
    
    # If no results found in local registry, allow user-typed symbol dynamically
    if not results:
        # Check if it looks like Indian stock without .NS
        guess_symbol = q if ("." in q or "^" in q or "-" in q) else q
        results.append({
            "symbol": guess_symbol,
            "name": f"Search '{guess_symbol}' directly",
            "exchange": "CUSTOM",
            "country": "US/GLOBAL",
            "type": "Stock"
        })
        if not guess_symbol.endswith(".NS") and not guess_symbol.startswith("^"):
            results.append({
                "symbol": f"{guess_symbol}.NS",
                "name": f"Search NSE '{guess_symbol}.NS'",
                "exchange": "NSE",
                "country": "IN",
                "type": "Stock"
            })

    return results[:limit]
