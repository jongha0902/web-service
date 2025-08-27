from fastapi import APIRouter, Request, Depends
from typing import Optional
from schemas.api_key_schema import ApiKeyCreateRequest, ApiKeyUpdateRequest
from services.api_key_service import *
from services.auth_service import verify_authentication

router = APIRouter()

@router.get("/apim/api-key")
async def api_key_list_router(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    user_id: Optional[str] = None,
    comment: Optional[str] = None,
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return get_api_key_list_service(page, per_page, user_id, comment, login_id, request)

@router.post("/apim/api-key")
async def create_api_key_router(payload: ApiKeyCreateRequest, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return generate_api_key_service(payload, login_id)

@router.put("/apim/api-key/{user_id}")
async def update_api_key_router(user_id: str, payload: ApiKeyUpdateRequest, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return update_api_key_service(user_id, payload.comment, login_id)

@router.put("/apim/api-key/{user_id}/regenerate")
async def regenerate_api_key_router(user_id: str, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return regenerate_api_key_service(user_id, login_id)

@router.delete("/apim/api-key/{user_id}")
async def delete_api_key_router(user_id: str, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return delete_api_key_service(user_id, login_id)
