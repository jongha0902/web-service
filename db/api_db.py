from utils.db_config import get_conn, DatabaseError
import math

# ✅ API 존재 여부 확인
def is_existing_api_id(api_id: str, method: str) -> bool:
    print(method)
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM api_list WHERE api_id = ? and method = ? ", (api_id, method))
            return cur.fetchone()[0] > 0
    except Exception as e:
        raise DatabaseError(f"[API 존재 확인 실패] {e}")
    
# ✅ API 등록
def insert_api_list(data: dict, login_id: str):
    try:
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO api_list (api_id, api_name, path, method, use_yn, description, flow_data, write_id, update_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data["api_id"], data["api_name"], data["path"], data["method"], data["use_yn"], data["description"], data["flow_data"], login_id, login_id))
    except Exception as e:
        raise DatabaseError(f"[API 등록 실패] {e}")

# ✅ API 수정
def update_api_info(api_id: str, method: str, data: dict, login_id: str) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.execute("""
                UPDATE api_list
                SET api_name = ?, path = ?, use_yn = ?, description = ?, flow_data = ?, update_id = ?, update_date = CURRENT_TIMESTAMP
                WHERE api_id = ?
                  and method = ?
            """, (data["api_name"], data["path"], data["use_yn"], data["description"], data["flow_data"], login_id, api_id, method))
            return cur.rowcount > 0
    except Exception as e:
        raise DatabaseError(f"[API 수정 실패] {e}")

# ✅ API 삭제
def delete_api_info(api_id, method) -> bool:
    try:
        with get_conn() as conn:
            # API 삭제
            cur = conn.execute("DELETE FROM api_list WHERE api_id = ? and method = ?", (api_id, method))
            if cur.rowcount == 0:
                raise ValueError(f"삭제하신 API({api_id + '-' + method})는 존재하지 않습니다.")
            # 권한 삭제
            conn.execute("DELETE FROM api_permissions WHERE api_id = ? and method = ?", (api_id, method))

            return cur.rowcount > 0
    except Exception as e:
        raise DatabaseError(f"[API 삭제 실패] {e}")

# ✅ API 목록 조회
def get_api_list_info(page: int = 1, per_page: int = 10, api_name: str = None, path: str = None, use_yn: str = None):
    try:
        filters = []
        params = []
        if api_name:
            filters.append("api_name LIKE ?")
            params.append(f"%{api_name}%")
        if path:
            filters.append("path LIKE ?")
            params.append(f"%{path}%")
        if use_yn:
            filters.append("use_yn = ?")
            params.append(use_yn)

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        with get_conn() as conn:
            cursor = conn.cursor()

            # 총 개수 조회
            count_query = f"SELECT COUNT(*) FROM api_list {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]

            # 전체 조회 여부 판단
            if per_page == -1:
                query = f"""
                    SELECT api_id, api_name, path, method, use_yn, description, flow_data,
                           write_id, write_date, update_id, update_date
                    FROM api_list
                    {where_clause}
                    ORDER BY write_date DESC
                """
                cursor.execute(query, params)
                items = [dict(row) for row in cursor.fetchall()]
                return {
                    "items": items,
                    "total_count": total_count,
                    "total_pages": 1,
                    "page": 1,
                    "per_page": -1
                }

            # 페이징 처리
            offset = (page - 1) * per_page
            query = f"""
                SELECT api_id, api_name, path, method, use_yn, description, flow_data,
                       write_id, write_date, update_id, update_date
                FROM api_list
                {where_clause}
                ORDER BY write_date DESC
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, params + [per_page, offset])
            items = [dict(row) for row in cursor.fetchall()]

            total_pages = math.ceil(total_count / per_page)
            return {
                "items": items,
                "total_count": total_count,
                "total_pages": total_pages,
                "page": page,
                "per_page": per_page
            }

    except Exception as e:
        raise DatabaseError(f"[API 목록 조회 실패] {e}")
