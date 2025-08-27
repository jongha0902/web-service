from fastapi import APIRouter, Request, Depends
from schemas.user_schema import UserCreateRequest, UserUpdateRequest, PasswordChangeRequest
from services.user_service import *
from services.auth_service import verify_authentication

router = APIRouter()

@router.get("/apim/user")
async def get_user_list_router(request: Request, page: int = 1, per_page: int = 15,
                    user_id: str = None, user_name: str = None, use_yn: str = None,
                    _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return get_user_list_service(page, per_page, user_id, user_name, use_yn, login_id)

@router.post("/apim/user")
async def create_user_router(request: Request, payload: UserCreateRequest, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return create_user_service(payload, login_id)

@router.put("/apim/user/{user_id}")
async def update_user_router(user_id: str, payload: UserUpdateRequest, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return update_user_service(user_id, payload, login_id)

@router.put("/apim/user/{user_id}/password")
async def update_user_password_router(user_id: str, payload: PasswordChangeRequest, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return update_user_password_service(user_id, payload.new_password, login_id)

@router.delete("/apim/user/{user_id}")
async def delete_user_router(user_id: str, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return delete_user_service(user_id, login_id)
