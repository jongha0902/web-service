import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from utils.config import Config
from contextlib import asynccontextmanager
from utils.init_sync import ( sync_api_on_startup )
from utils.exception_handler import (
    handle_http_exception,
    handle_validation_error,
    handle_type_error,
    handle_unexpected_exception,
    handle_database_error
)
from utils.db_config import init_db, DatabaseError
from routers import overview, auth, user, screen, api, api_key, api_permission, usage_log, user_permission_type, gateway_log
ACCESS_TOKEN_EXPIRE_MINUTES = Config.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = Config.REFRESH_TOKEN_EXPIRE_DAYS

# 🔧 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ lifespan 이벤트 설정 (앱 수명 주기 동안 초기화 및 정리 작업 수행)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ 앱 실행 전에 수행할 초기화 작업
    logger.info("🚀 앱 시작: DB 설정중...")
    await init_db()                 # DB 테이블 생성 (없으면)
    #await sync_api_on_startup(app)

    yield  # 👈 여기서 FastAPI 앱이 실행됩니다 (요청 수신 가능 상태로 진입)

    # 🛑 앱 종료 직전에 실행할 정리 작업 (옵션)
    logger.info("🛑 앱 종료")

app = FastAPI(
    title="Web Service API",
    version="1.0.0",
    description="API Gateway에서 프록시되는 실제 웹 서비스 API",
    lifespan=lifespan
)

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 보안상 실제 운영 시 도메인 지정 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 예외 핸들러 등록
app.add_exception_handler(HTTPException, handle_http_exception)
app.add_exception_handler(RequestValidationError, handle_validation_error)
app.add_exception_handler(TypeError, handle_type_error)
app.add_exception_handler(Exception, handle_unexpected_exception)
app.add_exception_handler(DatabaseError, handle_database_error)

# ✅ 라우터 등록
app.include_router(overview.router, prefix="")
app.include_router(auth.router, prefix="")
app.include_router(user.router, prefix="")
app.include_router(screen.router, prefix="")
app.include_router(api.router, prefix="")
app.include_router(api_key.router, prefix="")
app.include_router(api_permission.router, prefix="")
app.include_router(usage_log.router, prefix="")
app.include_router(user_permission_type.router, prefix="")
app.include_router(gateway_log.router, prefix="")

@app.middleware("http")
async def set_sliding_token_cookie(request: Request, call_next):
    response = await call_next(request)

    if hasattr(request.state, "new_access_token"):
        response.set_cookie(
            key="access_token",
            value=request.state.new_access_token,
            httponly=True,
            secure=True,  # 운영 환경에서 반드시 True
            samesite="Lax",
            max_age=60 * ACCESS_TOKEN_EXPIRE_MINUTES,
            path="/"
        )

    if hasattr(request.state, "new_refresh_token"):
        response.set_cookie(
            key="refresh_token",
            value=request.state.new_refresh_token,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,  # 예: 7일
            path="/"
        )

    return response

@app.middleware("http")
async def block_direct_browser_access(request: Request, call_next):
    if request.url.path.startswith("/apim"):
        ua = request.headers.get("user-agent", "")
        accept = request.headers.get("accept", "")
        xrw = request.headers.get("x-requested-with", "")

        # 조건: 주소창 직접 입력으로 보이는 경우
        if (
            not xrw == "XMLHttpRequest" and
            "text/html" in accept and
            "Mozilla" in ua
        ):
            return JSONResponse(
                status_code=403,
                content={"detail": "❌ 주소창 직접 접근이 차단되었습니다."}
            )

    return await call_next(request)