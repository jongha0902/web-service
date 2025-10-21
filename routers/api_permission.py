from fastapi import APIRouter, Request, Depends
from services.api_permission_service import *
from services.auth_service import verify_authentication

router = APIRouter()

# 유저 API 권한 전체 조회
@router.get("/apim/api-permissions/{user_id}")
async def get_api_permissions_router(request: Request, user_id: str, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return await get_api_permissions_service(user_id, login_id)

# 유저 API 권한 저장
@router.post("/apim/api-permissions/{user_id}")
async def save_user_api_permissions_router(request: Request, user_id: str, _: str = Depends(verify_authentication)):
    data = await request.json()
    login_id = request.state.user_id
    return await save_user_api_permissions_service(user_id, data, login_id)

# 권한 신청 목록 조회
@router.get("/apim/api-permission-requests")
async def get_permission_requests_list_router(
    request: Request,
    user_id: str = None,
    method: str = None,
    path: str = None,
    start_date: str = None,
    end_date: str = None,
    status: str = None,
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return await get_permission_requests_service(request.query_params, login_id)

# 권한 신청 승인
@router.post("/apim/api-permission-requests/{request_id}/approve")
async def approve_request_router(request: Request, request_id: int, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return approve_permission_request_service(request_id, login_id)

# 권한 신청 반려
@router.post("/apim/api-permission-requests/{request_id}/reject")
async def reject_request_router(request: Request, request_id: int, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return reject_permission_request_service(request_id, login_id)

# 권한 신청 수
@router.get("/apim/api-permission-requests/pending-count")
async def get_pending_permission_count_router(request: Request, _: str = Depends(verify_authentication)):
    login_id = request.state.user_id
    return get_pending_permission_count_service(login_id)

# API 권한 신청
@router.post("/apim/api-permission-requests/{user_id}")
async def request_api_permission_router(request: Request, user_id: str, _: str = Depends(verify_authentication)):
    data = await request.json()
    print(data)
    return request_api_permission_service(user_id, data)
