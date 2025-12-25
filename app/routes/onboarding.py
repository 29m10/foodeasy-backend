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
    
    def fetch_meal_items():
        """Helper function to fetch meal items with meal types"""
        try:
            response = supabase.table("onboarding_meal_items_meal_types") \
                .select("""
                    onboarding_meal_item_id,
                    is_vegetarian,
                    is_eggetarian,
                    is_carnitarian,
                    is_omnivore,
                    is_vegan,
                    onboarding_meal_items!inner(id, name, image_url, is_active),
                    meal_types!inner(id, name)
                """) \
                .execute()
            
            # Transform the response to match the requested format
            # Filter for only active meal items
            formatted_data = []
            for item in response.data:
                meal_item = item.get("onboarding_meal_items", {})
                meal_type = item.get("meal_types", {})
                
                # Only include active meal items
                if meal_item.get("is_active") is not True:
                    continue
                
                formatted_item = {
                    "onboarding_meal_item_name": meal_item.get("name"),
                    "onboarding_meal_item_id": meal_item.get("id"),
                    "onboarding_meal_item_image_url": meal_item.get("image_url"),
                    "meal_type_name": meal_type.get("name"),
                    "meal_type_id": meal_type.get("id"),
                    "is_vegetarian": item.get("is_vegetarian"),
                    "is_eggetarian": item.get("is_eggetarian"),
                    "is_carnitarian": item.get("is_carnitarian"),
                    "is_omnivore": item.get("is_omnivore"),
                    "is_vegan": item.get("is_vegan")
                }
                formatted_data.append(formatted_item)
            
            return formatted_data
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


@router.get("/medical-restrictions", status_code=status.HTTP_200_OK)
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
            detail=f"Failed to fetch medical restrictions: {str(e)}"
        )


@router.get("/nutrition-preferences", status_code=status.HTTP_200_OK)
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
            detail=f"Failed to fetch nutrition preferences: {str(e)}"
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


@router.get("/meal-items", status_code=status.HTTP_200_OK)
async def get_meal_items() -> Dict[str, Any]:
    """
    Get all meal items with their meal types and dietary preferences.
    
    Returns:
        Dict containing success status and list of meal items with:
        - onboarding_meal_item_name
        - onboarding_meal_item_id
        - onboarding_meal_item_image_url
        - meal_type_name
        - meal_type_id
        - is_vegetarian
        - is_eggetarian
        - is_carnitarian
        - is_omnivore
        - is_vegan
        
    Only returns active onboarding_meal_items (is_active = true).
    """
    supabase = get_supabase_admin()
    
    try:
        # Query the join table with related data
        # Using inner join to ensure we only get records with valid relationships
        response = supabase.table("onboarding_meal_items_meal_types") \
            .select("""
                onboarding_meal_item_id,
                is_vegetarian,
                is_eggetarian,
                is_carnitarian,
                is_omnivore,
                is_vegan,
                onboarding_meal_items!inner(id, name, image_url, is_active),
                meal_types!inner(id, name)
            """) \
            .eq("onboarding_meal_items.is_active", True) \
            .execute()
        
        # Transform the response to match the requested format
        formatted_data = []
        for item in response.data:
            meal_item = item.get("onboarding_meal_items", {})
            meal_type = item.get("meal_types", {})
            
            formatted_item = {
                "onboarding_meal_item_name": meal_item.get("name"),
                "onboarding_meal_item_id": meal_item.get("id"),
                "onboarding_meal_item_image_url": meal_item.get("image_url"),
                "meal_type_name": meal_type.get("name"),
                "meal_type_id": meal_type.get("id"),
                "is_vegetarian": item.get("is_vegetarian"),
                "is_eggetarian": item.get("is_eggetarian"),
                "is_carnitarian": item.get("is_carnitarian"),
                "is_omnivore": item.get("is_omnivore"),
                "is_vegan": item.get("is_vegan")
            }
            formatted_data.append(formatted_item)
        
        return {
            "success": True,
            "data": formatted_data
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


