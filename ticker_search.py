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
    {"symbol": "TRENT.NS", "name": "Trent Ltd", "exchange": "NSE", "country": "IN", "type": "Stock", "sector": "Consumer Goods & Retail", "industry": "Retail & Fashion"},
    {"symbol": "ZOMATO.NS", "name": "Zomato Ltd", "exchange": "NSE", "country": "IN", "type": "Stock", "sector": "Information Technology", "industry": "Food Delivery & Internet"},
    {"symbol": "JIOFIN.NS", "name": "Jio Financial Services Ltd", "exchange": "NSE", "country": "IN", "type": "Stock", "sector": "Financial Services", "industry": "NBFC & Broking"}
]

# --- Major ISIN to Symbol Mapping ---
ISIN_MAP = {
    "INE002A01018": "RELIANCE.NS",
    "INE040A01034": "HDFCBANK.NS",
    "INE009A01021": "INFY.NS",
    "INE467B01029": "TCS.NS",
    "INE062A01020": "SBIN.NS",
    "INE090A01021": "ICICIBANK.NS",
    "INE154A01015": "ITC.NS",
    "INE018A01030": "LT.NS",
    "INE238A01034": "AXISBANK.NS",
    "INE237A01028": "KOTAKBANK.NS",
    "INE296A01024": "BAJFINANCE.NS",
    "INE397D01024": "BHARTIARTL.NS",
    "INE155A01022": "TATAMOTORS.NS",
    "INE081A01020": "TATASTEEL.NS",
    "INE280A01028": "TITAN.NS",
    "INE021A01026": "ASIANPAINT.NS",
    "INE044A01036": "SUNPHARMA.NS",
    "INE585B01010": "MARUTI.NS",
    "INE848E01016": "TRENT.NS",
    "INE758T01015": "ZOMATO.NS"
}

# --- Add Major F&O Futures and Index Options into Search Index ---
FNO_REGISTRY = [
    # Index Futures
    {"symbol": "NIFTY-FUT", "name": "NIFTY 50 Current Month Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Index Derivatives", "industry": "Futures"},
    {"symbol": "BANKNIFTY-FUT", "name": "NIFTY Bank Current Month Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Index Derivatives", "industry": "Futures"},
    {"symbol": "FINNIFTY-FUT", "name": "NIFTY Financial Services Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Index Derivatives", "industry": "Futures"},
    {"symbol": "MIDCPNIFTY-FUT", "name": "NIFTY Midcap Select Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Index Derivatives", "industry": "Futures"},

    # Stock Futures
    {"symbol": "RELIANCE-FUT", "name": "Reliance Industries Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Stock Derivatives", "industry": "Futures"},
    {"symbol": "HDFCBANK-FUT", "name": "HDFC Bank Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Stock Derivatives", "industry": "Futures"},
    {"symbol": "ICICIBANK-FUT", "name": "ICICI Bank Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Stock Derivatives", "industry": "Futures"},
    {"symbol": "INFY-FUT", "name": "Infosys Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Stock Derivatives", "industry": "Futures"},
    {"symbol": "TCS-FUT", "name": "Tata Consultancy Services Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Stock Derivatives", "industry": "Futures"},
    {"symbol": "SBIN-FUT", "name": "State Bank of India Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Stock Derivatives", "industry": "Futures"},
    {"symbol": "TATAMOTORS-FUT", "name": "Tata Motors Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Stock Derivatives", "industry": "Futures"},
    {"symbol": "BHARTIARTL-FUT", "name": "Bharti Airtel Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Stock Derivatives", "industry": "Futures"},
    {"symbol": "LT-FUT", "name": "Larsen & Toubro Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Stock Derivatives", "industry": "Futures"},
    {"symbol": "BAJFINANCE-FUT", "name": "Bajaj Finance Future", "exchange": "NFO", "country": "IN", "type": "Future", "sector": "Stock Derivatives", "industry": "Futures"},

    # Major Liquid Index Options
    {"symbol": "NIFTY 22600 CE", "name": "NIFTY 22600 Call Option", "exchange": "NFO", "country": "IN", "type": "Option", "sector": "Options", "industry": "Call Option"},
    {"symbol": "NIFTY 22600 PE", "name": "NIFTY 22600 Put Option", "exchange": "NFO", "country": "IN", "type": "Option", "sector": "Options", "industry": "Put Option"},
    {"symbol": "NIFTY 22500 CE", "name": "NIFTY 22500 Call Option", "exchange": "NFO", "country": "IN", "type": "Option", "sector": "Options", "industry": "Call Option"},
    {"symbol": "NIFTY 22500 PE", "name": "NIFTY 22500 Put Option", "exchange": "NFO", "country": "IN", "type": "Option", "sector": "Options", "industry": "Put Option"},
    {"symbol": "NIFTY 22700 CE", "name": "NIFTY 22700 Call Option", "exchange": "NFO", "country": "IN", "type": "Option", "sector": "Options", "industry": "Call Option"},
    {"symbol": "NIFTY 22700 PE", "name": "NIFTY 22700 Put Option", "exchange": "NFO", "country": "IN", "type": "Option", "sector": "Options", "industry": "Put Option"},
    {"symbol": "BANKNIFTY 48000 CE", "name": "BANKNIFTY 48000 Call Option", "exchange": "NFO", "country": "IN", "type": "Option", "sector": "Options", "industry": "Call Option"},
    {"symbol": "BANKNIFTY 48000 PE", "name": "BANKNIFTY 48000 Put Option", "exchange": "NFO", "country": "IN", "type": "Option", "sector": "Options", "industry": "Put Option"},

    # Major BSE Equities
    {"symbol": "500325.BO", "name": "Reliance Industries Ltd (BSE)", "exchange": "BSE", "country": "IN", "type": "Stock", "sector": "Energy, Oil & Power", "industry": "Oil & Gas"},
    {"symbol": "500180.BO", "name": "HDFC Bank Ltd (BSE)", "exchange": "BSE", "country": "IN", "type": "Stock", "sector": "Financial Services", "industry": "Private Bank"},
    {"symbol": "532540.BO", "name": "Tata Consultancy Services Ltd (BSE)", "exchange": "BSE", "country": "IN", "type": "Stock", "sector": "Information Technology", "industry": "IT Services"},
    {"symbol": "500209.BO", "name": "Infosys Ltd (BSE)", "exchange": "BSE", "country": "IN", "type": "Stock", "sector": "Information Technology", "industry": "IT Services"},
    {"symbol": "500112.BO", "name": "State Bank of India (BSE)", "exchange": "BSE", "country": "IN", "type": "Stock", "sector": "Financial Services", "industry": "Public Bank"},

    # Commodities (MCX)
    {"symbol": "MCX:GOLD", "name": "Gold 1KG Commodity Future", "exchange": "MCX", "country": "IN", "type": "Commodity", "sector": "Commodities", "industry": "Precious Metals"},
    {"symbol": "MCX:SILVER", "name": "Silver 30KG Commodity Future", "exchange": "MCX", "country": "IN", "type": "Commodity", "sector": "Commodities", "industry": "Precious Metals"},
    {"symbol": "MCX:CRUDEOIL", "name": "Crude Oil 100 BBL Future", "exchange": "MCX", "country": "IN", "type": "Commodity", "sector": "Commodities", "industry": "Energy"},
    {"symbol": "MCX:NATURALGAS", "name": "Natural Gas 1250 MMBTU Future", "exchange": "MCX", "country": "IN", "type": "Commodity", "sector": "Commodities", "industry": "Energy"},
    {"symbol": "MCX:COPPER", "name": "Copper 2500KG Future", "exchange": "MCX", "country": "IN", "type": "Commodity", "sector": "Commodities", "industry": "Industrial Metals"},

    # Currencies & Forex
    {"symbol": "USDINR", "name": "USD / INR Currency Pair", "exchange": "FOREX", "country": "IN", "type": "Currency", "sector": "Currencies", "industry": "Forex"},
    {"symbol": "EURUSD", "name": "EUR / USD Currency Pair", "exchange": "FOREX", "country": "GLOBAL", "type": "Currency", "sector": "Currencies", "industry": "Forex"},
    {"symbol": "GBPUSD", "name": "GBP / USD Currency Pair", "exchange": "FOREX", "country": "GLOBAL", "type": "Currency", "sector": "Currencies", "industry": "Forex"},
    {"symbol": "USDJPY", "name": "USD / JPY Currency Pair", "exchange": "FOREX", "country": "GLOBAL", "type": "Currency", "sector": "Currencies", "industry": "Forex"},

    # ETFs
    {"symbol": "NIFTYBEES.NS", "name": "Nippon India ETF Nifty 50 BeES", "exchange": "NSE", "country": "IN", "type": "ETF", "sector": "Index ETF", "industry": "ETFs"},
    {"symbol": "BANKBEES.NS", "name": "Nippon India ETF Nifty Bank BeES", "exchange": "NSE", "country": "IN", "type": "ETF", "sector": "Sectoral ETF", "industry": "ETFs"},
    {"symbol": "GOLDBEES.NS", "name": "Nippon India ETF Gold BeES", "exchange": "NSE", "country": "IN", "type": "ETF", "sector": "Commodity ETF", "industry": "ETFs"},
    {"symbol": "ITBEES.NS", "name": "Nippon India ETF Nifty IT BeES", "exchange": "NSE", "country": "IN", "type": "ETF", "sector": "Sectoral ETF", "industry": "ETFs"},
]
TICKER_REGISTRY.extend(FNO_REGISTRY)

# Comprehensive Alias Mapping for Natural Language Search
ALIAS_MAP = {
    "SBI": "SBIN.NS",
    "STATE BANK": "SBIN.NS",
    "STATE BANK OF INDIA": "SBIN.NS",
    "RELIANCE": "RELIANCE.NS",
    "RIL": "RELIANCE.NS",
    "HDFC": "HDFCBANK.NS",
    "HDFC BANK": "HDFCBANK.NS",
    "ICICI": "ICICIBANK.NS",
    "ICICI BANK": "ICICIBANK.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "INFOSYS": "INFY.NS",
    "AIRTEL": "BHARTIARTL.NS",
    "BHARTI": "BHARTIARTL.NS",
    "TATA MOTORS": "TATAMOTORS.NS",
    "L&T": "LT.NS",
    "LARSEN": "LT.NS",
    "NIFTY": "^NSEI",
    "NIFTY 50": "^NSEI",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "BANK NIFTY": "^NSEBANK",
    "FINNIFTY": "^NSEI",
    "MIDCAP NIFTY": "^NSEI",
    "SENSEX": "^BSESN",
    "BSE SENSEX": "^BSESN",
    "GOLD": "MCX:GOLD",
    "SILVER": "MCX:SILVER",
    "CRUDE": "MCX:CRUDEOIL",
    "CRUDE OIL": "MCX:CRUDEOIL",
    "NATURAL GAS": "MCX:NATURALGAS",
    "NATGAS": "MCX:NATURALGAS",
}

# Enrich with full 5,150+ Cash Segment Equities from cash_stocks_db.json
try:
    import json
    import os
    db_file = os.path.join(os.path.dirname(__file__), "cash_stocks_db.json")
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            cash_db = json.load(f)
            _existing_map = {x["symbol"]: x for x in TICKER_REGISTRY}
            for stock in cash_db:
                sym = stock.get("symbol")
                if not sym:
                    continue
                if sym in _existing_map:
                    if not _existing_map[sym].get("sector"):
                        _existing_map[sym]["sector"] = stock.get("sector", "Other")
                    if not _existing_map[sym].get("industry"):
                        _existing_map[sym]["industry"] = stock.get("industry", "Equities")
                else:
                    item = {
                        "symbol": sym,
                        "name": stock.get("name", sym),
                        "exchange": stock.get("market", "NSE"),
                        "country": stock.get("country", "IN"),
                        "type": "Stock",
                        "sector": stock.get("sector", "Other"),
                        "industry": stock.get("industry", "Equities")
                    }
                    _existing_map[sym] = item
                    TICKER_REGISTRY.append(item)
except Exception as e:
    pass


def search_tickers(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    """
    High-speed substring, prefix, ISIN, sector, and industry search over 5,000+ equities & F&O contracts.
    Returns matched items ranked by relevance.
    """
    q = query.strip().upper()
    if not q:
        return TICKER_REGISTRY[:limit]

    # Check ISIN first
    if q in ISIN_MAP:
        mapped_sym = ISIN_MAP[q]
        for item in TICKER_REGISTRY:
            if item["symbol"] == mapped_sym:
                return [item]

    exact_matches = []

    # Check Alias Map (e.g. SBI -> SBIN.NS, RELIANCE -> RELIANCE.NS, GOLD -> MCX:GOLD)
    if q in ALIAS_MAP:
        alias_target = ALIAS_MAP[q]
        for it in TICKER_REGISTRY:
            if it["symbol"] == alias_target:
                exact_matches.append(it)
                break
    prefix_matches = []
    contain_matches = []
    fno_matches = []
    sector_matches = []

    q_clean = q.replace(".NS", "").replace(".BO", "")
    q_lower = query.strip().lower()

    for item in TICKER_REGISTRY:
        sym = item["symbol"].upper()
        name = item.get("name", "").upper()
        sec = item.get("sector", "").lower()
        ind = item.get("industry", "").lower()
        itype = item.get("type", "Stock")
        sym_clean = sym.replace(".NS", "").replace(".BO", "")

        # 1. Exact symbol or clean symbol match
        if sym == q or sym_clean == q_clean or (f"{q_clean}.NS" == sym):
            exact_matches.append(item)
        # 2. Prefix symbol match
        elif sym.startswith(q) or sym_clean.startswith(q_clean):
            prefix_matches.append(item)
        # 3. F&O contract match
        elif itype in ("Future", "Option") and (q_clean in sym or q_clean in name):
            fno_matches.append(item)
        # 4. Name or symbol contains query
        elif q in sym or q_clean in sym_clean or q_lower in name.lower():
            contain_matches.append(item)
        # 5. Sector or Industry match
        elif q_lower in sec or q_lower in ind:
            sector_matches.append(item)

    # Deduplicate while preserving rank order
    seen = set()
    ordered_results = []
    for it in exact_matches + prefix_matches + fno_matches + contain_matches + sector_matches:
        if it["symbol"] not in seen:
            seen.add(it["symbol"])
            ordered_results.append(it)

    # If no results found in local registry, allow user-typed symbol dynamically
    if not ordered_results:
        guess_symbol = q if ("." in q or "^" in q or "-" in q) else q
        ordered_results.append({
            "symbol": guess_symbol,
            "name": f"Search '{guess_symbol}' directly",
            "exchange": "CUSTOM",
            "country": "US/GLOBAL",
            "type": "Stock",
            "sector": "Custom",
            "industry": "Custom"
        })
        if not guess_symbol.endswith(".NS") and not guess_symbol.startswith("^"):
            ordered_results.append({
                "symbol": f"{guess_symbol}.NS",
                "name": f"Search NSE '{guess_symbol}.NS'",
                "exchange": "NSE",
                "country": "IN",
                "type": "Stock",
                "sector": "NSE Cash",
                "industry": "Equities"
            })
            ordered_results.append({
                "symbol": f"{guess_symbol}.BO",
                "name": f"Search BSE '{guess_symbol}.BO'",
                "exchange": "BSE",
                "country": "IN",
                "type": "Stock",
                "sector": "BSE Cash",
                "industry": "Equities"
            })

    return ordered_results[:limit]

