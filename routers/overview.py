from fastapi import APIRouter, Request, Depends
from services.overview_service import get_overview_stats_service
from services.auth_service import verify_authentication

router = APIRouter()

@router.get("/apim/overview/stats")
async def get_overview_stats_router(
    request: Request,
    _: str = Depends(verify_authentication)
):
    """대시보드에 필요한 모든 통계 데이터를 반환합니다."""
    login_id = request.state.user_id
    return get_overview_stats_service(login_id)