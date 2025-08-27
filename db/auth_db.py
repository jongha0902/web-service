from utils.db_config import get_conn, DatabaseError
from utils.common import password_hash_key
from typing import Optional

def authenticate_user(user_id, password) -> Optional[dict]:
    try:
        password_hashed_key = password_hash_key(password)
        with get_conn() as conn:
            cur = conn.execute("""
                SELECT 
                    u.user_id, 
                    u.user_name, 
                    u.use_yn,
                    CASE WHEN k.api_key IS NOT NULL THEN TRUE ELSE FALSE END AS has_api_key
                FROM users u
                LEFT JOIN api_keys k ON u.user_id = k.user_id
                WHERE u.user_id = ? AND u.password = ?
            """, (user_id, password_hashed_key))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        raise DatabaseError(f"[로그인 인증 실패] {e}")


def update_refresh_token(user_id: str, refresh_token: str):
    try:
        with get_conn() as conn:
            conn.execute(
                "UPDATE users SET refresh_token = ? WHERE user_id = ?",
                (refresh_token, user_id)
            )
            conn.commit()
    except Exception as e:
        raise DatabaseError(f"[Refresh Token 업데이트 실패] {e}")


def get_refresh_token(user_id: str) -> Optional[str]:
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "SELECT refresh_token FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = cur.fetchone()
            return row[0] if row else None
    except Exception as e:
        raise DatabaseError(f"[Refresh Token 조회 실패] {e}")


def clear_refresh_token(user_id: str):
    try:
        with get_conn() as conn:
            conn.execute(
                "UPDATE users SET refresh_token = NULL WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
    except Exception as e:
        raise DatabaseError(f"[Refresh Token 삭제 실패] {e}")
     