from functools import wraps
from fastapi import HTTPException, status
from typing import Callable

ROLE_PERMISSIONS = {
    "viewer": ["read_summary"],
    "analyst": ["read_records", "analytics"],
    "admin": ["read", "create", "update", "delete", "manage_users"]
}

def require_role(required_role: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request or not hasattr(request, "state"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")
            
            current_user = getattr(request.state, "user", None)
            if not current_user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
            
            if current_user.role_name.lower() != required_role.lower():
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator