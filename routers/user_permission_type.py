from fastapi import APIRouter, Request, Depends, Query
from typing import Optional
from schemas.user_permission_type import UserPermissionTypeCreate, UserPermissionTypeUpdate
from services.user_permission_type_service import (
    get_user_permission_type_list_service,
    create_user_permission_type_service,
    update_user_permission_type_service,
    delete_user_permission_type_service,
    read_users_with_user_permission_type_service
)
from services.auth_service import verify_authentication

router = APIRouter()


@router.get("/apim/user-permission-types")
async def get_user_permission_type_list_router(
    request: Request,
    search: Optional[str] = Query(None),
    search_field: Optional[str] = Query(None),
    use_yn: Optional[str] = Query(None, pattern="^(Y|N)$"),
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return get_user_permission_type_list_service(search, search_field, use_yn, login_id)


@router.post("/apim/user-permission-types")
async def create_user_permission_type_router(
    payload: UserPermissionTypeCreate,
    request: Request,
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return create_user_permission_type_service(payload, login_id)


@router.put("/apim/user-permission-types/{permission_code}")
async def update_user_permission_type_router(
    permission_code: str,
    payload: UserPermissionTypeUpdate,
    request: Request,
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return update_user_permission_type_service(permission_code, payload, login_id)


@router.delete("/apim/user-permission-types/{permission_code}")
async def delete_user_permission_type_router(
    permission_code: str,
    request: Request,
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return delete_user_permission_type_service(permission_code, login_id)


@router.get("/apim/users-with-permission-types")
async def get_users_with_user_permission_type_router(
    request: Request,
    permission_code: str = Query(...),
    user_id: Optional[str] = Query(None),
    user_name: Optional[str] = Query(None),
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return read_users_with_user_permission_type_service(permission_code, user_id, user_name, login_id)
