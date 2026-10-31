from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.core.database import get_database
from backend.app.core.security import create_access_token
from backend.app.models.user import UserResponse, SwitchUserRequest, UserInDB
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & Demo Users"])

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=List[UserResponse])
async def list_demo_users():
    db = get_database()
    users = await db.users.find({}).to_list(10)
    return [UserResponse(**u) for u in users]

@router.post("/switch-user")
async def switch_user(req: SwitchUserRequest):
    db = get_database()
    user_dict = await db.users.find_one({"_id": req.user_id})
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{req.user_id}' does not exist."
        )

    user = UserInDB(**user_dict)
    access_token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user_dict)
    }
