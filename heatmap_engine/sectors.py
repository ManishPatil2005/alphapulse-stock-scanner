"""
heatmap_engine/sectors.py
Calculates hierarchical sector and industry performance for visual Treemaps.
"""

import pandas as pd
from typing import List, Dict, Any
from .data_map import get_metadata
from data_feed import get_stock_data

class SectorHeatmapEngine:
    def __init__(self, symbols: List[str]):
        self.symbols = symbols

    def generate_heatmap(self) -> Dict[str, Any]:
        """
        Fetches the latest daily return for the given symbols and aggregates
        them into a hierarchical JSON structure for frontend Treemaps (e.g., D3.js, Highcharts).
        """
        records = []
        for sym in self.symbols:
            # Fetch minimal data for performance
            df, _ = get_stock_data(sym, interval="1d", data_range="5d")
            if df is None or len(df) < 2:
                continue
                
            last_close = df['close'].iloc[-1]
            prev_close = df['close'].iloc[-2]
            pct_change = ((last_close - prev_close) / prev_close) * 100
            
            meta = get_metadata(sym)
            records.append({
                "symbol": sym,
                "sector": meta["sector"],
                "industry": meta["industry"],
                "market_cap": meta["market_cap"],
                "change": round(pct_change, 2),
                "price": round(last_close, 2)
            })

        if not records:
            return {"name": "Market", "children": []}

        # Build Hierarchy: Market -> Sector -> Industry -> Ticker
        df_records = pd.DataFrame(records)
        
        market_tree = {"name": "Market", "children": []}
        
        sectors = df_records['sector'].unique()
        for sector in sectors:
            sector_df = df_records[df_records['sector'] == sector]
            sector_node = {"name": sector, "children": [], "change": 0.0, "market_cap": 0}
            
            industries = sector_df['industry'].unique()
            for industry in industries:
                ind_df = sector_df[sector_df['industry'] == industry]
                ind_node = {"name": industry, "children": [], "change": 0.0, "market_cap": 0}
                
                for _, row in ind_df.iterrows():
                    ticker_node = {
                        "name": row['symbol'],
                        "value": row['market_cap'],  # Size of the box
                        "change": row['change'],     # Color of the box (Red/Green)
                        "price": row['price']
                    }
                    ind_node['children'].append(ticker_node)
                    ind_node['market_cap'] += row['market_cap']
                
                # Industry change is market-cap weighted
                if ind_node['market_cap'] > 0:
                    weighted_change = sum(c['change'] * c['value'] for c in ind_node['children']) / ind_node['market_cap']
                    ind_node['change'] = round(weighted_change, 2)
                
                sector_node['children'].append(ind_node)
                sector_node['market_cap'] += ind_node['market_cap']
                
            # Sector change is market-cap weighted
            if sector_node['market_cap'] > 0:
                weighted_change = sum(c['change'] * c['market_cap'] for c in sector_node['children']) / sector_node['market_cap']
                sector_node['change'] = round(weighted_change, 2)
                
            market_tree['children'].append(sector_node)
            
        return market_tree
