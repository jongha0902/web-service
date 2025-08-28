from fastapi import HTTPException
from typing import Optional
from db.gateway_logs_db import select_gateway_logs
from db.usage_log_db import log_api_usage

def _validate_dt(dt: Optional[str]) -> Optional[str]:
    if not dt:
        return None
    # 기대 포맷: YYYY-MM-DDTHH:MM (프론트와 합의된 형태)
    # 형식이 다르면 그대로 DB에 넘기지 않고 400
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$", dt):
        raise HTTPException(400, "searchDateStart/End 형식은 YYYY-MM-DDTHH:MM 이어야 합니다.")
    return dt

def get_gateway_logs_service(
    page: int,
    per_page: int,
    login_id: str,
    request,
    is_admin: bool,
    user_id: Optional[str],
    api_id: Optional[str],
    method: Optional[str],
    is_success: Optional[str],
    status_code: Optional[int],
    date_start: Optional[str],
    date_end: Optional[str],
):
    date_start = _validate_dt(date_start)
    date_end = _validate_dt(date_end)

    # DB 조회
    result = select_gateway_logs(
        page=page,
        per_page=per_page,
        # 권한 반영된 user_id (관리자면 None 가능, 일반 사용자는 본인)
        user_id=user_id,
        api_id=api_id,
        method=method,
        is_success=is_success,
        status_code=status_code,
        date_start=date_start,
        date_end=date_end,
    )

    res = {
        "items": result["items"],
        "total_count": result["total_count"],
        "total_pages": result["total_pages"],
    }

    log_api_usage(login_id, "/apim/gateway-logs", "GET", dict(request.query_params), res, 200)
    return res
