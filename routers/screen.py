from fastapi import APIRouter, Request, Depends, Query
from typing import Optional
from schemas.screen_schema import *
from services.screen_service import *
from services.auth_service import verify_authentication

router = APIRouter()

@router.get("/apim/screens")
async def get_screen_list_router(
    request: Request,
    screen_name: str = Query(None),
    screen_path: str = Query(None),
    use_yn: Optional[str] = Query(None, pattern="^(Y|N)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1),
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return get_screen_list_service(screen_name, screen_path, use_yn, page, per_page, login_id)

@router.post("/apim/screens")
async def create_screen_router(payload: ScreenCreateRequest, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return create_screen_service(payload, login_id)

@router.put("/apim/screens/{screen_code}")
async def update_screen_router(screen_code: str, payload: ScreenUpdateRequest, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return update_screen_service(screen_code, payload, login_id)

@router.delete("/apim/screens/{screen_code}")
async def delete_screen_router(screen_code: str, request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return delete_screen_service(screen_code, login_id)

@router.get("/apim/screens/menu-order")
async def get_screen_ordered_list_router(request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return get_screen_ordered_list_service(login_id)

@router.post("/apim/screens/menu-order")
async def update_screen_menu_order_router(
    payload: ScreenOrderUpdateRequest,
    request: Request,
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return update_screen_menu_order_service(payload.orders, login_id)

@router.get("/apim/screens-with-permissions")
async def get_screens_with_permissions_router(
    request: Request,
    permission_code: str = Query(..., description="권한 타입 ID"),
    search: Optional[str] = Query(None, description="화면 이름 또는 경로 검색어"),
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return get_screens_with_permissions_service(permission_code, search, login_id)

@router.post("/apim/screens-with-permissions")
async def save_screen_permissions_router(
    payload: ScreenPermissionSaveRequest,
    request: Request,
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return save_screen_permissions_service(payload.permission_code, payload.screen_codes, login_id)

@router.get("/apim/screens-with-permissions/{user_id}")
async def get_screens_with_permissions_by_user_router(user_id: str, _: str = Depends(verify_authentication)):
    return get_screens_with_permissions_by_user_service(user_id)
