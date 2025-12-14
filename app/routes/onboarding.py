from fastapi import APIRouter, HTTPException, status
from app.services.supabase_client import get_supabase_admin
from typing import Dict, Any

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

# ============================================
# GET REFERENCE DATA
# ============================================

@router.get("/goals", status_code=status.HTTP_200_OK)
async def get_goals() -> Dict[str, Any]:
    """
    Get all available goals for onboarding.
    
    Returns:
        Dict containing success status and list of active goals ordered by display_order
    """
    supabase = get_supabase_admin()
    
    try:
        response = supabase.table("onboarding_goals") \
            .select("*") \
            .eq("is_active", True) \
            .order("display_order") \
            .execute()
        
        return {
            "success": True,
            "data": response.data
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error in production (you might want to add logging here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch goals: {str(e)}"
        )


@router.get("/medical-deficiencies", status_code=status.HTTP_200_OK)
async def get_medical_deficiencies() -> Dict[str, Any]:
    """
    Get all available medical deficiencies for onboarding.
    
    Returns:
        Dict containing success status and list of active medical deficiencies ordered by display_order
    """
    supabase = get_supabase_admin()
    
    try:
        response = supabase.table("onboarding_medical_deficiencies") \
            .select("*") \
            .eq("is_active", True) \
            .order("display_order") \
            .execute()
        
        return {
            "success": True,
            "data": response.data
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error in production (you might want to add logging here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch medical deficiencies: {str(e)}"
        )


@router.get("/dietary-patterns", status_code=status.HTTP_200_OK)
async def get_dietary_patterns() -> Dict[str, Any]:
    """
    Get all available dietary patterns for onboarding.
    
    Returns:
        Dict containing success status and list of active dietary patterns ordered by display_order
    """
    supabase = get_supabase_admin()
    
    try:
        response = supabase.table("onboarding_dietary_patterns") \
            .select("*") \
            .eq("is_active", True) \
            .order("display_order") \
            .execute()
        
        return {
            "success": True,
            "data": response.data
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error in production (you might want to add logging here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dietary patterns: {str(e)}"
        )


@router.get("/dietary-restrictions", status_code=status.HTTP_200_OK)
async def get_dietary_restrictions() -> Dict[str, Any]:
    """
    Get all available dietary restrictions for onboarding.
    
    Returns:
        Dict containing success status and list of active dietary restrictions ordered by display_order
    """
    supabase = get_supabase_admin()
    
    try:
        response = supabase.table("onboarding_dietary_restrictions") \
            .select("*") \
            .eq("is_active", True) \
            .order("display_order") \
            .execute()
        
        return {
            "success": True,
            "data": response.data
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error in production (you might want to add logging here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dietary restrictions: {str(e)}"
        )


@router.get("/spice-levels", status_code=status.HTTP_200_OK)
async def get_spice_levels() -> Dict[str, Any]:
    """
    Get all available spice levels for onboarding.
    
    Returns:
        Dict containing success status and list of active spice levels ordered by display_order
    """
    supabase = get_supabase_admin()
    
    try:
        response = supabase.table("onboarding_spice_levels") \
            .select("*") \
            .eq("is_active", True) \
            .order("display_order") \
            .execute()
        
        return {
            "success": True,
            "data": response.data
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error in production (you might want to add logging here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch spice levels: {str(e)}"
        )


@router.get("/cooking-oils", status_code=status.HTTP_200_OK)
async def get_cooking_oils() -> Dict[str, Any]:
    """
    Get all available cooking oils for onboarding.
    
    Returns:
        Dict containing success status and list of active cooking oils ordered by display_order
    """
    supabase = get_supabase_admin()
    
    try:
        response = supabase.table("onboarding_cooking_oils") \
            .select("*") \
            .eq("is_active", True) \
            .order("display_order") \
            .execute()
        
        return {
            "success": True,
            "data": response.data
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error in production (you might want to add logging here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch cooking oils: {str(e)}"
        )


@router.get("/cuisines", status_code=status.HTTP_200_OK)
async def get_cuisines() -> Dict[str, Any]:
    """
    Get all available cuisines for onboarding.
    
    Returns:
        Dict containing success status and list of active cuisines ordered by display_order
    """
    supabase = get_supabase_admin()
    
    try:
        response = supabase.table("onboarding_cuisines") \
            .select("*") \
            .eq("is_active", True) \
            .order("display_order") \
            .execute()
        
        return {
            "success": True,
            "data": response.data
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error in production (you might want to add logging here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch cuisines: {str(e)}"
        )


