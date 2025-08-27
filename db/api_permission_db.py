from utils.db_config import get_conn, DatabaseError

def get_user_api_permissions(user_id: str):
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    al.api_id,
                    al.api_name,
                    al.path,
                    al.method,
                    CASE WHEN ap.user_id IS NOT NULL THEN 1 ELSE 0 END AS has_permission
                FROM api_list al
                LEFT JOIN api_permissions ap ON al.api_id = ap.api_id AND ap.user_id = ?
                WHERE al.use_yn = 'Y'
                ORDER BY al.api_id
            """, (user_id,))
            return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    except Exception as e:
        raise DatabaseError(f"[유저 API 권한 조회 실패] {e}")

def save_update_user_api_permissions(user_id: str, api_id_list: list, login_id: str) -> bool:
    try:
        with get_conn() as conn:
            cursor = conn.cursor()

            # 기존 권한 삭제
            cursor.execute("DELETE FROM api_permissions WHERE user_id = ?", (user_id,))

            for api_id in api_id_list:
                # 권한 부여
                cursor.execute("""
                    INSERT INTO api_permissions (api_id, user_id, create_id, update_id)
                    VALUES (?, ?, ?, ?)
                """, (api_id, user_id, login_id, login_id))

                # PENDING 신청이 존재하는 경우만 APPROVED 처리
                cursor.execute("""
                    SELECT request_id FROM api_permission_requests
                    WHERE user_id = ? AND api_id = ? AND status = 'PENDING'
                    ORDER BY request_date DESC
                    LIMIT 1
                """, (user_id, api_id))
                row = cursor.fetchone()
                if row:
                    request_id = row["request_id"] if isinstance(row, dict) else row[0]
                    cursor.execute("""
                        UPDATE api_permission_requests
                        SET status = 'APPROVED',
                            response_date = CURRENT_TIMESTAMP,
                            response_id = ?
                        WHERE request_id = ?
                    """, (login_id, request_id))

            return True
    except Exception as e:
        raise DatabaseError(f"[유저 API 권한 저장 실패] {e}")
    
def has_user_api_permission(user_id: str, method: str, path: str) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.execute("""
                SELECT 1
                FROM api_permissions p
                JOIN api_list l ON p.api_id = l.api_id
                JOIN users u ON p.user_id = u.user_id
                WHERE p.user_id = ?
                AND l.method = ?
                AND l.path = ?
                AND l.use_yn = 'Y'
                AND u.use_yn = 'Y'
                LIMIT 1
            """, (user_id, method.upper(), path))
            return cur.fetchone() is not None
    except Exception as e:
        raise DatabaseError(f"[유저 API 권한 체크 실패] {e}")
    
def get_pending_permission_count() -> int:
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_permission_requests WHERE status = 'PENDING'")
            return cursor.fetchone()[0]
    except Exception as e:
        raise DatabaseError(f"[미처리 권한 신청 건수 조회 실패] {e}")    
    
def get_permission_request_list(user_id=None, method=None, path=None, start_date=None, end_date=None, status=None):
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            query = """
                SELECT
                    pr.request_id,
                    pr.user_id,
                    al.api_id,
                    al.api_name,
                    al.path,
                    al.method,
                    pr.status,
                    pr.request_date,
                    pr.response_id,
                    pr.response_date,
                    pr.memo
                FROM api_permission_requests pr
                JOIN api_list al ON pr.api_id = al.api_id
                WHERE 1=1
            """
            params = []

            if user_id:
                query += " AND pr.user_id LIKE ?"
                params.append(f"%{user_id}%")
            if method:
                query += " AND al.method = ?"
                params.append(method)
            if path:
                query += " AND al.path LIKE ?"
                params.append(f"%{path}%")
            if start_date:
                query += " AND DATE(pr.request_date) >= DATE(?)"
                params.append(start_date)
            if end_date:
                query += " AND DATE(pr.request_date) <= DATE(?)"
                params.append(end_date)
            if status:
                query += " AND pr.status = ?"
                params.append(status)

            query += " ORDER BY pr.request_date DESC"

            cur.execute(query, params)
            rows = cur.fetchall()

            return [dict(zip([col[0] for col in cur.description], row)) for row in rows]

    except Exception as e:
        raise DatabaseError(f"[권한 신청 목록 조회 실패] {e}")

def approve_permission_request(request_id: int, login_id: str):
    try:
        with get_conn() as conn:
            cur = conn.execute("""
                UPDATE api_permission_requests
                SET status = 'APPROVED', response_date = datetime('now'), response_id = ?
                WHERE request_id = ? AND status = 'PENDING'
            """, (login_id, request_id))
            if cur.rowcount == 0:
                raise ValueError("대기 중인 요청이 없습니다.")

            # 해당 API에 대한 권한 부여
            row = conn.execute("SELECT user_id, api_id FROM api_permission_requests WHERE request_id = ?", (request_id,)).fetchone()
            if row:
                conn.execute("""
                    INSERT INTO api_permissions (api_id, user_id, create_id, update_id)
                    VALUES (?, ?, ?, ?)
                """, (row["api_id"], row["user_id"], login_id, login_id))
    except Exception as e:
        raise DatabaseError(f"[권한 승인 실패] {e}")

def reject_permission_request(request_id: int, update_id: str):
    try:
        with get_conn() as conn:
            cur = conn.execute("""
                UPDATE api_permission_requests
                SET status = 'REJECTED', response_date = datetime('now'), response_id = ?
                WHERE request_id = ? AND status = 'PENDING'
            """, (update_id, request_id))
            if cur.rowcount == 0:
                raise ValueError("대기 중인 요청이 없습니다.")
    except Exception as e:
        raise DatabaseError(f"[권한 반려 실패] {e}")

def is_existing_request_id(request_id: int) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "SELECT 1 FROM api_permission_requests WHERE request_id = ?",
                (request_id,)
            )
            return cur.fetchone() is not None
    except Exception as e:
        raise DatabaseError(f"[요청 권한 ID 확인 실패] {e}")
    
def insert_permission_request(user_id: str, api_id: int, reason: str):
    try:
        with get_conn() as conn:
            # 1. 이미 권한이 승인된 경우 차단
            existing_permission = conn.execute("""
                SELECT 1 FROM api_permissions
                WHERE user_id = ? AND api_id = ?
            """, (user_id, api_id)).fetchone()
            if existing_permission:
                raise ValueError("이미 해당 API에 대한 권한이 승인되어 있습니다.")

            # 2. 이미 PENDING 상태의 신청이 있는 경우 차단
            existing_request = conn.execute("""
                SELECT 1 FROM api_permission_requests
                WHERE user_id = ? AND api_id = ? AND status = 'PENDING'
            """, (user_id, api_id)).fetchone()
            if existing_request:
                raise ValueError("이미 해당 API에 대한 신청이 진행 중입니다.")

            # 3. 새 신청 등록
            conn.execute("""
                INSERT INTO api_permission_requests (user_id, api_id, memo)
                VALUES (?, ?, ?)
            """, (user_id, api_id, reason))

    except Exception as e:
        raise DatabaseError(f"[API 권한 신청 실패] {e}")
    
def get_user_all_api_permissions(user_id: str):
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    al.api_id,
                    al.api_name,
                    al.path,
                    al.description,
                    al.method,
                    CASE WHEN ap.user_id IS NOT NULL THEN 1 ELSE 0 END AS has_permission,
                    CASE 
                        WHEN ap.user_id IS NULL THEN (
                            SELECT 
                                CASE 
                                    WHEN pr.status = 'APPROVED' THEN 'return'
                                    ELSE pr.status
                                END
                            FROM api_permission_requests pr
                            WHERE pr.user_id = ?
                            AND pr.api_id = al.api_id
                            ORDER BY pr.request_date DESC
                            LIMIT 1
                        )
                        ELSE NULL
                    END AS request_status
                FROM api_list al
                LEFT JOIN api_permissions ap ON al.api_id = ap.api_id AND ap.user_id = ?
                WHERE al.use_yn = 'Y'
                ORDER BY al.api_id;
            """, (user_id, user_id))
            return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    except Exception as e:
        raise DatabaseError(f"[유저 전체 API 권한 + 상태 조회 실패] {e}")