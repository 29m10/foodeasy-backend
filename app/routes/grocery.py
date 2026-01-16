"""
Grocery Routes

Routes for fetching grocery items required for a user's meal plan.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.services.supabase_client import get_supabase_admin
from app.dependencies.auth import verify_user_access
from typing import Dict, Any
from collections import defaultdict

router = APIRouter(prefix="/grocery", tags=["Grocery"])


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Get grocery items for user's recent meal plan",
    description="""
    Get all grocery items with their types required for a user's most recent meal plan.
    
    This endpoint:
    1. Fetches the user's most recent meal plan (based on user_id and the highest meal plan id)
    2. Gets all meal items from that meal plan
    3. Fetches all grocery items required for those meal items
    4. Groups groceries by their types
    
    **Authentication Required:** Bearer token in Authorization header.
    
    **Response Structure:**
    ```json
    {
      "success": true,
      "data": {
        "meal_plan_id": 1,
        "start_date": "2024-01-15",
        "end_date": "2024-01-21",
        "grocery_items_by_type": {
          "Grains": [
            {
              "id": 1,
              "name": "Rice",
              "type": "Grains",
              "type_id": 1,
              "quantity": "2 kg",
              "meal_items": [1, 2, 3]
            }
          ]
        }
      }
    }
    ```
    
    If no meal plan exists for the user, returns an empty list.
    """
)
async def get_user_groceries(
    user_id: str = Depends(verify_user_access)
) -> Dict[str, Any]:
    """
    Get all grocery items with their types required for a user's most recent meal plan.
    
    Returns:
        Dict containing success status, meal plan info, and grocery items grouped by type.
    """
    supabase = get_supabase_admin()
    
    try:
        # Get the most recent meal plan for the user
        # Order by id DESC (assuming id is auto-incrementing) or created_at DESC
        meal_plan_response = supabase.table("user_meal_plan") \
            .select("id, start_date, end_date, created_at") \
            .eq("user_id", user_id) \
            .eq("is_active", True) \
            .order("id", desc=True) \
            .limit(1) \
            .execute()
        
        if not meal_plan_response.data or len(meal_plan_response.data) == 0:
            return {
                "success": True,
                "data": {
                    "meal_plan_id": None,
                    "start_date": None,
                    "end_date": None,
                    "grocery_items_by_type": {}
                },
                "message": "No active meal plan found for this user"
            }
        
        meal_plan = meal_plan_response.data[0]
        meal_plan_id = meal_plan["id"]
        
        # Get all meal items from the meal plan details
        meal_plan_details_response = supabase.table("user_meal_plan_details") \
            .select("meal_item_id") \
            .eq("user_meal_plan_id", meal_plan_id) \
            .eq("is_active", True) \
            .execute()
        
        if not meal_plan_details_response.data:
            return {
                "success": True,
                "data": {
                    "meal_plan_id": meal_plan_id,
                    "start_date": meal_plan.get("start_date"),
                    "end_date": meal_plan.get("end_date"),
                    "grocery_items_by_type": {}
                },
                "message": "No meal items found in the meal plan"
            }
        
        # Extract unique meal item IDs
        meal_item_ids = list(set([
            detail["meal_item_id"] for detail in meal_plan_details_response.data
        ]))
        
        # If no meal item IDs, return empty result
        if not meal_item_ids:
            return {
                "success": True,
                "data": {
                    "meal_plan_id": meal_plan_id,
                    "start_date": meal_plan.get("start_date"),
                    "end_date": meal_plan.get("end_date"),
                    "grocery_items_by_type": {}
                },
                "message": "No meal items found in the meal plan"
            }
        
        # Fetch grocery items for these meal items
        # Try different possible schema patterns:
        # 1. Junction table: meal_item_groceries (meal_item_id, grocery_item_id)
        # 2. Direct foreign key: grocery_items.meal_item_id
        # 3. JSONB array in meal_items
        
        grocery_items = []
        
        # Try pattern 1: Junction table meal_item_groceries
        try:
            junction_response = supabase.table("meal_item_groceries") \
                .select("""
                    grocery_item_id,
                    meal_item_id,
                    grocery_items (
                        id,
                        name,
                        grocery_type_id,
                        quantity,
                        grocery_types (
                            id,
                            name
                        )
                    )
                """) \
                .in_("meal_item_id", meal_item_ids) \
                .execute()
            
            if junction_response.data:
                # Process junction table results
                grocery_item_map = {}
                for junction in junction_response.data:
                    grocery_item_data = junction.get("grocery_items")
                    if not grocery_item_data:
                        continue
                    
                    grocery_id = grocery_item_data.get("id")
                    meal_item_id = junction.get("meal_item_id")
                    
                    if grocery_id not in grocery_item_map:
                        grocery_type_data = grocery_item_data.get("grocery_types")
                        grocery_item_map[grocery_id] = {
                            "id": grocery_id,
                            "name": grocery_item_data.get("name"),
                            "type": grocery_type_data.get("name") if grocery_type_data else None,
                            "type_id": grocery_item_data.get("grocery_type_id"),
                            "quantity": grocery_item_data.get("quantity"),
                            "meal_items": []
                        }
                    
                    grocery_item_map[grocery_id]["meal_items"].append(meal_item_id)
                
                grocery_items = list(grocery_item_map.values())
        
        except Exception as e:
            # Junction table might not exist, try pattern 2
            print(f"Junction table pattern failed: {e}")
            
            # Try pattern 2: Direct foreign key in grocery_items
            try:
                direct_response = supabase.table("grocery_items") \
                    .select("""
                        id,
                        name,
                        grocery_type_id,
                        quantity,
                        meal_item_id,
                        grocery_types (
                            id,
                            name
                        )
                    """) \
                    .in_("meal_item_id", meal_item_ids) \
                    .execute()
                
                if direct_response.data:
                    grocery_item_map = {}
                    for item in direct_response.data:
                        grocery_id = item.get("id")
                        meal_item_id = item.get("meal_item_id")
                        
                        if grocery_id not in grocery_item_map:
                            grocery_type_data = item.get("grocery_types")
                            grocery_item_map[grocery_id] = {
                                "id": grocery_id,
                                "name": item.get("name"),
                                "type": grocery_type_data.get("name") if grocery_type_data else None,
                                "type_id": item.get("grocery_type_id"),
                                "quantity": item.get("quantity"),
                                "meal_items": []
                            }
                        
                        if meal_item_id:
                            grocery_item_map[grocery_id]["meal_items"].append(meal_item_id)
                    
                    grocery_items = list(grocery_item_map.values())
            
            except Exception as e2:
                # Try pattern 3: Check if groceries are stored in meal_items as JSONB
                print(f"Direct foreign key pattern failed: {e2}")
                
                # Fetch meal items and check for grocery data
                meal_items_response = supabase.table("meal_items") \
                    .select("id, groceries, grocery_items") \
                    .in_("id", meal_item_ids) \
                    .execute()
                
                if meal_items_response.data:
                    grocery_item_map = {}
                    for meal_item in meal_items_response.data:
                        meal_item_id = meal_item.get("id")
                        # Check for groceries or grocery_items field (could be JSONB)
                        groceries_data = meal_item.get("groceries") or meal_item.get("grocery_items")
                        
                        if groceries_data:
                            if isinstance(groceries_data, list):
                                for grocery in groceries_data:
                                    if isinstance(grocery, dict):
                                        grocery_id = grocery.get("id") or grocery.get("grocery_item_id")
                                        if grocery_id:
                                            if grocery_id not in grocery_item_map:
                                                grocery_item_map[grocery_id] = {
                                                    "id": grocery_id,
                                                    "name": grocery.get("name"),
                                                    "type": grocery.get("type") or grocery.get("grocery_type"),
                                                    "type_id": grocery.get("type_id") or grocery.get("grocery_type_id"),
                                                    "quantity": grocery.get("quantity"),
                                                    "meal_items": []
                                                }
                                            grocery_item_map[grocery_id]["meal_items"].append(meal_item_id)
                    
                    grocery_items = list(grocery_item_map.values())
        
        # Group groceries by type
        grocery_items_by_type = defaultdict(list)
        for grocery in grocery_items:
            type_name = grocery.get("type") or "Uncategorized"
            grocery_items_by_type[type_name].append(grocery)
        
        # Convert defaultdict to regular dict for JSON serialization
        grocery_items_by_type = dict(grocery_items_by_type)
        
        return {
            "success": True,
            "data": {
                "meal_plan_id": meal_plan_id,
                "start_date": meal_plan.get("start_date"),
                "end_date": meal_plan.get("end_date"),
                "grocery_items_by_type": grocery_items_by_type
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error in production (you might want to add logging here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grocery items: {str(e)}"
        )
