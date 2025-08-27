from pydantic import BaseModel
from typing import Optional

class UserPermissionTypeCreate(BaseModel):
    permission_code: str
    permission_name: str
    use_yn: str
    description: Optional[str] = ''

class UserPermissionTypeUpdate(BaseModel):
    permission_name: str
    use_yn: str
    description: Optional[str] = ''
