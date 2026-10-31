from typing import Optional
from fastapi import Header, HTTPException, status, Depends
from backend.app.core.database import get_database
from backend.app.core.security import decode_access_token
from backend.app.models.user import UserInDB

async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
) -> UserInDB:
    db = get_database()
    user_id = None

    # Check for direct demo header
    if x_user_id:
        user_id = x_user_id
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            user_id = payload["sub"]

    if not user_id:
        # Default fallback to Alice for initial page load if no header is passed yet
        user_id = "usr_alice"

    user_dict = await db.users.find_one({"_id": user_id})
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User '{user_id}' not found or session expired."
        )

    return UserInDB(**user_dict)

async def verify_workspace_access(
    workspace_id: str,
    current_user: UserInDB = Depends(get_current_user)
) -> str:
    if workspace_id not in current_user.accessible_workspaces:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access to workspace '{workspace_id}' is forbidden for user '{current_user.id}'."
        )
    return workspace_id
