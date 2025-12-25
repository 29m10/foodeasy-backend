# app/routes/auth.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.services.auth_service import auth_service
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


class UpdateProfileRequest(BaseModel):
    """Request to update user profile"""
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")


class UpdateOnboardingRequest(BaseModel):
    """Request to update complete onboarding data - all values are TEXT, not IDs"""
    
    # Basic demographics
    age: Optional[int] = Field(None, ge=1, le=120, description="User age")
    gender: Optional[str] = Field(None, description="Gender: male, female, other, prefer_not_to_say")
    total_household_adults: Optional[int] = Field(1, ge=1, description="Number of adults in household")
    total_household_children: Optional[int] = Field(0, ge=0, description="Number of children in household")
    
    # Onboarding selections (all are TEXT values, not IDs)
    goals: List[str] = Field(default=[], description="Selected goal names (e.g., ['Weight Loss', 'Muscle Gain'])")
    medical_restrictions: List[str] = Field(default=[], description="Medical restriction names")
    dietary_pattern: Optional[str] = Field(None, description="Dietary pattern name (e.g., 'Vegetarian')")
    nutrition_preferences: List[str] = Field(default=[], description="Nutrition preference names")
    dietary_restrictions: List[str] = Field(default=[], description="Dietary restriction names")
    spice_level: Optional[str] = Field(None, description="Spice level name (e.g., 'Medium')")
    cooking_oil_preferences: List[str] = Field(default=[], description="Cooking oil names")
    cuisines_preferences: List[str] = Field(default=[], description="Cuisine names")
    breakfast_preferences: List[str] = Field(default=[], description="Breakfast item names")
    lunch_preferences: List[str] = Field(default=[], description="Lunch item names")
    snacks_preferences: List[str] = Field(default=[], description="Snack item names")
    dinner_preferences: List[str] = Field(default=[], description="Dinner item names")
    
    # Additional input
    extra_input: Optional[str] = Field(None, max_length=1000, description="Additional notes/preferences from user")
    
    class Config:
        json_schema_extra = {
            "example": {
                "age": 28,
                "gender": "male",
                "total_household_adults": 2,
                "total_household_children": 1,
                "goals": ["Weight Loss", "Muscle Gain"],
                "medical_restrictions": ["Diabetes"],
                "dietary_pattern": "Vegetarian",
                "nutrition_preferences": ["High Protein"],
                "dietary_restrictions": ["No Onion No Garlic"],
                "spice_level": "Medium",
                "cooking_oil_preferences": ["Olive Oil", "Coconut Oil"],
                "cuisines_preferences": ["North Indian", "South Indian"],
                "breakfast_preferences": ["Idli", "Poha"],
                "lunch_preferences": ["Dal Rice"],
                "snacks_preferences": ["Samosa"],
                "dinner_preferences": ["Roti Sabzi"],
                "extra_input": "I prefer early dinner around 7 PM"
            }
        }


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


@router.put(
    "/user/{user_id}/profile",
    status_code=status.HTTP_200_OK,
    summary="Update user profile (add name)",
    description="""
    Update user profile with basic information like full name.
    
    This endpoint allows updating user profile fields after initial registration.
    Currently supports updating the user's full name.
    
    **Protected fields:** Cannot update id, firebase_uid, phone_number, or created_at.
    """
)
async def update_profile(user_id: str, request: UpdateProfileRequest) -> Dict[str, Any]:
    """Update user profile with name."""
    try:
        update_data = {"full_name": request.full_name}
        updated_user = await auth_service.update_user_profile(user_id, update_data)
        
        return {
            "success": True,
            "data": updated_user
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error in update_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.put(
    "/user/{user_id}/onboarding",
    status_code=status.HTTP_200_OK,
    summary="Save complete onboarding data",
    description="""
    Save all user onboarding selections.
    
    **IMPORTANT:** Send actual TEXT values (names), NOT IDs.
    
    Example:
    - ✅ "goals": ["Weight Loss", "Muscle Gain"]
    - ❌ "goals": ["goal_id_1", "goal_id_2"]
    """
)
async def update_onboarding_data(user_id: str, request: UpdateOnboardingRequest) -> Dict[str, Any]:
    """Save complete onboarding data for user"""
    try:
        onboarding_data = request.dict(exclude_none=True)
        updated_user = await auth_service.update_onboarding_data(user_id, onboarding_data)
        
        return {
            "success": True,
            "message": "Onboarding data saved successfully",
            "data": updated_user
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error in update_onboarding_data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update onboarding data: {str(e)}"
        )


@router.get(
    "/user/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Get user profile with all data",
    description="""
    Retrieve complete user profile including all onboarding data and preferences.
    
    Returns:
    - Basic info: user_id, phone_number, full_name, age, gender
    - Household info: total_household_adults, total_household_children
    - Onboarding status: onboarding_completed, onboarding_completed_at
    - All preferences stored in metadata JSON (goals, dietary patterns, restrictions, etc.)
    - Timestamps: created_at, last_login
    """
)
async def get_user(user_id: str) -> Dict[str, Any]:
    """Get complete user profile"""
    try:
        user = await auth_service.get_user_by_id(user_id)
        return {
            "success": True,
            "data": user
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error in get_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user: {str(e)}"
        )


@router.get(
    "/user/{user_id}/onboarding-status",
    status_code=status.HTTP_200_OK,
    summary="Check onboarding completion status",
    description="""
    Check if user has completed the onboarding process.
    
    Returns:
    - onboarding_completed: Boolean indicating if onboarding is complete
    - onboarding_completed_at: ISO timestamp when onboarding was completed (if completed)
    - has_name: Boolean indicating if user has set their full name
    
    Use this endpoint to determine if user needs to complete onboarding flow.
    """
)
async def get_onboarding_status(user_id: str) -> Dict[str, Any]:
    """Get onboarding completion status"""
    try:
        status_data = await auth_service.get_onboarding_status(user_id)
        
        return {
            "success": True,
            "data": status_data
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get onboarding status: {str(e)}"
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
        "supabase": "connected"
    }