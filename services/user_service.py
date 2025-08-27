from db.user_db import (
    get_user_list, insert_user, update_user_info, update_user_password,
    delete_user_overall_logic, is_existing_user_id
)
from db.usage_log_db import log_api_usage
from fastapi import HTTPException
from schemas.user_schema import UserCreateRequest, UserUpdateRequest

def get_user_list_service(page, per_page, user_id, user_name, use_yn, login_id):
    result = get_user_list(page, per_page, user_id, user_name, use_yn)
    log_api_usage(login_id, "/apim/user", "GET", {page, per_page, user_id, user_name, use_yn}, result, 200)
    return result

def create_user_service(data: UserCreateRequest, login_id: str):
    if is_existing_user_id(data.user_id):
        raise HTTPException(400, f"입력하신 유저ID({data.user_id})는 이미 존재합니다.")
    if data.password != data.passwordCheck:
        raise HTTPException(400, "비밀번호가 다릅니다.")
    insert_user({**data.model_dump(), "login_id": login_id})
    log_api_usage(login_id, "/apim/user", "POST", data, {"message": "등록을 완료하였습니다."}, 200)
    return {"message": "등록을 완료하였습니다."}

def update_user_service(user_id: str, data: UserUpdateRequest, login_id: str):
    if not is_existing_user_id(user_id):
        raise HTTPException(400, f"수정하신 유저ID({user_id})는 존재하지 않습니다.")
    update_user_info({**data.model_dump(), "user_id": user_id, "login_id": login_id})
    log_api_usage(login_id, "/apim/user/{user_id}", "PUT", data, {"message": "수정을 완료하였습니다."}, 200)
    return {"message": "수정을 완료하였습니다."}

def update_user_password_service(user_id: str, new_password: str, login_id: str):
    if not is_existing_user_id(user_id):
        raise HTTPException(400, f"변경하신 유저ID({user_id})는 존재하지 않습니다.")
    update_user_password(user_id, new_password, login_id)
    log_api_usage(login_id, "/apim/user/{user_id}/password", "PUT", {"user_id": user_id}, {"message": "비밀번호가 성공적으로 변경되었습니다."}, 200)
    return {"message": "비밀번호가 성공적으로 변경되었습니다."}

def delete_user_service(user_id: str, login_id: str):
    if not is_existing_user_id(user_id):
        raise HTTPException(400, f"삭제하신 유저ID({user_id})는 존재하지 않습니다.")
    delete_user_overall_logic(user_id)
    log_api_usage(login_id, "/apim/user/{user_id}", "DELETE", {"user_id": user_id}, {"message": "삭제 완료"}, 200)
    return {"message": "선택하신 유저를 삭제하였습니다."}
