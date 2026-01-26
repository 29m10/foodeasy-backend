"""
Meal Items Routes

Routes for fetching meal items with various filters.
"""

from fastapi import APIRouter, HTTPException, status, Query
from app.services.supabase_client import get_supabase_admin
from typing import Dict, Any, Optional, List

router = APIRouter(prefix="/meal-items", tags=["Meal Items"])


async def _fetch_grocery_items_for_meal_items(meal_item_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
    """
    Fetch all grocery items for multiple meal items.
    Each grocery item includes its details and tag from meal_item_ingredients table.
    
    Args:
        meal_item_ids: List of meal item IDs to fetch groceries for
        
    Returns:
        Dict mapping meal_item_id to list of grocery items
        Example: {
            1: [
                {
                    "id": 10,
                    "name": "Rice",
                    "type": "Grains, Cereals & Grain Products",
                    "type_id": 1,
                    "tag": "main_item"
                },
                {
                    "id": 11,
                    "name": "Tomato",
                    "type": "Vegetables",
                    "type_id": 3,
                    "tag": "vegetable_item"
                }
            ]
        }
    """
    if not meal_item_ids:
        return {}
    
    supabase = get_supabase_admin()
    
    try:
        # Fetch ingredients with tags from meal_item_ingredients junction table
        ingredients_response = supabase.table("meal_item_ingredients") \
            .select("""
                meal_item_id,
                is_main_item,
                is_fruit_item,
                is_vegetable_item,
                is_spices_seeds_oils_item,
                meal_ingredients (
                    id,
                    name,
                    meal_ingredients_types (
                        id,
                        name
                    )
                )
            """) \
            .in_("meal_item_id", meal_item_ids) \
            .eq("is_active", True) \
            .execute()
        
        # Group ingredients by meal_item_id as a list
        meal_item_groceries = {}
        
        # Define tag field mappings
        tag_fields = {
            "is_main_item": "main_item",
            "is_fruit_item": "fruit_item",
            "is_vegetable_item": "vegetable_item",
            "is_spices_seeds_oils_item": "spices_seeds_oils_item"
        }
        
        if ingredients_response.data:
            for item in ingredients_response.data:
                meal_item_id = item.get("meal_item_id")
                ingredient_data = item.get("meal_ingredients")
                
                if not ingredient_data or not meal_item_id:
                    continue
                
                # Initialize list for this meal item if not exists
                if meal_item_id not in meal_item_groceries:
                    meal_item_groceries[meal_item_id] = []
                
                # Get ingredient details
                ingredient_name = ingredient_data.get("name")
                ingredient_id = ingredient_data.get("id")
                ingredient_type_data = ingredient_data.get("meal_ingredients_types")
                
                if not ingredient_name:
                    continue
                
                # Get type name, default to "Uncategorized"
                type_name = "Uncategorized"
                type_id = None
                if ingredient_type_data:
                    type_name = ingredient_type_data.get("name", "Uncategorized")
                    type_id = ingredient_type_data.get("id")
                
                # Find the first active tag (only one tag per grocery item)
                tag = None
                for field_name, tag_name in tag_fields.items():
                    if item.get(field_name, False):
                        tag = tag_name
                        break
                
                # Create grocery item object
                grocery_item = {
                    "id": ingredient_id,
                    "name": ingredient_name,
                    "type": type_name,
                    "type_id": type_id,
                    "tag": tag
                }
                
                # Add to the list for this meal item
                meal_item_groceries[meal_item_id].append(grocery_item)
        
        return meal_item_groceries
        
    except Exception as e:
        print(f"Error fetching grocery items for meal items: {e}")
        return {}


async def _fetch_nutrients_for_meal_items(meal_item_ids: List[int]) -> Dict[int, List[Dict[str, str]]]:
    """
    Fetch nutrients with hex colors for multiple meal items.
    
    Args:
        meal_item_ids: List of meal item IDs to fetch nutrients for
        
    Returns:
        Dict mapping meal_item_id to list of nutrients with their hex colors
        Example: {
            1: [
                {"nutrient": "Protein", "color_hex": "#FF5733"},
                {"nutrient": "Carbohydrates", "color_hex": "#33FF57"}
            ],
            2: [
                {"nutrient": "Fiber", "color_hex": "#3357FF"}
            ]
        }
    """
    if not meal_item_ids:
        return {}
    
    supabase = get_supabase_admin()
    
    try:
        # Fetch nutrients for these meal items using the junction table
        nutrients_response = supabase.table("meal_item_nutrients") \
            .select("""
                meal_item_id,
                master_nutrients (
                    nutrient,
                    color_hex
                )
            """) \
            .in_("meal_item_id", meal_item_ids) \
            .eq("is_active", True) \
            .execute()
        
        # Group nutrients by meal_item_id
        meal_item_nutrients = {}
        
        if nutrients_response.data:
            for item in nutrients_response.data:
                meal_item_id = item.get("meal_item_id")
                nutrient_data = item.get("master_nutrients")
                
                if not nutrient_data or not meal_item_id:
                    continue
                
                # Initialize list for this meal item if not exists
                if meal_item_id not in meal_item_nutrients:
                    meal_item_nutrients[meal_item_id] = []
                
                # Get nutrient name and color_hex
                nutrient_name = nutrient_data.get("nutrient")
                color_hex = nutrient_data.get("color_hex")
                
                if not nutrient_name or not color_hex:
                    continue
                
                # Create nutrient object
                nutrient_obj = {
                    "nutrient": nutrient_name,
                    "color_hex": color_hex
                }
                
                # Avoid duplicates (check if this nutrient already exists for this meal item)
                if nutrient_obj not in meal_item_nutrients[meal_item_id]:
                    meal_item_nutrients[meal_item_id].append(nutrient_obj)
        
        return meal_item_nutrients
        
    except Exception as e:
        print(f"Error fetching nutrients for meal items: {e}")
        return {}


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get active meal items with filters",
    description="""
    Get active meal items from the meal_items table with optional filters.
    
    **Filters available:**
    - can_vegetarian_eat: Filter by vegetarian compatibility (true/false)
    - can_eggetarian_eat: Filter by eggetarian compatibility (true/false)
    - can_carnitarian_eat: Filter by carnitarian compatibility (true/false)
    - can_omnitarian_eat: Filter by omnitarian compatibility (true/false)
    - can_vegan_eat: Filter by vegan compatibility (true/false)
    - is_breakfast: Filter by breakfast meal type (true/false)
    - is_lunch: Filter by lunch meal type (true/false)
    - is_dinner: Filter by dinner meal type (true/false)
    - is_snacks: Filter by snacks meal type (true/false)
    
    **Note:** All filters are optional. If no filters are provided, all active meal items are returned.
    Only returns items where is_active = true.
    Response excludes created_at and is_active fields.
    """
)
async def get_meal_items(
    can_vegetarian_eat: Optional[bool] = Query(None, description="Filter by vegetarian compatibility"),
    can_eggetarian_eat: Optional[bool] = Query(None, description="Filter by eggetarian compatibility"),
    can_carnitarian_eat: Optional[bool] = Query(None, description="Filter by carnitarian compatibility"),
    can_omnitarian_eat: Optional[bool] = Query(None, description="Filter by omnitarian compatibility"),
    can_vegan_eat: Optional[bool] = Query(None, description="Filter by vegan compatibility"),
    is_breakfast: Optional[bool] = Query(None, description="Filter by breakfast meal type"),
    is_lunch: Optional[bool] = Query(None, description="Filter by lunch meal type"),
    is_dinner: Optional[bool] = Query(None, description="Filter by dinner meal type"),
    is_snacks: Optional[bool] = Query(None, description="Filter by snacks meal type")
) -> Dict[str, Any]:
    """
    Get active meal items with optional filters.
    
    Returns:
        Dict containing success status and list of filtered meal items.
        Response excludes created_at and is_active fields.
    """
    supabase = get_supabase_admin()
    
    try:
        # Start with base query - only active items
        query = supabase.table("meal_items") \
            .select("*") \
            .eq("is_active", True)
        
        # Apply dietary pattern filters
        if can_vegetarian_eat is not None:
            query = query.eq("can_vegetarian_eat", can_vegetarian_eat)
        
        if can_eggetarian_eat is not None:
            query = query.eq("can_eggetarian_eat", can_eggetarian_eat)
        
        if can_carnitarian_eat is not None:
            query = query.eq("can_carnitarian_eat", can_carnitarian_eat)
        
        if can_omnitarian_eat is not None:
            query = query.eq("can_omnitarian_eat", can_omnitarian_eat)
        
        if can_vegan_eat is not None:
            query = query.eq("can_vegan_eat", can_vegan_eat)
        
        # Apply meal type filters (these are boolean fields in the table)
        if is_breakfast is not None:
            query = query.eq("is_breakfast", is_breakfast)
        
        if is_lunch is not None:
            query = query.eq("is_lunch", is_lunch)
        
        if is_dinner is not None:
            query = query.eq("is_dinner", is_dinner)
        
        if is_snacks is not None:
            query = query.eq("is_snacks", is_snacks)
        
        # Execute query
        response = query.order("id").execute()
        
        # Remove created_at and is_active from each item
        filtered_data = [
            {k: v for k, v in item.items() if k not in ["created_at", "is_active"]}
            for item in response.data
        ]
        
        return {
            "success": True,
            "data": filtered_data,
            "count": len(filtered_data)
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
