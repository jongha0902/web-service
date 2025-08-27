from utils.db_config import get_conn, DatabaseError
from typing import Optional

def get_screen_list_info(screen_name: Optional[str], screen_path: Optional[str], use_yn: Optional[str], page: int, per_page: int) -> dict:
    try:
        with get_conn() as conn:
            base_query = "FROM screens WHERE 1=1"
            filters = []
            params = []

            if screen_name:
                filters.append("screen_name LIKE ?")
                params.append(f"%{screen_name}%")
            if screen_path:
                filters.append("screen_path LIKE ?")
                params.append(f"%{screen_path}%")
            if use_yn in ("Y", "N"):  # ✅ 필터가 주어졌을 때만 적용
                filters.append("use_yn = ?")
                params.append(use_yn)                

            where_clause = " AND ".join(filters)
            if where_clause:
                base_query += " AND " + where_clause

            # total count
            count_sql = f"SELECT COUNT(*) {base_query}"
            total_count = conn.execute(count_sql, params).fetchone()[0]

            # paging
            offset = (page - 1) * per_page
            list_sql = f"SELECT screen_code, screen_name, screen_path, component_name, use_yn, description, create_id, create_date, update_id, update_date {base_query} ORDER BY create_date DESC LIMIT ? OFFSET ?"
            rows = conn.execute(list_sql, params + [per_page, offset]).fetchall()
            items = [dict(row) for row in rows]

            return {"items": items, "total_count": total_count}
    except Exception as e:
        raise DatabaseError("화면 목록 조회 중 오류 발생", e)


def create_screen_info(data: dict, login_id):
    try:

        with get_conn() as conn:
            # ✅ 중복 체크
            existing = conn.execute(
                "SELECT 1 FROM screens WHERE UPPER(screen_code) = UPPER(?)",
                (data["screen_code"],)
            ).fetchone()

            if existing:
                raise DatabaseError(f"이미 존재하는 화면 코드입니다: {data['screen_code']}")

            # ✅ 등록
            conn.execute(
                """
                INSERT INTO screens (
                    screen_code, screen_name, screen_path, component_name, use_yn, description,
                    create_id, create_date, update_id, update_date
                )
                VALUES (UPPER(?), ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, CURRENT_TIMESTAMP)
                """,
                (
                    data["screen_code"],
                    data["screen_name"],
                    data["screen_path"],
                    data["component_name"],
                    data["use_yn"],
                    data.get("description", ""),
                    login_id,
                    login_id
                )
            )
    except Exception as e:
        raise DatabaseError("화면 등록 중 오류 발생", e)


def update_screen_info(screen_code: str, data: dict, login_id) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.execute(
                """
                    UPDATE screens
                    SET screen_name = ?, screen_path = ?, component_name = ?, use_yn = ?, description = ?,
                        update_id = ?, update_date = CURRENT_TIMESTAMP
                    WHERE screen_code = ?
                    """,
                    (
                        data.get("screen_name"),
                        data.get("screen_path"),
                        data.get("component_name"),
                        data.get("use_yn"),
                        data.get("description"),
                        login_id,
                        screen_code
                    )
            )
            return cur.rowcount > 0
    except Exception as e:
        raise DatabaseError("화면 수정 중 오류 발생", e)


def delete_screen_info(screen_code: str) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM screens WHERE screen_code = ?",
                (screen_code,)
            )
            return cur.rowcount > 0
    except Exception as e:
        raise DatabaseError("화면 삭제 중 오류 발생", e)
    
def get_screen_ordered_list_info() -> list[dict]:
    try:
        with get_conn() as conn:
            rows = conn.execute(
                """
                SELECT screen_code, screen_name, screen_path, component_name, menu_order
                FROM screens
                WHERE use_yn = 'Y' AND menu_order IS NOT NULL
                ORDER BY menu_order ASC
                """
            ).fetchall()
            return { "items": [dict(row) for row in rows] }
    except Exception as e:
        raise DatabaseError("화면 순서 목록 조회 중 오류 발생", e)
        
def update_screen_order_info(order_list: list[dict]):
    try:
        with get_conn() as conn:
            # 1. 전체 화면의 menu_order 초기화
            conn.execute("UPDATE screens SET menu_order = NULL")

            # 2. 전송된 항목만 다시 menu_order 지정
            for item in order_list:
                data = item.model_dump()  # Pydantic → dict
                conn.execute(
                    "UPDATE screens SET menu_order = ? WHERE screen_code = ?",
                    (data["menu_order"], data["screen_code"])
                )
    except Exception as e:
        raise DatabaseError("화면 순서 저장 중 오류 발생", e)
    
def get_screens_with_permissions(permission_code: str, search: Optional[str] = None) -> list[dict]:
    try:
        with get_conn() as conn:
            sql = """
                SELECT
                    s.screen_code,
                    s.screen_name,
                    s.screen_path,
                    s.use_yn,
                    CASE WHEN sp.screen_code IS NOT NULL THEN 1 ELSE 0 END AS has_permission
                FROM screens s
                LEFT JOIN screen_permissions sp
                    ON s.screen_code = sp.screen_code
                    AND sp.permission_code = ?
                WHERE s.use_yn = 'Y'
            """
            params = [permission_code]

            if search:
                sql += " AND (s.screen_name LIKE ? OR s.screen_path LIKE ?)"
                params += [f"%{search}%", f"%{search}%"]

            sql += " ORDER BY s.menu_order ASC"
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        raise DatabaseError("화면 권한 목록 조회 중 오류 발생", e)

def save_screen_permissions(permission_code: str, screen_codes: list[str]):
    try:
        with get_conn() as conn:
            # 1. 기존 권한 삭제
            conn.execute(
                "DELETE FROM screen_permissions WHERE permission_code = ?",
                (permission_code,)
            )

            # 2. 새로 insert
            for code in screen_codes:
                conn.execute(
                    "INSERT INTO screen_permissions (permission_code, screen_code) VALUES (?, ?)",
                    (permission_code, code)
                )
    except Exception as e:
        raise DatabaseError("화면 권한 저장 중 오류 발생", e)
    
def get_screen_code_by_path(screen_path: str) -> Optional[str]:
    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT screen_code FROM screens WHERE screen_path = ? AND use_yn = 'Y'",
                (screen_path,)
            ).fetchone()
            return row["screen_code"] if row else None
    except Exception as e:
        raise DatabaseError("화면 코드 조회 중 오류 발생", e)    
    
def get_screen_codes_by_permission_code(permission_code: str) -> list[str]:
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT screen_code FROM screen_permissions WHERE permission_code = ?",
                (permission_code,)
            ).fetchall()
            return [row["screen_code"] for row in rows]
    except Exception as e:
        raise DatabaseError("권한별 접근 가능한 화면 목록 조회 중 오류 발생", e)    
    
def get_screens_with_permissions_by_user(user_id: str) -> list[dict]:
    try:
        with get_conn() as conn:
            # 1. 유저의 permission_code 가져오기
            permission_row = conn.execute(
                "SELECT permission_code FROM users WHERE user_id = ? AND use_yn = 'Y'",
                (user_id,)
            ).fetchone()

            if not permission_row:
                raise DatabaseError("유저의 권한 정보를 찾을 수 없습니다.")

            permission_code = permission_row["permission_code"]

            # 2. 권한별 screen 목록 가져오기
            rows = conn.execute(
                """
                SELECT s.screen_code, s.screen_name, s.screen_path, s.menu_order
                FROM screens s
                INNER JOIN screen_permissions sp ON s.screen_code = sp.screen_code
                WHERE sp.permission_code = ? AND s.use_yn = 'Y'
                ORDER BY s.menu_order ASC
                """,
                (permission_code,)
            ).fetchall()

            return [dict(row) for row in rows]

    except Exception as e:
        raise DatabaseError("유저별 화면 목록 조회 중 오류 발생", e)    
    
def get_screens_with_permissions_by_user(user_id: str) -> list[dict]:
    try:
        with get_conn() as conn:
            # 1. 유저의 permission_code 가져오기
            permission_row = conn.execute(
                "SELECT permission_code FROM users WHERE user_id = ? AND use_yn = 'Y'",
                (user_id,)
            ).fetchone()

            if not permission_row:
                raise DatabaseError("유저의 권한 정보를 찾을 수 없습니다.")

            permission_code = permission_row["permission_code"]

            # 2. 권한별 screen 목록 가져오기
            rows = conn.execute(
                """
                SELECT s.screen_code, s.screen_name, s.screen_path, s.component_name, s.menu_order
                FROM screens s
                INNER JOIN screen_permissions sp ON s.screen_code = sp.screen_code
                WHERE sp.permission_code = ? AND s.use_yn = 'Y'
                ORDER BY s.menu_order ASC
                """,
                (permission_code,)
            ).fetchall()

            items = [dict(row) for row in rows]

            return {"items": items}

    except Exception as e:
        raise DatabaseError("유저별 화면 목록 조회 중 오류 발생", e)    