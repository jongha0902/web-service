from utils.db_config import get_conn, DatabaseError
from typing import Optional, Dict, Any, List
import math

def _normalize_dt_param(s: Optional[str], end: bool=False) -> Optional[str]:
    """
    '2025-08-27T16:14' → '2025-08-27 16:14:00'
    end=True        → '2025-08-27 16:14:59'
    이미 'YYYY-MM-DD HH:MM:SS' 이면 그대로 리턴
    """
    if not s:
        return None
    s = s.strip().replace('T', ' ')
    # 길이에 따라 초 붙이기
    # 'YYYY-MM-DD HH:MM' (16) → 초 부착
    if len(s) == 16:
        s = f"{s}:59" if end else f"{s}:00"
    return s

def row_to_dict(cur, row):
    return {desc[0]: row[i] for i, desc in enumerate(cur.description)}

def select_gateway_logs(
    page: int,
    per_page: int,
    user_id: Optional[str],
    api_id: Optional[str],
    method: Optional[str],
    is_success: Optional[str],
    status_code: Optional[int],
    date_start: Optional[str],
    date_end: Optional[str],
) -> Dict[str, Any]:
    """
    gateway_logs 조회. 요청시간(requested_at) 기준, 최신순.
    화면에서 'YYYY-MM-DDTHH:MM'로 온 값을 여기서 정규화한다.
    """
    try:
        # 🔧 화면에서 온 파라미터 정규화
        date_start = _normalize_dt_param(date_start, end=False)  # 시작: :00
        date_end   = _normalize_dt_param(date_end,   end=True)   # 끝:   :59

        where = []
        params: List[Any] = []

        if user_id:
            where.append("user_id = ?")
            params.append(user_id)
        if api_id:
            where.append("api_id = ?")
            params.append(api_id)
        if method and method.upper() != "ALL":
            where.append("method = ?")
            params.append(method.upper())
        if is_success and is_success in ("Y", "N"):
            where.append("is_success = ?")
            params.append(is_success)
        if status_code is not None:
            where.append("status_code = ?")
            params.append(int(status_code))

        # ✅ 요청시간 기준, 초 단위 비교 (인덱스 타기 쉬움)
        if date_start and date_end:
            where.append("requested_at BETWEEN ? AND ?")
            params.extend([date_start, date_end])
        elif date_start:
            where.append("requested_at >= ?")
            params.append(date_start)
        elif date_end:
            where.append("requested_at <= ?")
            params.append(date_end)

        where_sql = "WHERE " + " AND ".join(where) if where else ""
        offset = (page - 1) * per_page

        count_sql = f"SELECT COUNT(*) AS cnt FROM gateway_logs {where_sql}"
        list_sql = f"""
            SELECT
              log_id, user_id, api_id, method, path, query_param, headers, body,
              status_code, response, requested_at, responded_at, latency_ms,
              client_ip, user_agent, is_success, error_message
            FROM gateway_logs
            {where_sql}
            ORDER BY requested_at DESC
            LIMIT ? OFFSET ?
        """

        with get_conn() as conn:
            conn.row_factory = lambda cur, row: row_to_dict(cur, row)
            cur = conn.cursor()
            cur.execute(count_sql, params)
            row = cur.fetchone()
            total_count = int(row["cnt"]) if row else 0

            cur.execute(list_sql, params + [per_page, offset])
            items = cur.fetchall() or []

        total_pages = max(1, math.ceil(total_count / per_page)) if per_page else 1

        return {"items": items, "total_count": total_count, "total_pages": total_pages}

    except Exception as e:
        raise DatabaseError(f"[Gateway 로그 조회 실패] {e}")
