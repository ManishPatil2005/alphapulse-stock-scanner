"""
scanner/nlp_parser.py
Autonomous Strategy Generator - Natural Language to AST.
Converts plain English trading rules into executable JSON AST graphs.
"""

import re
from typing import Dict, Any

class NLPParser:
    """
    Parses user natural language into Scanner AST structure.
    In a full production environment, this calls an LLM (like Gemini 1.5 Pro)
    to output structured JSON. Here we implement a regex heuristic engine for
    immediate local operation.
    """
    
    @staticmethod
    def parse_query(query: str) -> Dict[str, Any]:
        """
        Translates text like:
        "stocks breaking 20 day consolidation with volume expansion and RSI above 60"
        into an AST dict.
        """
        query = query.lower()
        conditions = []
        
        # Rule 1: RSI conditions
        rsi_match = re.search(r'rsi\s*(?:is|above|greater than|>)\s*(\d+)', query)
        if rsi_match:
            conditions.append({
                "left": "rsi_21",
                "op": ">",
                "right": float(rsi_match.group(1)),
                "is_right_column": False
            })
            
        rsi_below = re.search(r'rsi\s*(?:is below|less than|<)\s*(\d+)', query)
        if rsi_below:
            conditions.append({
                "left": "rsi_21",
                "op": "<",
                "right": float(rsi_below.group(1)),
                "is_right_column": False
            })

        # Rule 2: Volume expansion
        if "volume expansion" in query or "volume surge" in query:
            conditions.append({
                "left": "volume",
                "op": ">",
                "right": "volume_avg_20",
                "is_right_column": True
            })
            
        # Rule 3: Moving Average crossovers
        cross_above = re.search(r'(?:price|close)\s*cross(?:es|ing)?\s*above\s*(?:the\s*)?(ema|sma|ma)\s*(\d+)', query)
        if cross_above:
            period = cross_above.group(2)
            conditions.append({
                "left": "close",
                "op": "CROSSES_ABOVE",
                "right": f"ema_{period}",
                "is_right_column": True
            })

        # Rule 4: EMA Compression / Consolidation
        if "consolidation" in query or "squeeze" in query:
            # We use our custom boolean flag for ema compression as a proxy
            conditions.append({
                "left": "has_ema_compression",
                "op": "==",
                "right": 1.0,
                "is_right_column": False
            })
            
        # Rule 5: Episodic Pivot
        if "episodic pivot" in query or "earnings gap" in query:
            conditions.append({
                "left": "is_ep",
                "op": "==",
                "right": 1.0,
                "is_right_column": False
            })

        # Default fallback if empty
        if not conditions:
            # Base condition: Price above EMA 20
            conditions.append({
                "left": "close",
                "op": ">",
                "right": "ema_20",
                "is_right_column": True
            })

        if len(conditions) == 1:
            return conditions[0]
            
        return {
            "operator": "AND",
            "children": conditions
        }
