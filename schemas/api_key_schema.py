from pydantic import BaseModel, Field

class ApiKeyCreateRequest(BaseModel):
    user_id: str
    comment: str | None = Field(default=None, description="발급 사유 (옵션)")

class ApiKeyUpdateRequest(BaseModel):
    comment: str
