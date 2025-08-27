from db.usage_log_db import get_usage_log_list

def get_usage_log_service(page, per_page, search_start, search_end, user_id, path, method):
    search_start = search_start.replace("T", " ")
    search_end = search_end.replace("T", " ")
    result = get_usage_log_list(page, per_page, search_start, search_end, user_id, path, method)
    res = {"items": result["items"], "total_pages": result["total_pages"], "total_count": result["total_count"]}
    return res
