from pydantic import BaseModel

class ApiCreateRequest(BaseModel):
    api_id: str
    api_name: str
    path: str
    method: str
    use_yn: str
    description: str
    flow_data: str

class ApiUpdateRequest(BaseModel):
    api_name: str
    path: str
    method: str
    use_yn: str
    description: str
    flow_data: str
