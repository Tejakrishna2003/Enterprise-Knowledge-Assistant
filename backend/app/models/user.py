from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    full_name: str
    role: str
    accessible_workspaces: List[str]

    model_config = ConfigDict(populate_by_name=True)

class UserInDB(UserBase):
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserResponse(UserBase):
    pass

class SwitchUserRequest(BaseModel):
    user_id: str
