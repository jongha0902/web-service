from utils.db_config import get_conn, DatabaseError
from typing import Optional

def get_user_permission_types(
    search: Optional[str],
    search_field: Optional[str],
    use_yn: Optional[str]
):
    try:
        with get_conn() as conn:
            query = "SELECT * FROM user_permission_types WHERE 1=1"
            params = []
            if use_yn:
                query += " AND use_yn = ?"
                params.append(use_yn)
            if search and search_field:
                query += f" AND {search_field} LIKE ?"
                params.append(f"%{search}%")
            rows = conn.execute(query, tuple(params)).fetchall()
            return {"items": [dict(row) for row in rows]}
    except Exception as e:
        raise DatabaseError("권한 목록 조회 중 오류 발생", e)


def create_user_permission_type(data: dict, login_id: str):
    try:
        with get_conn() as conn:
            existing = conn.execute("SELECT 1 FROM user_permission_types WHERE UPPER(permission_code) = UPPER(?)", (data["permission_code"],)).fetchone()
            if existing:
                raise DatabaseError(f"이미 존재하는 권한 코드입니다: {data['permission_code']}")
            conn.execute("""
                INSERT INTO user_permission_types (
                    permission_code, permission_name, use_yn, description,
                    create_id, create_date, update_id, update_date
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, CURRENT_TIMESTAMP)
            """, (
                data["permission_code"].upper(),
                data["permission_name"],
                data["use_yn"],
                data.get("description", ""),
                login_id,
                login_id
            ))
    except Exception as e:
        raise DatabaseError("권한 등록 중 오류 발생", e)

def update_user_permission_type(permission_code: str, data: dict, login_id: str) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.execute("""
                UPDATE user_permission_types
                SET permission_name = ?, use_yn = ?, description = ?, update_id = ?, update_date = CURRENT_TIMESTAMP
                WHERE permission_code = ?
            """, (
                data["permission_name"],
                data["use_yn"],
                data.get("description", ""),
                login_id,
                permission_code
            ))
            return cur.rowcount > 0
    except Exception as e:
        raise DatabaseError("권한 수정 중 오류 발생", e)

def delete_user_permission_type(permission_code: str) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.execute("DELETE FROM user_permission_types WHERE permission_code = ?", (permission_code,))
            return cur.rowcount > 0
    except Exception as e:
        raise DatabaseError("권한 삭제 중 오류 발생", e)

def get_users_with_user_permission_type(permission_code: str, user_id=None, user_name=None):
    try:
        with get_conn() as conn:
            query = """
                SELECT u.user_id, u.user_name, u.use_yn
                FROM users u
                JOIN user_permission_types up ON u.permission_code = up.permission_code
                WHERE up.permission_code = ?
            """
            params = [permission_code]
            if user_id:
                query += " AND u.user_id LIKE ?"
                params.append(f"%{user_id}%")
            if user_name:
                query += " AND u.user_name LIKE ?"
                params.append(f"%{user_name}%")
            query += " ORDER BY u.user_id ASC"

            rows = conn.execute(query, tuple(params)).fetchall()
            return {"items": [dict(row) for row in rows], "total_count": len(rows)}
    except Exception as e:
        raise DatabaseError("유저 권한 조회 중 오류 발생", e)

