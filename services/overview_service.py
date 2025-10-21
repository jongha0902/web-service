from db.overview_db import get_overview_stats
from db.usage_log_db import log_api_usage
from fastapi import HTTPException

def get_overview_stats_service(login_id: str):
    """대시보드 통계 데이터를 조회하고 API 사용 로그를 기록합니다."""
    try:
        stats = get_overview_stats()
        log_api_usage(login_id, "/apim/overview/stats", "GET", {}, stats, 200)
        return stats
    except Exception as e:
        # DB 조회 중 발생한 예외를 처리합니다.
        raise HTTPException(status_code=500, detail=str(e))