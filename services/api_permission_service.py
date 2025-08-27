from fastapi import HTTPException
from fastapi.responses import JSONResponse
from db.api_permission_db import *
from db.user_db import is_existing_user_id
from db.usage_log_db import log_api_usage

async def get_api_permissions_service(user_id, login_id):
    if not is_existing_user_id(user_id):
        raise HTTPException(400, f"선택하신 유저ID({user_id})는 존재하지 않습니다.")
    permissions = get_user_all_api_permissions(user_id)
    res = {"message": "선택하신 유저의 API 권한 조회를 성공하였습니다.", "permissionList": permissions}
    log_api_usage(login_id, "/apim/api-permissions/{user_id}", "GET", {"user_id": user_id}, res, 200)
    return JSONResponse(content=res, status_code=200)

async def save_user_api_permissions_service(user_id, data, login_id):
    api_ids = data.get("api_ids", [])
    if not is_existing_user_id(user_id):
        raise HTTPException(404, f"유저 ID({user_id})가 존재하지 않습니다.")
    if not isinstance(api_ids, list):
        raise HTTPException(400, "api_ids는 리스트 형식이어야 합니다.")
    save_update_user_api_permissions(user_id, api_ids, login_id)
    res = {"message": "유저 API 접근 권한이 저장되었습니다."}
    log_api_usage(login_id, "/apim/api-permissions/{user_id}", "POST", data, res, 200)
    return JSONResponse(content=res, status_code=200)

async def get_permission_requests_service(query_params, login_id):
    filters = dict(query_params)
    requestList = get_permission_request_list(**filters)
    res = {"requestList": requestList, "message": "권한 신청 목록 조회가 성공하였습니다."}
    log_api_usage(login_id, "/apim/api-permission-requests", "GET", {"data": filters}, res, 200)
    return JSONResponse(content=res, status_code=200)

def approve_permission_request_service(request_id, login_id):
    if not is_existing_request_id(request_id):
        raise HTTPException(400, f"요청 ID({request_id})는 존재하지 않습니다.")
    approve_permission_request(request_id, login_id)
    res = {"message": "선택하신 유저의 신청 권한 승인이 완료되었습니다."}
    log_api_usage(login_id, "/apim/api-permission-requests/{request_id}/approve", "POST", {"request_id": request_id}, res, 200)
    return JSONResponse(content=res, status_code=200)

def reject_permission_request_service(request_id, login_id):
    if not is_existing_request_id(request_id):
        raise HTTPException(400, f"요청 ID({request_id})는 존재하지 않습니다.")
    reject_permission_request(request_id, login_id)
    res = {"message": "선택하신 유저의 신청 권한 승인이 반려되었습니다."}
    log_api_usage(login_id, "/apim/api-permission-requests/{request_id}/reject", "POST", {"request_id": request_id}, res, 200)
    return JSONResponse(content=res, status_code=200)

def get_pending_permission_count_service(login_id):
    count = get_pending_permission_count()
    res = {"pendingCount": count}
    log_api_usage(login_id, "/apim/api-permission-requests/pending-count", "GET", {}, res, 200)
    return JSONResponse(content=res, status_code=200)

def request_api_permission_service(user_id, data):
    api_id = data.get("api_id")
    reason = data.get("reason", "").strip()
    if not api_id:
        raise HTTPException(400, "api_id는 필수입니다.")
    if not reason:
        raise HTTPException(400, "신청 사유는 필수입니다.")
    insert_permission_request(user_id, api_id, reason)
    res = {"message": "API 권한 신청이 완료되었습니다."}
    log_api_usage(user_id, "/apim/user/api-permission-requests/{user_id}", "POST", {"data": data, "user_id": user_id}, res, 200)
    return JSONResponse(content=res, status_code=200)
