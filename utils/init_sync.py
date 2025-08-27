from fastapi.routing import APIRoute
from typing import Set, Tuple
from utils.db_config import get_conn 
from db.api_db import insert_api_list

EXCLUDE_PATHS: Set[Tuple[str, str]] = {
    ("/", "GET"),
    ("/auth/login", "POST"),
    ("/auth/logout", "POST"),
    ("/auth/refresh", "POST")
}

async def sync_api_on_startup(app):
    try:
        current_api_set: Set[Tuple[str, str]] = set()
        api_name_map = {}

        for route in app.routes:
            if isinstance(route, APIRoute):
                for method in route.methods:
                    method_upper = method.upper()
                    path_method = (route.path, method_upper)

                    if method_upper in {"GET", "POST", "PUT", "DELETE"} and path_method not in EXCLUDE_PATHS:
                        current_api_set.add(path_method)
                        api_name_map[path_method] = route.name or route.path

        with get_conn() as conn:
            rows = conn.execute("SELECT path, method, use_yn FROM api_list").fetchall()
            db_all = {(row["path"], row["method"]): row["use_yn"] for row in rows}

        # ➕ 등록
        to_add = current_api_set - db_all.keys()
        for path, method in to_add:
            insert_api_list({
                "api_name": api_name_map.get((path, method), path),
                "path": path,
                "method": method,
                "use_yn": "Y",
                "description": "",
                "flow_data": ""
            }, "system")

        # ➖ 비활성화
        to_deactivate = [p for p, y in db_all.items() if p not in current_api_set and y == "Y"]
        for path, method in to_deactivate:
            with get_conn() as conn:
                conn.execute("""
                    UPDATE api_list
                    SET use_yn = 'N', update_id = 'system', update_date = CURRENT_TIMESTAMP
                    WHERE path = ? AND method = ?
                """, (path, method))

        print(f"[✓] API 동기화 완료 - 등록: {len(to_add)}, 비활성화: {len(to_deactivate)}")

    except Exception as e:
        print(f"[!] API 동기화 실패: {e}")
