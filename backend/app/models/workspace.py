from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

class WorkspaceBase(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: str
    department: str

    model_config = ConfigDict(populate_by_name=True)

class WorkspaceInDB(WorkspaceBase):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WorkspaceResponse(WorkspaceBase):
    pass
