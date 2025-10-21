from utils.db_config import get_conn, DatabaseError
from datetime import datetime, timedelta

def get_overview_stats() -> dict:
    """대시보드에 필요한 모든 통계 데이터를 한 번에 조회합니다."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()

            # 1. 총 API 수
            cur.execute("SELECT COUNT(*) FROM api_list WHERE use_yn = 'Y'")
            total_apis = cur.fetchone()[0]

            # 2. 총 발급 키 수
            cur.execute("SELECT COUNT(*) FROM api_keys")
            total_api_keys = cur.fetchone()[0]

            # 3. 총 호출 수 (gateway_logs 기준)
            cur.execute("SELECT COUNT(*) FROM gateway_logs")
            total_calls = cur.fetchone()[0]

            # 4. 오늘 호출 수 (gateway_logs 기준)
            today = datetime.now().strftime('%Y-%m-%d')
            cur.execute(
                "SELECT COUNT(*) FROM gateway_logs WHERE DATE(requested_at) = ?",
                (today,)
            )
            today_calls = cur.fetchone()[0]

            # 5. 최근 7일간의 호출 통계
            cur.execute("""
                WITH RECURSIVE date_series(date) AS (
                    SELECT DATE('now', '-6 day')
                    UNION ALL
                    SELECT DATE(date, '+1 day')
                    FROM date_series
                    WHERE date < DATE('now')
                )
                SELECT
                    ds.date,
                    COUNT(gl.log_id) as count
                FROM date_series ds
                LEFT JOIN gateway_logs gl ON DATE(gl.requested_at) = ds.date
                GROUP BY ds.date
                ORDER BY ds.date ASC
            """)
            daily_stats = [dict(row) for row in cur.fetchall()]

            # 6. 최근 7일간의 오류 통계
            cur.execute("""
                WITH RECURSIVE date_series(date) AS (
                    SELECT DATE('now', '-6 day')
                    UNION ALL
                    SELECT DATE(date, '+1 day')
                    FROM date_series
                    WHERE date < DATE('now')
                )
                SELECT
                    ds.date,
                    COUNT(gl.log_id) as count
                FROM date_series ds
                LEFT JOIN gateway_logs gl ON DATE(gl.requested_at) = ds.date AND gl.status_code >= 400
                GROUP BY ds.date
                ORDER BY ds.date ASC
            """)
            daily_errors = [dict(row) for row in cur.fetchall()]

            # 7. 많이 호출된 API TOP 5
            cur.execute("""
                SELECT
                    al.api_id,
                    al.api_name,
                    al.method,
                    COUNT(gl.log_id) as count
                FROM gateway_logs gl
                JOIN api_list al ON gl.path = al.path AND gl.method = al.method
                GROUP BY al.api_id, al.api_name, al.method
                ORDER BY count DESC
                LIMIT 5
            """)
            top_apis = [dict(row) for row in cur.fetchall()]

            # 8. API 권한 신청 대기 건수
            cur.execute("SELECT COUNT(*) FROM api_permission_requests WHERE status = 'PENDING'")
            pending_requests = cur.fetchone()[0]

            # 9. 최근 오류 발생 로그
            cur.execute("""
                SELECT 
                    gl.requested_at as time, 
                    al.api_id,
                    al.api_name,
                    al.method,
                    gl.status_code, 
                    gl.user_id
                FROM gateway_logs gl
                LEFT JOIN api_list al ON gl.api_id = al.api_id
                WHERE gl.status_code >= 400
                ORDER BY gl.requested_at DESC
                LIMIT 20
            """)
            recent_errors = [dict(row) for row in cur.fetchall()]

            return {
                "totalApis": total_apis,
                "totalApiKeys": total_api_keys,
                "totalCalls": total_calls,
                "todayCalls": today_calls,
                "dailyStats": daily_stats,
                "dailyErrors": daily_errors,
                "topApis": top_apis,
                "pendingRequests": pending_requests,
                "recentErrors": recent_errors,
            }

    except Exception as e:
        raise DatabaseError(f"[대시보드 통계 조회 실패] {e}")