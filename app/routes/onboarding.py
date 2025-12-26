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

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get all onboarding reference data",
    description="""
    Get all onboarding reference data in a single request.
    
    This endpoint fetches all available options for the onboarding flow in parallel,
    including goals, dietary patterns, restrictions, preferences, and meal items.
    
    **Returns:**
    - goals: Available health/fitness goals
    - dietary_patterns: Vegetarian, Vegan, etc.
    - dietary_restrictions: Food restrictions (No Onion No Garlic, etc.)
    - medical_restrictions: Medical conditions (Diabetes, etc.)
    - nutrition_preferences: High Protein, Low Carb, etc.
    - spice_levels: Mild, Medium, Hot, etc.
    - cooking_oils: Available cooking oil options
    - cuisines: Available cuisine types
    - meal_items: Meal items with meal types and dietary flags
    
    **Performance:** All data is fetched in parallel for optimal response time.
    Only returns active items (is_active = true) ordered by display_order.
    """
)
async def get_all_onboarding_data() -> Dict[str, Any]:
    """
    Get all onboarding reference data in a single request.
    
    Returns:
        Dict containing success status and all onboarding data:
        - goals
        - dietary_patterns
        - dietary_restrictions
        - medical_restrictions
        - nutrition_preferences
        - spice_levels
        - cooking_oils
        - cuisines
        - meal_items
    """
    supabase = get_supabase_admin()
    
    def remove_created_at(items):
        """Helper function to remove created_at from a list of items"""
        return [{k: v for k, v in item.items() if k != "created_at"} for item in items]
    
    def fetch_table_data(table_name: str):
        """Helper function to fetch data from a table"""
        try:
            response = supabase.table(table_name) \
                .select("*") \
                .eq("is_active", True) \
                .order("display_order") \
                .execute()
            return remove_created_at(response.data)
        except Exception as e:
            raise Exception(f"Failed to fetch {table_name}: {str(e)}")
    
    def fetch_meal_items():
        """Helper function to fetch meal items"""
        try:
            response = supabase.table("onboarding_meal_items") \
                .select("*") \
                .eq("is_active", True) \
                .order("id") \
                .execute()
            
            # Remove created_at from each item
            return remove_created_at(response.data)
        except Exception as e:
            raise Exception(f"Failed to fetch meal items: {str(e)}")
    
    try:
        # Fetch all tables in parallel using thread pool executor
        loop = asyncio.get_event_loop()
        
        goals_task = loop.run_in_executor(
            executor, 
            fetch_table_data, 
            "onboarding_goals"
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
        medical_restrictions_task = loop.run_in_executor(
            executor,
            fetch_table_data,
            "onboarding_medical_restrictions"
        )
        nutrition_preferences_task = loop.run_in_executor(
            executor,
            fetch_table_data,
            "onboarding_nutrition_preferences"
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
        meal_items_task = loop.run_in_executor(
            executor,
            fetch_meal_items
        )
        
        # Wait for all tasks to complete
        goals, dietary_patterns, dietary_restrictions, medical_restrictions, \
        nutrition_preferences, spice_levels, cooking_oils, cuisines, meal_items = await asyncio.gather(
            goals_task,
            dietary_patterns_task,
            dietary_restrictions_task,
            medical_restrictions_task,
            nutrition_preferences_task,
            spice_levels_task,
            cooking_oils_task,
            cuisines_task,
            meal_items_task
        )
        
        return {
            "success": True,
            "data": {
                "goals": goals,
                "dietary_patterns": dietary_patterns,
                "dietary_restrictions": dietary_restrictions,
                "medical_restrictions": medical_restrictions,
                "nutrition_preferences": nutrition_preferences,
                "spice_levels": spice_levels,
                "cooking_oils": cooking_oils,
                "cuisines": cuisines,
                "meal_items": meal_items
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

@router.get(
    "/goals",
    status_code=status.HTTP_200_OK,
    summary="Get all available goals",
    description="""
    Get all available health and fitness goals for onboarding.
    
    Returns a list of active goals (e.g., "Weight Loss", "Muscle Gain", "General Health")
    ordered by display_order. Only returns goals where is_active = true.
    
    **Note:** Use the main endpoint GET /onboarding to get all data in one request.
    """
)
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
        
        # Remove created_at from each item
        data = [{k: v for k, v in item.items() if k != "created_at"} for item in response.data]
        
        return {
            "success": True,
            "data": data
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


@router.get(
    "/dietary-patterns",
    status_code=status.HTTP_200_OK,
    summary="Get all available dietary patterns",
    description="""
    Get all available dietary patterns for onboarding.
    
    Returns a list of active dietary patterns (e.g., "Vegetarian", "Vegan", "Non-Vegetarian")
    ordered by display_order. Only returns patterns where is_active = true.
    
    **Note:** Use the main endpoint GET /onboarding to get all data in one request.
    """
)
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
        
        # Remove created_at from each item
        data = [{k: v for k, v in item.items() if k != "created_at"} for item in response.data]
        
        return {
            "success": True,
            "data": data
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


@router.get(
    "/dietary-restrictions",
    status_code=status.HTTP_200_OK,
    summary="Get all available dietary restrictions",
    description="""
    Get all available dietary restrictions for onboarding.
    
    Returns a list of active dietary restrictions (e.g., "No Onion No Garlic", "No Egg")
    ordered by display_order. Only returns restrictions where is_active = true.
    
    **Note:** Use the main endpoint GET /onboarding to get all data in one request.
    """
)
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
        
        # Remove created_at from each item
        data = [{k: v for k, v in item.items() if k != "created_at"} for item in response.data]
        
        return {
            "success": True,
            "data": data
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


@router.get(
    "/medical-restrictions",
    status_code=status.HTTP_200_OK,
    summary="Get all available medical restrictions",
    description="""
    Get all available medical restrictions for onboarding.
    
    Returns a list of active medical restrictions (e.g., "Diabetes", "Hypertension", "PCOS")
    ordered by display_order. Only returns restrictions where is_active = true.
    
    **Note:** Use the main endpoint GET /onboarding to get all data in one request.
    """
)
async def get_medical_restrictions() -> Dict[str, Any]:
    """
    Get all available medical restrictions for onboarding.
    
    Returns:
        Dict containing success status and list of active medical restrictions ordered by display_order
    """
    supabase = get_supabase_admin()
    
    try:
        response = supabase.table("onboarding_medical_restrictions") \
            .select("*") \
            .eq("is_active", True) \
            .order("display_order") \
            .execute()
        
        # Remove created_at from each item
        data = [{k: v for k, v in item.items() if k != "created_at"} for item in response.data]
        
        return {
            "success": True,
            "data": data
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error in production (you might want to add logging here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch medical restrictions: {str(e)}"
        )


@router.get(
    "/nutrition-preferences",
    status_code=status.HTTP_200_OK,
    summary="Get all available nutrition preferences",
    description="""
    Get all available nutrition preferences for onboarding.
    
    Returns a list of active nutrition preferences (e.g., "High Protein", "Low Carb", "High Fiber")
    ordered by display_order. Only returns preferences where is_active = true.
    
    **Note:** Use the main endpoint GET /onboarding to get all data in one request.
    """
)
async def get_nutrition_preferences() -> Dict[str, Any]:
    """
    Get all available nutrition preferences for onboarding.
    
    Returns:
        Dict containing success status and list of active nutrition preferences ordered by display_order
    """
    supabase = get_supabase_admin()
    
    try:
        response = supabase.table("onboarding_nutrition_preferences") \
            .select("*") \
            .eq("is_active", True) \
            .order("display_order") \
            .execute()
        
        # Remove created_at from each item
        data = [{k: v for k, v in item.items() if k != "created_at"} for item in response.data]
        
        return {
            "success": True,
            "data": data
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error in production (you might want to add logging here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch nutrition preferences: {str(e)}"
        )


@router.get(
    "/spice-levels",
    status_code=status.HTTP_200_OK,
    summary="Get all available spice levels",
    description="""
    Get all available spice levels for onboarding.
    
    Returns a list of active spice levels (e.g., "Mild", "Medium", "Hot", "Very Hot")
    ordered by display_order. Only returns levels where is_active = true.
    
    **Note:** Use the main endpoint GET /onboarding to get all data in one request.
    """
)
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
        
        # Remove created_at from each item
        data = [{k: v for k, v in item.items() if k != "created_at"} for item in response.data]
        
        return {
            "success": True,
            "data": data
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


@router.get(
    "/cooking-oils",
    status_code=status.HTTP_200_OK,
    summary="Get all available cooking oils",
    description="""
    Get all available cooking oils for onboarding.
    
    Returns a list of active cooking oils (e.g., "Olive Oil", "Coconut Oil", "Mustard Oil")
    ordered by display_order. Only returns oils where is_active = true.
    
    **Note:** Use the main endpoint GET /onboarding to get all data in one request.
    """
)
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
        
        # Remove created_at from each item
        data = [{k: v for k, v in item.items() if k != "created_at"} for item in response.data]
        
        return {
            "success": True,
            "data": data
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


@router.get(
    "/cuisines",
    status_code=status.HTTP_200_OK,
    summary="Get all available cuisines",
    description="""
    Get all available cuisines for onboarding.
    
    Returns a list of active cuisines (e.g., "North Indian", "South Indian", "Chinese")
    ordered by display_order. Only returns cuisines where is_active = true.
    
    **Note:** Use the main endpoint GET /onboarding to get all data in one request.
    """
)
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
        
        # Remove created_at from each item
        data = [{k: v for k, v in item.items() if k != "created_at"} for item in response.data]
        
        return {
            "success": True,
            "data": data
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


@router.get(
    "/meal-items",
    status_code=status.HTTP_200_OK,
    summary="Get all meal items",
    description="""
    Get all meal items from the onboarding_meal_items table.
    
    Returns all records with all columns from the onboarding_meal_items table.
    
    **Note:** Use the main endpoint GET /onboarding to get all data in one request.
    """
)
async def get_meal_items() -> Dict[str, Any]:
    """
    Get all meal items.
    
    Returns:
        Dict containing success status and list of all meal items with all columns from the onboarding_meal_items table.
    """
    supabase = get_supabase_admin()
    
    try:
        # Query the onboarding_meal_items table directly - return all records and all columns
        response = supabase.table("onboarding_meal_items") \
            .select("*") \
            .order("id") \
            .execute()
        
        # Remove created_at from each item
        data_without_created_at = [{k: v for k, v in item.items() if k != "created_at"} for item in response.data]
        
        return {
            "success": True,
            "data": data_without_created_at
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error in production (you might want to add logging here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch meal items: {str(e)}"
        )


