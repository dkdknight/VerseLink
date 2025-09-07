from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from database import get_database
from models.user import User, UserUpdate, UserResponse, UserProfile
from middleware.auth import get_current_active_user

router = APIRouter()

@router.get("/me", response_model=UserProfile)
async def get_my_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user's detailed profile"""
    return UserProfile(**current_user.dict())

@router.patch("/me", response_model=UserProfile)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update current user's profile"""
    db = get_database()
    
    # Prepare update data
    update_data = {}
    for field, value in user_update.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
    
    if not update_data:
        return UserProfile(**current_user.dict())
    
    # Check for unique handle if updating
    if "handle" in update_data:
        existing_user = await db.users.find_one({
            "handle": update_data["handle"], 
            "id": {"$ne": current_user.id}
        })
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Handle already taken"
            )
    
    # Add updated timestamp
    update_data["updated_at"] = datetime.utcnow()
    
    # Update user
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": update_data}
    )
    
    # Get updated user
    updated_user_doc = await db.users.find_one({"id": current_user.id})
    updated_user = User(**updated_user_doc)
    
    return UserProfile(**updated_user.dict())

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(user_id: str):
    """Get public user profile"""
    db = get_database()
    
    user_doc = await db.users.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = User(**user_doc)
    return UserResponse(**user.dict())

@router.get("/", response_model=List[UserResponse])
async def search_users(
    query: str = "",
    limit: int = 20,
    skip: int = 0
):
    """Search users by handle or Discord username"""
    db = get_database()
    
    # Build search filter
    search_filter = {}
    if query:
        search_filter = {
            "$or": [
                {"handle": {"$regex": query, "$options": "i"}},
                {"discord_username": {"$regex": query, "$options": "i"}}
            ]
        }
    
    # Execute search
    cursor = db.users.find(search_filter).skip(skip).limit(limit)
    users = []
    
    async for user_doc in cursor:
        user = User(**user_doc)
        users.append(UserResponse(**user.dict()))
    
    return users