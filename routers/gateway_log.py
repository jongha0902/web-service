from fastapi import APIRouter, Request, Depends, Query
from typing import Optional
from services.gateway_logs_service import get_gateway_logs_service
from services.auth_service import verify_authentication
from db.user_db import get_user_info

router = APIRouter()

@router.get("/apim/gateway-logs")
async def get_gateway_logs_router(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=200),
    user_id: Optional[str] = None,
    api_id: Optional[str] = None,
    method: Optional[str] = None,          # GET/POST/...
    is_success: Optional[str] = None,      # 'Y' | 'N'
    status_code: Optional[int] = None,     # 200 ...
    searchDateStart: Optional[str] = None, # 'YYYY-MM-DDTHH:MM'
    searchDateEnd: Optional[str] = None,   # 'YYYY-MM-DDTHH:MM'
    _: str = Depends(verify_authentication)  # 세션 인증
):
    login_id = request.state.user_id

    # 권한 확인 (api_key와 동일한 정책: permission_code == 'admin' 이면 관리자)
    user_info = get_user_info(login_id)
    is_admin = bool(user_info and user_info.get("permission_code") == "ADMIN")

    # 일반 유저는 자신의 로그만 강제
    effective_user_id = user_id if is_admin else login_id

    return get_gateway_logs_service(
        page=page,
        per_page=per_page,
        login_id=login_id,
        request=request,
        is_admin=is_admin,
        user_id=effective_user_id,
        api_id=api_id,
        method=method,
        is_success=is_success,
        status_code=status_code,
        date_start=searchDateStart,
        date_end=searchDateEnd,
    )
