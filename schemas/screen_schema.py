from pydantic import BaseModel
from typing import List

class ScreenCreateRequest(BaseModel):
    screen_code: str
    screen_name: str
    screen_path: str
    component_name: str
    use_yn: str
    description: str

class ScreenUpdateRequest(BaseModel):
    screen_name: str
    screen_path: str
    component_name: str
    use_yn: str
    description: str

class ScreenOrderItem(BaseModel):
    screen_code: str
    menu_order: int

class ScreenOrderUpdateRequest(BaseModel):
    orders: List[ScreenOrderItem]

class ScreenPermissionSaveRequest(BaseModel):
    permission_code: str
    screen_codes: list[str]    