from pydantic import BaseModel, Field
from typing import Optional

class ApiKeyCreateRequest(BaseModel):
    user_id: str
    comment: Optional[str] = Field(default=None, description="발급 사유 (옵션)")

class ApiKeyUpdateRequest(BaseModel):
    comment: str
