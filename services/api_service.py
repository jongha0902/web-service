from db.api_db import (
    insert_api_list, is_existing_api_id,
    update_api_info, delete_api_info, get_api_list_info
)
from fastapi import HTTPException
from schemas.api_schema import ApiCreateRequest, ApiUpdateRequest
from db.usage_log_db import log_api_usage

def create_api_service(data: ApiCreateRequest, login_id: str):
    if is_existing_api_id(data.api_id):
        raise HTTPException(400, f"API ID({data.api_id})가 이미 존재합니다.")
    
    insert_api_list(data.model_dump(), login_id)
    res = {"message": f"입력하신 API({data.api_name}) 정보 등록을 성공하였습니다."}
    log_api_usage(login_id, "/apim/api", "POST", data.model_dump(), res, 200)
    return res

def update_api_service(api_id: str, data: ApiUpdateRequest, login_id: str):
    if not is_existing_api_id(api_id):
        raise HTTPException(400, f"API ID({api_id})가 존재하지 않습니다.")
    update_api_info(data.model_dump(), api_id, login_id)
    res = {"message": f"입력하신 API({data.api_name}) 수정이 완료되었습니다."}
    log_api_usage(login_id, "/apim/api/{api_id}", "PUT", data.model_dump(), res, 200)
    return res

def delete_api_service(api_id: str, login_id: str):
    if not is_existing_api_id(api_id):
        raise HTTPException(400, f"삭제하신 API의 ID({api_id})가 존재하지 않습니다.")
    delete_api_info(api_id)
    res = {"message": "선택하신 API 삭제를 완료하였습니다."}
    log_api_usage(login_id, "/apim/api/{api_id}", "DELETE", {"api_id": api_id}, res, 200)
    return res

def get_api_list_service(page, per_page, api_name, path, use_yn, login_id):
    result = get_api_list_info(page, per_page, api_name, path, use_yn)
    log_api_usage(login_id, "/apim/api", "GET", {}, result, 200)
    return result
