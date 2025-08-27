import secrets
from fastapi import HTTPException
from db.api_key_db import (
    get_api_key_list, insert_api_key, update_api_key_comment,
    regenerate_api_key, delete_api_key, is_api_key_existing_id,
)
from db.user_db import get_user_info
from db.usage_log_db import log_api_usage


def get_api_key_list_service(page, per_page, user_id, comment, login_id, request):
    result = get_api_key_list(page, per_page, user_id=user_id, comment=comment)

    res = {"items": result["items"], "total_pages": result["total_pages"], "total_count": result["total_count"]}

    log_api_usage(login_id, "/apim/api-key", "GET", dict(request.query_params), res, 200)

    return res

def generate_api_key_service(data: dict, login_id: str):
    user_id = data.user_id
    comment = data.comment

    if not user_id:
        raise HTTPException(400, "유저ID는 필수 정보입니다.")

    user_info = get_user_info(login_id) ## 등록을 진행하는 사람 정보
    if not user_info:
        raise HTTPException(403, "유저 정보를 확인할 수 없습니다.")

    if login_id != user_id and user_info["permission_code"] != "admin":
        raise HTTPException(403, "다른 사용자에 대한 API Key 발급은 관리자만 가능합니다.")

    if is_api_key_existing_id(user_id):
        raise HTTPException(400, f"이미 API Key가 발급된 ID입니다: {user_id}")

    api_key = f"ets-{secrets.token_hex(16)}"
    insert_api_key(user_id, api_key, comment, login_id)

    res = {
        "user_id": user_id,
        "comment": comment,
        "api_key": api_key,
        "message": "API Key 발급에 성공하였습니다."
    }

    log_api_usage(login_id, "/apim/api-key", "POST", data, res, 200)

    return res

def update_api_key_service(user_id: str, comment: str, login_id: str):
    if not is_api_key_existing_id(user_id):
        raise HTTPException(400, f"USER_ID({user_id})는 존재하지 않습니다.")
    
    update_api_key_comment(user_id, comment, login_id)

    res = {"user_id": user_id, "new_comment": comment, "message": "API Key 정보 수정을 완료하였습니다."}

    log_api_usage(login_id, "/apim/api-key/{user_id}", "PUT", {"comment": comment}, res, 200)

    return res

def regenerate_api_key_service(user_id: str, login_id: str):
    if not is_api_key_existing_id(user_id):
        raise HTTPException(400, f"USER_ID({user_id})는 존재하지 않습니다.")
    
    new_key, comment = regenerate_api_key(user_id, login_id)

    res = {
        "user_id": user_id,
        "comment": comment,
        "new_api_key": new_key,
        "message": "API Key 재발급을 완료했습니다."
    }

    log_api_usage(login_id, "/apim/api-key/{user_id}/regenerate", "PUT", {"user_id": user_id}, res, 200)
    return res

def delete_api_key_service(user_id: str, login_id: str):
    if not is_api_key_existing_id(user_id):
        raise HTTPException(400, f"USER_ID({user_id})는 존재하지 않습니다.")
    
    delete_api_key(user_id)

    res = {"message": "API Key 삭제를 완료하였습니다."}

    log_api_usage(login_id, "/apim/api-key/{user_id}", "DELETE", {"user_id": user_id}, res, 200)

    return res
