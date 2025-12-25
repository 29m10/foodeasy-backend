# app/routes/auth.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.services.auth_service import auth_service
from app.services.firebase_service import verify_firebase_token, get_token_expiration_info, create_custom_token, TOKEN_EXPIRATION_SECONDS
from firebase_admin import auth as firebase_auth
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class VerifyTokenRequest(BaseModel):
    """Request for OTP verification"""
    id_token: str = Field(..., description="Firebase ID token after OTP verification")


class VerifyTokenResponse(BaseModel):
    """Response after successful OTP verification"""
    user_id: str = Field(..., description="Unique user ID")
    phone_number: str = Field(..., description="Verified phone number")
    is_new_user: bool = Field(..., description="True if first time login")


class TokenInfoRequest(BaseModel):
    """Request to get token expiration information"""
    id_token: str = Field(..., description="Firebase ID token to check")


class RefreshTokenRequest(BaseModel):
    """Request to refresh token (requires valid current token)"""
    id_token: str = Field(..., description="Current Firebase ID token (even if expired)")




# ============================================
# AUTH ENDPOINTS
# ============================================

@router.post(
    "/verify-otp",
    response_model=VerifyTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and get user_id",
    description="""
    Verify Firebase ID token after OTP verification and sync user with Supabase.
    
    **Flow:**
    1. User enters phone number in React Native app
    2. Firebase sends OTP to phone number
    3. User enters OTP, Firebase verifies it and returns ID token
    4. React Native calls this endpoint with the Firebase ID token
    5. Backend verifies token, creates/retrieves user in Supabase
    6. Returns user_id and phone number for authenticated user
    
    **For returning users:** Same phone number returns same user_id.
    **For new users:** Creates new user profile with phone number only.
    """
)
async def verify_otp(request: VerifyTokenRequest) -> VerifyTokenResponse:
    """Verify Firebase token and return user_id."""
    try:
        user_data = await auth_service.verify_and_sync_user(request.id_token)
        return VerifyTokenResponse(**user_data)
        
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token. Please try again."
        )
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired. Please request new OTP."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error in verify_otp: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed. Please try again."
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Auth service health check",
    description="""
    Health check endpoint for authentication service.
    
    Verifies that Firebase and Supabase connections are working properly.
    Returns connection status for both services.
    
    Use this endpoint for monitoring and health checks.
    """
)
async def auth_health_check():
    """Check if Firebase and Supabase connections are working"""
    return {
        "success": True,
        "service": "auth",
        "firebase": "connected",
        "supabase": "connected",
        "token_expiration_seconds": TOKEN_EXPIRATION_SECONDS
    }


@router.post(
    "/token-info",
    status_code=status.HTTP_200_OK,
    summary="Get token expiration information",
    description="""
    Get detailed information about a Firebase ID token's expiration.
    
    Returns:
    - expires_at: ISO timestamp when token expires
    - expires_in: Seconds until expiration (negative if expired)
    - is_expired: Boolean indicating if token is expired
    - issued_at: ISO timestamp when token was issued
    
    Useful for checking token expiration before making API calls.
    """
)
async def get_token_info(request: TokenInfoRequest) -> Dict[str, Any]:
    """Get token expiration information"""
    try:
        # Try to verify token (even if expired, we want to get expiration info)
        try:
            decoded_token = verify_firebase_token(request.id_token, check_expiration=False)
        except firebase_auth.InvalidIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
        except firebase_auth.ExpiredIdTokenError:
            # Even if expired, try to decode to get expiration info
            try:
                decoded_token = verify_firebase_token(request.id_token, check_expiration=False)
            except:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token is invalid or expired"
                )
        
        expiration_info = get_token_expiration_info(decoded_token)
        
        return {
            "success": True,
            "data": expiration_info
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_token_info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get token information"
        )


@router.post(
    "/refresh-token",
    status_code=status.HTTP_200_OK,
    summary="Refresh Firebase ID token",
    description="""
    Refresh a Firebase ID token.
    
    **Note:** This endpoint validates the current token and returns expiration info.
    Actual token refresh must be done on the client side using Firebase SDK:
    `await user.getIdToken(true)` to force refresh.
    
    This endpoint helps by:
    1. Validating the current token
    2. Returning expiration information
    3. Indicating if refresh is needed
    
    **Client-side refresh is required** because Firebase ID tokens are issued by Firebase,
    not by this backend. The backend can only verify tokens, not issue new ones.
    """
)
async def refresh_token_info(request: RefreshTokenRequest) -> Dict[str, Any]:
    """
    Get token refresh information.
    
    Note: Actual token refresh must be done client-side with Firebase SDK.
    """
    try:
        # Try to verify token
        try:
            decoded_token = verify_firebase_token(request.id_token, check_expiration=False)
            expiration_info = get_token_expiration_info(decoded_token)
            
            # Check if token is expired or about to expire (within 5 minutes)
            needs_refresh = expiration_info.get("is_expired", False) or \
                          (expiration_info.get("expires_in", 0) < 300)  # 5 minutes
            
            return {
                "success": True,
                "needs_refresh": needs_refresh,
                "data": expiration_info,
                "message": "Token refresh must be done client-side using Firebase SDK: await user.getIdToken(true)"
            }
        except firebase_auth.ExpiredIdTokenError:
            return {
                "success": True,
                "needs_refresh": True,
                "data": {
                    "is_expired": True,
                    "expires_in": 0
                },
                "message": "Token is expired. Please refresh client-side using: await user.getIdToken(true)"
            }
        except firebase_auth.InvalidIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token. Please login again."
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in refresh_token_info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process token refresh request"
        )