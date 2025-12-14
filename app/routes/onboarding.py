from fastapi import APIRouter, HTTPException, status
from app.services.supabase_client import get_supabase_admin
from typing import Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

# Thread pool executor for running synchronous Supabase queries in parallel
executor = ThreadPoolExecutor(max_workers=10)

# ============================================
# GET ALL ONBOARDING DATA (COMBINED)
# ============================================

@router.get("", status_code=status.HTTP_200_OK)
async def get_all_onboarding_data() -> Dict[str, Any]:
    """
    Get all onboarding reference data in a single request.
    
    Returns:
        Dict containing success status and all onboarding data:
        - goals
        - medical_deficiencies
        - dietary_patterns
        - dietary_restrictions
        - spice_levels
        - cooking_oils
        - cuisines
    """
    supabase = get_supabase_admin()
    
    def fetch_table_data(table_name: str):
        """Helper function to fetch data from a table"""
        try:
            response = supabase.table(table_name) \
                .select("*") \
                .eq("is_active", True) \
                .order("display_order") \
                .execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to fetch {table_name}: {str(e)}")
    
    try:
        # Fetch all tables in parallel using thread pool executor
        loop = asyncio.get_event_loop()
        
        goals_task = loop.run_in_executor(
            executor, 
            fetch_table_data, 
            "onboarding_goals"
        )
        medical_deficiencies_task = loop.run_in_executor(
            executor,
            fetch_table_data,
            "onboarding_medical_deficiencies"
        )
        dietary_patterns_task = loop.run_in_executor(
            executor,
            fetch_table_data,
            "onboarding_dietary_patterns"
        )
        dietary_restrictions_task = loop.run_in_executor(
            executor,
            fetch_table_data,
            "onboarding_dietary_restrictions"
        )
        spice_levels_task = loop.run_in_executor(
            executor,
            fetch_table_data,
            "onboarding_spice_levels"
        )
        cooking_oils_task = loop.run_in_executor(
            executor,
            fetch_table_data,
            "onboarding_cooking_oils"
        )
        cuisines_task = loop.run_in_executor(
            executor,
            fetch_table_data,
            "onboarding_cuisines"
        )
        
        # Wait for all tasks to complete
        goals, medical_deficiencies, dietary_patterns, dietary_restrictions, \
        spice_levels, cooking_oils, cuisines = await asyncio.gather(
            goals_task,
            medical_deficiencies_task,
            dietary_patterns_task,
            dietary_restrictions_task,
            spice_levels_task,
            cooking_oils_task,
            cuisines_task
        )
        
        return {
            "success": True,
            "data": {
                "goals": goals,
                "medical_deficiencies": medical_deficiencies,
                "dietary_patterns": dietary_patterns,
                "dietary_restrictions": dietary_restrictions,
                "spice_levels": spice_levels,
                "cooking_oils": cooking_oils,
                "cuisines": cuisines
            }
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error in production (you might want to add logging here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch onboarding data: {str(e)}"
        )


# ============================================
# GET REFERENCE DATA (INDIVIDUAL ENDPOINTS)
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


