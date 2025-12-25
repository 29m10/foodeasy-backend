# app/services/cook_service.py

from app.services.supabase_client import get_supabase_admin
from typing import Dict, Any, List


class CookService:
    """
    Service class for managing cook information.
    """
    
    def __init__(self):
        self.supabase = get_supabase_admin()
    
    async def add_cook(self, user_id: str, cook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new cook for a user.
        
        Args:
            user_id: UUID of the user
            cook_data: Dictionary containing cook details
            
        Returns:
            dict: Created cook data
            
        Raises:
            ValueError: If cook with same phone already exists for this user
        """
        try:
            # Check if cook with same phone already exists for this user
            existing = self.supabase.table('cooks') \
                .select('*') \
                .eq('user_id', user_id) \
                .eq('phone_number', cook_data['phone_number']) \
                .execute()
            
            if existing.data and len(existing.data) > 0:
                raise ValueError("Cook with this phone number already exists")
            
            # Insert new cook
            new_cook = {
                'user_id': user_id,
                'name': cook_data['name'],
                'phone_number': cook_data['phone_number'],
                'languages_known': cook_data.get('languages_known', []),
                'has_smart_phone': cook_data.get('has_smart_phone', False)
            }
            
            result = self.supabase.table('cooks') \
                .insert(new_cook) \
                .execute()
            
            print(f"Cook added for user {user_id}: {result.data[0]['id']}")
            return result.data[0]
            
        except Exception as e:
            print(f"Error adding cook: {str(e)}")
            raise
    
    async def get_user_cooks(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all cooks for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            list: List of cooks
        """
        try:
            result = self.supabase.table('cooks') \
                .select('*') \
                .eq('user_id', user_id) \
                .order('created_at', desc=True) \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting cooks: {str(e)}")
            raise
    
    async def get_cook_by_id(self, cook_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get a specific cook by ID (only if it belongs to the user).
        
        Args:
            cook_id: UUID of the cook
            user_id: UUID of the user (for authorization)
            
        Returns:
            dict: Cook data
            
        Raises:
            ValueError: If cook not found or doesn't belong to user
        """
        try:
            result = self.supabase.table('cooks') \
                .select('*') \
                .eq('id', cook_id) \
                .eq('user_id', user_id) \
                .execute()
            
            if not result.data or len(result.data) == 0:
                raise ValueError("Cook not found")
            
            return result.data[0]
            
        except Exception as e:
            print(f"Error getting cook: {str(e)}")
            raise
    
    async def update_cook(self, cook_id: str, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update cook information.
        
        Args:
            cook_id: UUID of the cook
            user_id: UUID of the user (for authorization)
            update_data: Dictionary of fields to update
            
        Returns:
            dict: Updated cook data
            
        Raises:
            ValueError: If cook not found or doesn't belong to user
        """
        try:
            # Verify cook belongs to user
            await self.get_cook_by_id(cook_id, user_id)
            
            # Protected fields
            protected_fields = ['id', 'user_id', 'created_at', 'updated_at']
            clean_data = {k: v for k, v in update_data.items() if k not in protected_fields}
            
            if not clean_data:
                raise ValueError("No valid fields to update")
            
            result = self.supabase.table('cooks') \
                .update(clean_data) \
                .eq('id', cook_id) \
                .eq('user_id', user_id) \
                .execute()
            
            if not result.data or len(result.data) == 0:
                raise ValueError("Cook not found")
            
            print(f"Cook updated: {cook_id}")
            return result.data[0]
            
        except Exception as e:
            print(f"Error updating cook: {str(e)}")
            raise
    
    async def delete_cook(self, cook_id: str, user_id: str) -> Dict[str, Any]:
        """
        Delete a cook.
        
        Args:
            cook_id: UUID of the cook
            user_id: UUID of the user (for authorization)
            
        Returns:
            dict: Success message
            
        Raises:
            ValueError: If cook not found or doesn't belong to user
        """
        try:
            # Verify cook belongs to user
            await self.get_cook_by_id(cook_id, user_id)
            
            result = self.supabase.table('cooks') \
                .delete() \
                .eq('id', cook_id) \
                .eq('user_id', user_id) \
                .execute()
            
            print(f"Cook deleted: {cook_id}")
            return {"message": "Cook deleted successfully"}
            
        except Exception as e:
            print(f"Error deleting cook: {str(e)}")
            raise


# Create singleton instance
cook_service = CookService()