"""
heatmap_engine/rotation.py
Institutional Rotation Tracker.
Monitors relative strength of Sectors (Growth vs Value, Defensive vs Cyclical)
to detect capital flows.
"""

from typing import List, Dict, Any
from .sectors import SectorHeatmapEngine

class InstitutionalRotationTracker:
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.engine = SectorHeatmapEngine(symbols)

    def calculate_flows(self) -> Dict[str, Any]:
        """
        Calculates capital flows by analyzing the 1-Day or 5-Day change
        in the Sector Heatmap tree.
        """
        tree = self.engine.generate_heatmap()
        if not tree.get("children"):
            return {"error": "No sector data available"}

        sectors = []
        for sector_node in tree["children"]:
            sectors.append({
                "name": sector_node["name"],
                "change": sector_node["change"]
            })
            
        # Sort by best performing to worst
        sectors.sort(key=lambda x: x["change"], reverse=True)
        
        # Risk-On Sectors usually include Tech, Consumer Cyclical, Communication Services
        # Risk-Off Sectors usually include Utilities, Consumer Defensive, Healthcare
        risk_on = ["Technology", "Consumer Cyclical", "Communication Services", "Crypto"]
        risk_off = ["Utilities", "Consumer Defensive", "Healthcare"]
        
        risk_on_perf = 0.0
        risk_on_count = 0
        risk_off_perf = 0.0
        risk_off_count = 0
        
        for s in sectors:
            if s["name"] in risk_on:
                risk_on_perf += s["change"]
                risk_on_count += 1
            elif s["name"] in risk_off:
                risk_off_perf += s["change"]
                risk_off_count += 1
                
        avg_risk_on = risk_on_perf / risk_on_count if risk_on_count > 0 else 0
        avg_risk_off = risk_off_perf / risk_off_count if risk_off_count > 0 else 0
        
        flow_vector = "Neutral"
        if avg_risk_on > avg_risk_off + 0.5:
            flow_vector = "Risk-On (Capital flowing into Growth/Tech)"
        elif avg_risk_off > avg_risk_on + 0.5:
            flow_vector = "Risk-Off (Capital flowing into Defensive/Value)"

        return {
            "top_sectors": sectors[:3],
            "bottom_sectors": sectors[-3:] if len(sectors) >= 3 else sectors,
            "rotation_vector": flow_vector,
            "metrics": {
                "avg_risk_on_change": round(avg_risk_on, 2),
                "avg_risk_off_change": round(avg_risk_off, 2)
            }
        }
