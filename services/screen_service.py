from db.screen_db import *
from db.usage_log_db import log_api_usage
from fastapi import HTTPException
from schemas.screen_schema import ScreenCreateRequest, ScreenUpdateRequest, ScreenOrderItem

def get_screen_list_service(name, screen_path, use_yn, page, per_page, login_id):
    result = get_screen_list_info(name, screen_path, use_yn, page, per_page)
    log_api_usage(login_id, "/apim/screens", "GET", {"name":name, "screen_path":screen_path, "use_yn":use_yn, "page":page, "per_page":per_page}, result, 200)
    return result

def create_screen_service(data: ScreenCreateRequest, login_id: str):
    create_screen_info(data.model_dump(), login_id)
    res = {"message": "입력하신 화면 정보가 등록되었습니다."}
    log_api_usage(login_id, "/apim/screens", "POST", {data.model_dump_json}, res, 200)
    return res

def update_screen_service(screen_code: str, data: ScreenUpdateRequest, login_id: str):
    success = update_screen_info(screen_code, data.model_dump(), login_id)
    if not success:
        raise HTTPException(404, f"{screen_code} 에 해당하는 화면이 없습니다.")
    res = {"message": "선택하신 화면이 수정되었습니다."}
    log_api_usage(login_id, "/apim/screens/{screen_code}", "PUT", {"screen_code": screen_code, "data":data.model_dump_json}, res, 200)
    return res

def delete_screen_service(screen_code: str, login_id: str):
    success = delete_screen_info(screen_code)
    if not success:
        raise HTTPException(404, f"{screen_code} 에 해당하는 화면이 없습니다.")
    res = {"message": "선택하신 화면이 삭제되었습니다."}
    log_api_usage(login_id, "/apim/screens/{screen_code}", "DELETE", {"screen_code": screen_code}, res, 200)
    return res

def get_screen_ordered_list_service(login_id: str):
    result = get_screen_ordered_list_info()
    log_api_usage(login_id, "/apim/screens/order", "GET", {}, result, 200)
    return result

def update_screen_menu_order_service(order_list: list[ScreenOrderItem], login_id: str):
    update_screen_order_info(order_list)
    res = { "message": "✅ 화면 순서가 저장되었습니다." }
    log_api_usage(login_id, "/apim/screens/menu-order", "POST", [o.model_dump() for o in order_list], res, 200)
    return res

def get_screens_with_permissions_service(permission_code: str, search: Optional[str], login_id: str):
    result = get_screens_with_permissions(permission_code, search)
    log_api_usage(login_id, "/apim/screens-with-permissions", "GET", {"permission_type_id": permission_code, "search": search}, result, 200)
    return {"items": result}

def save_screen_permissions_service(permission_code: str, screen_codes: list[str], login_id: str):
    save_screen_permissions(permission_code, screen_codes)
    res = { "message": "✅ 화면 권한이 저장되었습니다." }
    log_api_usage(login_id, "/apim/screen-permissions", "POST", {"permission_code": permission_code,"screen_codes": screen_codes}, res, 200)
    return res

def get_screens_with_permissions_by_user_service(user_id: str):
    result = get_screens_with_permissions_by_user(user_id)
    log_api_usage(user_id, "/apim/screens-with-permissions/{user_id}", "POST", {"user_id": user_id}, result, 200)
    return result

