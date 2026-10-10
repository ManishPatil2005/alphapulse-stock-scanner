"""
learning_engine/education.py
Provides structured Auction Market Theory and Market Profile education modules.
"""

from typing import List, Dict, Any

AUCTION_THEORY_MODULES = [
    {
        "id": "mod_1",
        "title": "Introduction to Auction Market Theory",
        "level": "Beginner",
        "tags": ["AMT", "Basics"],
        "content": (
            "The market is simply a dual-sided auction process. Its primary purpose is to facilitate trade "
            "between buyers and sellers. When prices are too high, buyers step back, and prices fall. "
            "When prices are too low, buyers step in, and prices rise. The area where the most volume is "
            "transacted is considered 'Fair Value'."
        )
    },
    {
        "id": "mod_2",
        "title": "The Initial Balance (IB)",
        "level": "Intermediate",
        "tags": ["Market Profile", "IB"],
        "content": (
            "The Initial Balance represents the price range established during the first hour of trading. "
            "It shows the initial attempt by the market to find fair value. Breakouts from the IB often "
            "dictate the trend for the remainder of the day. A narrow IB suggests trend potential, while "
            "a wide IB suggests a range-bound day."
        )
    },
    {
        "id": "mod_3",
        "title": "Point of Control (POC) and Value Area",
        "level": "Intermediate",
        "tags": ["Market Profile", "POC", "VAH", "VAL"],
        "content": (
            "The Point of Control (POC) is the price level where the most volume (or time) was transacted. "
            "The Value Area represents the range where 70% of the volume occurred, bordered by the Value Area "
            "High (VAH) and Value Area Low (VAL). Price trading outside the Value Area is considered 'imbalanced' "
            "and represents a trading opportunity as the market seeks a new equilibrium."
        )
    },
    {
        "id": "mod_4",
        "title": "Profile Shapes (P, b, D)",
        "level": "Advanced",
        "tags": ["Market Profile", "Shapes", "Context"],
        "content": (
            "Profile shapes give us immediate context about institutional participation:\n"
            "- **P-Shape**: Often forms in an uptrend or short-covering rally. The lower tail shows aggressive buying, with value establishing higher.\n"
            "- **b-Shape**: Often forms in a downtrend or long-liquidation. The upper tail shows aggressive selling, with value establishing lower.\n"
            "- **D-Shape**: Represents a balanced market. Buyers and sellers agree on price, forming a bell curve."
        )
    }
]

def get_all_modules() -> List[Dict[str, Any]]:
    return AUCTION_THEORY_MODULES

def get_module_by_id(module_id: str) -> Dict[str, Any]:
    for mod in AUCTION_THEORY_MODULES:
        if mod["id"] == module_id:
            return mod
    return {}
