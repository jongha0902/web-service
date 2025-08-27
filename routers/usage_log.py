from fastapi import APIRouter, Request, Depends, Query
from typing import Optional
from services.usage_log_service import get_usage_log_service
from services.auth_service import verify_authentication

router = APIRouter()

@router.get("/apim/usage-log")
async def get_usage_log_router(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1),
    user_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    searchDateStart: str = Query(..., description="시작일자 (필수)"),
    searchDateEnd: str = Query(..., description="종료일자 (필수)"),
    _: str = Depends(verify_authentication)
):
    login_id = request.state.user_id
    return get_usage_log_service(
        page, per_page, searchDateStart, searchDateEnd,
        user_id, path, method
    )

