"""
scanner/historical_export.py
Historical Scanner Validation Engine.
Runs visual scanner conditions against 1, 3, 5, 10 years of historical data.
Exports results to CSV, Parquet, and JSON formats to validate strategies over time.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from data_feed import get_stock_data
from technicals import analyze_market_structure
from scanner_engine.ast_engine import build_ast_from_dict, ASTNode


class HistoricalScannerEngine:
    """Validates dynamic strategies over multi-year datasets and exports results."""

    def __init__(self, export_dir: str = "exports"):
        self.export_dir = export_dir
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

    def run_historical_scan(
        self,
        symbols: List[str],
        ast_json: Dict[str, Any],
        years: int = 1,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        Runs the AST logic against historical bars for all provided symbols.
        Returns a DataFrame of all historical occurrences (signal fires).
        """
        ast_root = build_ast_from_dict(ast_json)
        all_signals = []

        # Convert years to data range string (e.g., '1y', '5y')
        data_range = f"{years}y"
        if years > 10:
            data_range = "max"

        for symbol in symbols:
            # 1. Fetch deep historical data
            df, meta = get_stock_data(symbol, interval=timeframe, data_range=data_range)
            if df is None or len(df) < 50:
                continue

            # 2. Enrich with technicals (we need the boolean indicators computed)
            # analyze_market_structure modifies df in place and returns latest dict.
            # We want the DataFrame with 'ema_10', 'rsi_21', 'volume_avg_20' etc. appended for all rows.
            _ = analyze_market_structure(df) 
            
            # Additional rolling columns for AST
            if "volume" in df.columns:
                df["volume_avg_20"] = df["volume"].rolling(window=20).mean()
            
            # Compute mock boolean flags over series for the AST
            # Example: ema compression flag over time
            if all(col in df.columns for col in ["ema_10", "ema_20", "ema_50"]):
                spread = (df[["ema_10", "ema_20", "ema_50"]].max(axis=1) - df[["ema_10", "ema_20", "ema_50"]].min(axis=1)) / df["close"] * 100
                df["has_ema_compression"] = np.where(spread <= 3.5, 1.0, 0.0)
            else:
                df["has_ema_compression"] = 0.0
                
            df["is_ep"] = 0.0 # Simplify for this batch historical pass

            # 3. Evaluate AST logic across the timeline
            for i in range(20, len(df)):
                if ast_root.evaluate(df, i):
                    row = df.iloc[i]
                    ts = row["time"]
                    date_str = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
                    all_signals.append({
                        "Date": date_str,
                        "Symbol": symbol,
                        "Close": round(row["close"], 2),
                        "Volume": int(row["volume"]),
                        "RSI_21": round(row.get("rsi_21", 0.0), 2)
                    })

        # Return as DataFrame for easy export
        result_df = pd.DataFrame(all_signals)
        if not result_df.empty:
            # Sort by Date descending
            result_df = result_df.sort_values("Date", ascending=False).reset_index(drop=True)
            
        return result_df

    def export_results(self, df: pd.DataFrame, strategy_name: str, format_type: str = "parquet") -> str:
        """Exports the signal DataFrame to Parquet, CSV, or JSON."""
        if df.empty:
            return "No signals found to export."
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = strategy_name.replace(" ", "_").lower()
        base_filename = f"{self.export_dir}/{safe_name}_{timestamp}"

        if format_type.lower() == "parquet":
            filepath = f"{base_filename}.parquet"
            df.to_parquet(filepath, engine="fastparquet")
            return filepath
        elif format_type.lower() == "csv":
            filepath = f"{base_filename}.csv"
            df.to_csv(filepath, index=False)
            return filepath
        elif format_type.lower() == "json":
            filepath = f"{base_filename}.json"
            df.to_json(filepath, orient="records", indent=2)
            return filepath
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
