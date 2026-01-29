# app/dependencies/auth.py

from fastapi import Header, HTTPException, status, Depends
from typing import Optional

from app.services.jwt_service import verify_access_token
from app.services.auth_service import auth_service


async def get_current_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """
    Verify backend JWT and return authenticated user_id.
    Expects: Authorization: Bearer <access_token> (from /auth/verify-otp).
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user identifier",
            )
        # Optional: ensure user still exists and is active
        try:
            await auth_service.get_user_by_id(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or deactivated.",
            )
        return str(user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_user_access(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
) -> str:
    """Ensure the authenticated user matches the requested user_id."""
    current = str(current_user_id)
    requested = str(user_id)
    if current != requested:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )
    return requested
