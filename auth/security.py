"""
auth/security.py
Role-Based Access Control (RBAC) and Multi-Tenancy Mock System.
Defines Tiers, Permissions, and User Authentication dependencies.
"""

from enum import Enum
from typing import Dict, Any, List
from fastapi import Header, HTTPException, Depends

class Role(str, Enum):
    RETAIL = "RETAIL"
    PRO = "PRO"
    INSTITUTIONAL = "INSTITUTIONAL"
    ADMIN = "ADMIN"

class User:
    def __init__(self, user_id: str, email: str, role: Role, organization: str = "Individual"):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.organization = organization

# In-memory mock database of users for Phase 7 demonstration
MOCK_USERS = {
    "token_retail_123": User("u_001", "retail@example.com", Role.RETAIL),
    "token_pro_456": User("u_002", "pro@example.com", Role.PRO),
    "token_inst_789": User("u_003", "trader@hedgefund.com", Role.INSTITUTIONAL, "Alpha Fund LLC"),
    "token_admin_999": User("u_000", "admin@alphapulse.com", Role.ADMIN, "AlphaPulse Inc")
}

async def get_current_user(authorization: str = Header(default="Bearer token_retail_123")) -> User:
    """
    FastAPI dependency to authenticate users. 
    Defaults to RETAIL for unauthenticated ease of testing, 
    but strictly enforces based on passed token.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
    token = authorization.split(" ")[1]
    
    user = MOCK_USERS.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    return user

def require_roles(allowed_roles: List[Role]):
    """Decorator / Dependency factory to restrict endpoints to specific roles."""
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles and user.role != Role.ADMIN:
            raise HTTPException(
                status_code=403, 
                detail=f"Operation not permitted. Required roles: {[r.value for r in allowed_roles]}"
            )
        return user
    return role_checker
