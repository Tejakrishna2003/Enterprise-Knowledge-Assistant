from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.core.database import get_database
from backend.app.models.workspace import WorkspaceResponse
from backend.app.models.user import UserInDB
from backend.app.api.deps import get_current_user, verify_workspace_access

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(current_user: UserInDB = Depends(get_current_user)):
    db = get_database()
    # Filter strictly by user's accessible workspaces
    workspaces = await db.workspaces.find(
        {"_id": {"$in": current_user.accessible_workspaces}}
    ).to_list(20)
    return [WorkspaceResponse(**w) for w in workspaces]

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str = Depends(verify_workspace_access)
):
    db = get_database()
    ws = await db.workspaces.find_one({"_id": workspace_id})
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace '{workspace_id}' not found."
        )
    return WorkspaceResponse(**ws)
