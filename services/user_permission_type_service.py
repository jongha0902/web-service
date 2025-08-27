from db.user_permission_type import (
    get_user_permission_types,
    create_user_permission_type,
    update_user_permission_type,
    delete_user_permission_type,
    get_users_with_user_permission_type
)
from fastapi import HTTPException
from schemas.user_permission_type import UserPermissionTypeCreate, UserPermissionTypeUpdate
from db.usage_log_db import log_api_usage


def get_user_permission_type_list_service(search: str, search_field: str, use_yn: str, login_id: str):
    result = get_user_permission_types(search, search_field, use_yn)
    log_api_usage(login_id, "/apim/user-permission-types", "GET", {"search": search, "search_field": search_field, "use_yn": use_yn}, result, 200)
    return result


def create_user_permission_type_service(payload: UserPermissionTypeCreate, login_id: str):
    create_user_permission_type(payload.model_dump(), login_id)
    res = {"message": "권한이 등록되었습니다."}
    log_api_usage(login_id, "/apim/user-permission-types", "POST", {**payload.model_dump()}, res, 200)
    return res


def update_user_permission_type_service(permission_code: str, payload: UserPermissionTypeUpdate, login_id: str):
    success = update_user_permission_type(permission_code, payload.model_dump(), login_id)
    if not success:
        raise HTTPException(404, f"{permission_code} 에 해당하는 권한이 없습니다.")
    res = {"message": "권한이 수정되었습니다."}
    log_api_usage(login_id, "/apim/user-permission-types/{permission_code}", "PUT", {"permission_code": permission_code, **payload.model_dump()}, res, 200)
    return res


def delete_user_permission_type_service(permission_code: str, login_id: str):
    success = delete_user_permission_type(permission_code)
    if not success:
        raise HTTPException(404, f"{permission_code} 에 해당하는 권한이 없습니다.")
    res = {"message": "권한이 삭제되었습니다."}
    log_api_usage(login_id, "/apim/user-permission-types/{permission_code}", "DELETE", {"permission_code": permission_code}, res, 200)
    return res


def read_users_with_user_permission_type_service(permission_code: str, user_id: str, user_name: str, login_id: str):
    result = get_users_with_user_permission_type(permission_code, user_id, user_name)
    log_api_usage(login_id, "/apim/users-with-user-permission-type", "GET", {
        "permission_code": permission_code,
        "user_id": user_id,
        "user_name": user_name
    }, result, 200)
    return result
