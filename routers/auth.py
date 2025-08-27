from fastapi import APIRouter, Request, Depends, HTTPException, Cookie, Query
from typing import Optional
from fastapi.responses import JSONResponse
from schemas.auth_schema import LoginRequest
from services.auth_service import *
from db.auth_db import *
from db.user_db import get_user_info

router = APIRouter()

async def verify_authentication_optional(
    request: Request,
    # 원래 verify_authentication이 기대하는 것과 동일한 시그니처로 DI 받기
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    access_token: Optional[str] = Cookie(default=None),
    refresh_token: Optional[str] = Cookie(default=None),
) -> Optional[str]:
    """
    - verify_authentication을 직접 호출하되, FastAPI가 주입해 준 문자열/쿠키를 그대로 전달.
    - 실패(HTTPException)이면 None으로 삼켜서 silent 처리가 가능하도록 한다.
    """
    try:
        # verify_authentication이 async면 await, sync면 그대로 호출
        return await verify_authentication(
            request=request,
            authorization=authorization,
            access_token=access_token,
            refresh_token=refresh_token,
        )
    except HTTPException:
        return None
    
@router.post("/apim/auth/login")
async def login(request: Request, payload: LoginRequest):
    user = authenticate_user(payload.user_id, payload.password)
    if not user:
        raise HTTPException(401, "아이디 또는 비밀번호가 올바르지 않습니다.")

    if user["use_yn"] == "N":
            raise HTTPException(status_code=403, detail="비활성화된 계정입니다. 관리자에게 문의해주세요.")
    
    access_token = create_access_token(payload.user_id)
    refresh_token = create_refresh_token(payload.user_id)
    update_refresh_token(payload.user_id, refresh_token)

    # ✅ 쿠키는 middleware에서 처리
    request.state.new_access_token = access_token
    request.state.new_refresh_token = refresh_token

    return JSONResponse(content={"user": user})

@router.post("/apim/auth/refresh")
async def refresh(
    request: Request,
    user_id: str = Depends(decode_refresh_token),
    refresh_token: str = Cookie(None)
):
    user = get_user_info(user_id)
    if not user:
        raise HTTPException(status_code=403, detail="유저 정보를 찾을 수 없습니다.")

    stored_token = get_refresh_token(user_id)
    if refresh_token != stored_token:
        raise HTTPException(status_code=401, detail="다른 기기에서 로그인되어 세션이 무효화되었습니다.")

    access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    update_refresh_token(user_id, new_refresh_token)

    # ✅ 쿠키는 middleware에서 처리
    request.state.new_access_token = access_token
    request.state.new_refresh_token = new_refresh_token

    return JSONResponse(content={
        "message": "토큰이 갱신되었습니다.",
        "access_token_refreshed": True,
        "refresh_token_refreshed": True
    })

@router.get("/apim/auth/profile")
async def get_profile(
    silent: bool = Query(False),
    user_id: Optional[str] = Depends(verify_authentication_optional),
):
    if not user_id:
        if silent:
            return JSONResponse(status_code=200, content={"authenticated": False, "user": None})
        raise HTTPException(status_code=440, detail="⛔ 로그인 후 접근 가능한 페이지입니다.")

    user = get_user_info(user_id)
    if not user:
        if silent:
            return JSONResponse(status_code=200, content={"authenticated": False, "user": None})
        raise HTTPException(status_code=404, detail="사용자 정보를 찾을 수 없습니다.")

    return {"authenticated": True, "user": user} if silent else {"user": user}

@router.post("/apim/auth/logout")
async def logout(request: Request, user_id: str = Depends(try_verify_authentication)):
    #if user_id:
    #    clear_refresh_token(user_id)

    # ✅ 삭제는 직접 해도 됨 (middleware는 상태 기반으로만 set)
    res = JSONResponse(content={"message": "로그아웃이 완료되었습니다."})
    res.delete_cookie("access_token", path="/", samesite="Lax")
    res.delete_cookie("refresh_token", path="/", samesite="Lax")
    res.delete_cookie("last_screen_path", path="/", samesite="Lax")
    return res
