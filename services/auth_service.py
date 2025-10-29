import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException, Cookie, Header
from utils.config import Config
from db.auth_db import get_refresh_token
from db.user_db import get_user_info, is_active_user_id
from db.api_permission_db import has_user_api_permission
from db.api_key_db import get_user_id_by_api_key
from db.screen_db import get_screen_code_by_path, get_screen_codes_by_permission_code

JWT_SECRET = Config.JWT_SECRET
JWT_ALGORITHM = Config.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = Config.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = Config.REFRESH_TOKEN_EXPIRE_DAYS
TOKEN_REFRESH_THRESHOLD_SECONDS = Config.TOKEN_REFRESH_THRESHOLD_SECONDS #액세스 토큰 리프레쉬 시간 10분 이하로 남으면 리프레쉬

    
# ✅ Access Token 생성
def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    kst_time = expire.astimezone(timezone(timedelta(hours=9)))
    print(f"[Access Token 만료 시간 (KST)] {kst_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[Access Token] {token}")
    return token

# ✅ Refresh Token 생성
def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    kst_time = expire.astimezone(timezone(timedelta(hours=9)))
    print(f"[Refresh Token 만료 시간 (KST)] {kst_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[Refresh Token] {token}")
    return token

# ✅ Refresh Token 검증 후 사용자 ID 반환
def decode_refresh_token(refresh_token: str = Cookie(None)) -> str:
    if not refresh_token:
        raise HTTPException(status_code=440, detail="Refresh 토큰이 없습니다.")
    try:
        payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=440, detail="유효하지 않은 토큰 유형입니다.")
        return payload["sub"]
    except ExpiredSignatureError:
        raise HTTPException(status_code=440, detail="Refresh 토큰이 만료되었습니다.")
    except InvalidTokenError:
        raise HTTPException(status_code=440, detail="유효하지 않은 Refresh 토큰입니다.")

async def verify_authentication(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    access_token: Optional[str] = Cookie(default=None),
    refresh_token: Optional[str] = Cookie(default=None),
) -> str:
    method = request.method
    path = request.scope["route"].path
    user_id = None

    # ✅ API Key 인증 우선
    # if authorization and authorization.startswith("ApiKey "):
    #     api_key = authorization.replace("ApiKey ", "")
    #     user_id = get_user_id_by_api_key(api_key)
    #     if not user_id:
    #         raise HTTPException(status_code=401, detail="유효하지 않은 API 키입니다.")
    #     if not is_active_user_id(user_id):
    #         raise HTTPException(status_code=403, detail="비활성화된 계정입니다. 관리자에게 문의해주세요.")
    #     request.state.user_id = user_id

    # else:
    
    if not access_token and not refresh_token:
        raise HTTPException(status_code=440, detail="⛔ 로그인 후 접근 가능한 페이지입니다.") 
    # ✅ access_token 파싱
    token = access_token
    if not token:
        raise HTTPException(status_code=419, detail="세션이 만료되었습니다. 다시 로그인 해주세요.")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        exp_timestamp = payload.get("exp")

        if not user_id or not exp_timestamp:
            raise HTTPException(status_code=419, detail="세션이 만료되었습니다. 다시 로그인 해주세요.")
        if not is_active_user_id(user_id):
            raise HTTPException(status_code=403, detail="비활성화된 계정입니다. 관리자에게 문의해주세요.")

        db_refresh_token = get_refresh_token(user_id)

        # ✅ refresh token 아예 없음 (로그인 정보 초기화됨)
        if not db_refresh_token:
            raise HTTPException(status_code=440, detail="세션이 만료되었습니다. 다시 로그인 해주세요.")

        if not refresh_token:
            raise HTTPException(status_code=440, detail="세션이 만료되었습니다. 다시 로그인 해주세요.")

        if db_refresh_token != refresh_token:
            raise HTTPException(status_code=440, detail="다른 기기에서 로그인되어 현재 세션이 만료되었습니다.")

        request.state.user_id = user_id

        now = datetime.now(timezone.utc).timestamp()
        if exp_timestamp - now < TOKEN_REFRESH_THRESHOLD_SECONDS:
            new_token = jwt.encode({
                "sub": user_id,
                "exp": int(now + 60 * ACCESS_TOKEN_EXPIRE_MINUTES)
            }, JWT_SECRET, algorithm=JWT_ALGORITHM)
            request.state.new_access_token = new_token

    except ExpiredSignatureError:
        raise HTTPException(status_code=419, detail="세션이 만료되었습니다. 다시 로그인 해주세요.")
    except InvalidTokenError:
        raise HTTPException(status_code=419, detail="세션이 만료되었습니다. 다시 로그인 해주세요.")

    # ✅ 공통 권한 검사
    # user_info = get_user_info(user_id)
    # if not user_info:
    #     raise HTTPException(status_code=403, detail="유저 정보를 확인할 수 없습니다.")
    # if user_info.get("permission_code") != "admin":
    #     if not has_user_api_permission(user_id, method.upper(), path):
    #         raise HTTPException(status_code=403, detail="해당 API에 접근 권한이 없습니다.")

    # ✅ 화면 접근 권한 검사
    #await verify_screen_access(request)
    return user_id


def try_verify_authentication(
    access_token: str = Cookie(default=None),
    authorization: str = Header(default=None)
) -> Optional[str]:
    token = access_token

    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload.get("sub")
        except Exception:
            return None
    return None

async def verify_screen_access(request: Request):
    screen_path = request.query_params.get("screen_path")
    
    print(screen_path)
    # POST/PUT/PATCH일 경우 body에서 추출
    if not screen_path and request.method in ("POST", "PUT", "PATCH"):
        try:
            body = await request.json()
            screen_path = body.get("screen_path")
        except:
            screen_path = None

    if not screen_path:
        raise HTTPException(400, detail="screen_path가 요청에 포함되어야 합니다.")
    
    if screen_path == '/' or not screen_path:
        return  # 권한 검사 하지 않음

    # DB에서 screen_code 조회
    screen_code = get_screen_code_by_path(screen_path)
    if not screen_code:
        raise HTTPException(404, detail=f"해당 경로에 대한 화면이 존재하지 않습니다: {screen_path}")

    user_id = request.state.user_id
    permission_code = get_user_info(user_id).get("permission_code")
    allowed_screen_codes = get_screen_codes_by_permission_code(permission_code)

    if screen_code not in allowed_screen_codes:
        raise HTTPException(403, detail="해당 화면에 접근할 수 있는 권한이 없습니다.")