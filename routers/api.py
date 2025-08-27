from fastapi import APIRouter, Request, Depends, Query
from typing import Optional
from schemas.api_schema import ApiCreateRequest, ApiUpdateRequest
from services.api_service import *
from services.auth_service import verify_authentication

router = APIRouter()

@router.post("/apim/api")
async def create_api_router(payload: ApiCreateRequest, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return create_api_service(payload, login_id)

@router.put("/apim/api/{api_id}")
async def update_api_router(api_id: str, payload: ApiUpdateRequest, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return update_api_service(api_id, payload, login_id)

@router.delete("/apim/api/{api_id}")
async def delete_api_route(api_id: str, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return delete_api_service(api_id, login_id)

@router.get("/apim/api")
async def get_api_list_router(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10),
    api_name: Optional[str] = None,
    path: Optional[str] = None,
    use_yn: Optional[str] = None,
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return get_api_list_service(page, per_page, api_name, path, use_yn, login_id)
