from pydantic import BaseModel

class ApiKeyCreateRequest(BaseModel):
    user_id: str
    comment: str

class ApiKeyUpdateRequest(BaseModel):
    comment: str
