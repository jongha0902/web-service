from utils.db_config import get_conn, DatabaseError
import json, math

# ✅ 사용 로그 목록 조회
def get_usage_log_list(page, per_page, searchDateStart, searchDateEnd, user_id=None, path=None, method=None):
    try:
        with get_conn() as conn:
            cur = conn.cursor()

            # ✅ 공통 조건 구성
            where_clauses = ["strftime('%Y-%m-%d %H:%M', request_time) BETWEEN ? AND ?"]
            params = [searchDateStart, searchDateEnd]

            if user_id:
                where_clauses.append("user_id LIKE ?")
                params.append(f"%{user_id}%")
            if path:
                where_clauses.append("path LIKE ?")
                params.append(f"%{path}%")
            if method:
                where_clauses.append("method = ?")
                params.append(method)

            where_sql = " AND ".join(where_clauses)

            # ✅ 메인 쿼리
            query = f"""
                SELECT user_id, path, method, status_code, request_data, response_data, request_time
                FROM api_usage_log
                WHERE {where_sql}
                ORDER BY request_time DESC
                LIMIT ? OFFSET ?
            """
            cur.execute(query, params + [per_page, (page - 1) * per_page])
            rows = cur.fetchall()

            # ✅ 카운트 쿼리
            count_query = f"""
                SELECT COUNT(*)
                FROM api_usage_log
                WHERE {where_sql}
            """
            cur.execute(count_query, params)
            total_count = cur.fetchone()[0]

            return {
                "items": [dict(row) for row in rows],
                "total_pages": math.ceil(total_count / per_page),
                "total_count": total_count
            }

    except Exception as e:
        raise DatabaseError(f"[로그 조회 실패] {e}")




def to_json_safe(obj):
    try:
        return json.dumps(obj, ensure_ascii=False)
    except TypeError:
        return json.dumps(str(obj), ensure_ascii=False)
    
# ✅ 사용 로그 기록
def log_api_usage(login_id, path, method, request_data, response_data, status_code):
    try:
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO api_usage_log (user_id, path, method, request_data, response_data, status_code, request_time)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            """, (
                login_id,
                path,
                method,
                to_json_safe(request_data),
                to_json_safe(response_data),
                status_code
            ))
    except Exception as e:
        raise DatabaseError(f"[로그 기록 실패] {e}")
