"""
auth/billing.py
Billing Architecture. Handles Feature Flags and Rate Limits based on User Tier.
"""
from typing import Dict, Any
from .security import Role, User

TIER_LIMITS = {
    Role.RETAIL: {
        "max_historical_years": 1,
        "max_symbols_per_scan": 50,
        "features": {
            "l2_orderbook": False,
            "institutional_heatmap": False,
            "monte_carlo_sims": False
        },
        "api_rate_limit_per_min": 10
    },
    Role.PRO: {
        "max_historical_years": 5,
        "max_symbols_per_scan": 500,
        "features": {
            "l2_orderbook": True,
            "institutional_heatmap": True,
            "monte_carlo_sims": True
        },
        "api_rate_limit_per_min": 100
    },
    Role.INSTITUTIONAL: {
        "max_historical_years": 20,
        "max_symbols_per_scan": 5000,
        "features": {
            "l2_orderbook": True,
            "institutional_heatmap": True,
            "monte_carlo_sims": True,
            "fix_api_access": True
        },
        "api_rate_limit_per_min": 1000
    },
    Role.ADMIN: {
        "max_historical_years": 100,
        "max_symbols_per_scan": 100000,
        "features": {
            "l2_orderbook": True,
            "institutional_heatmap": True,
            "monte_carlo_sims": True,
            "fix_api_access": True,
            "admin_telemetry": True
        },
        "api_rate_limit_per_min": 9999
    }
}

def get_user_limits(user: User) -> Dict[str, Any]:
    """Returns the billing and feature limits for the current user's role."""
    return TIER_LIMITS.get(user.role, TIER_LIMITS[Role.RETAIL])
