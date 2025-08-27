from utils.db_config import get_conn, DatabaseError
from utils.common import password_hash_key
from typing import Optional
import math


def authenticate_user(user_id, password) -> Optional[dict]:
    try:
        password_hashed_key = password_hash_key(password)
        with get_conn() as conn:
            cur = conn.execute("""
                SELECT 
                    u.user_id, 
                    u.user_name, 
                    u.permission_code,
                    upt.permission_name,
                    CASE WHEN k.api_key IS NOT NULL THEN TRUE ELSE FALSE END AS has_api_key
                FROM users u
                LEFT JOIN user_permission_types upt ON u.permission_code = upt.permission_code
                LEFT JOIN api_keys k ON u.user_id = k.user_id
                WHERE u.user_id = ? AND u.password = ?
            """, (user_id, password_hashed_key))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        raise DatabaseError(f"[로그인 인증 실패] {e}")

    
def get_user_list(page=1, per_page=15, user_id=None, user_name=None, use_yn=None):
    try:
        with get_conn() as conn:
            cur = conn.cursor()

            # 공통 조건문 작성
            where_clauses = []
            params = []
            if user_id:
                where_clauses.append("u.user_id LIKE ?")
                params.append(f"%{user_id}%")
            if user_name:
                where_clauses.append("u.user_name LIKE ?")
                params.append(f"%{user_name}%")
            if use_yn:
                where_clauses.append("u.use_yn = ?")
                params.append(use_yn)

            where_sql = " AND ".join(where_clauses)
            if where_sql:
                where_sql = " AND " + where_sql

            # 목록 조회
            query = f"""
                SELECT 
                    u.*, 
                    upt.permission_name 
                FROM users u
                LEFT JOIN user_permission_types upt ON u.permission_code = upt.permission_code
                WHERE 1=1
                {where_sql}
                ORDER BY u.create_date DESC
                LIMIT ? OFFSET ?
            """
            cur.execute(query, params + [per_page, (page - 1) * per_page])
            rows = cur.fetchall()

            # 총 개수 조회
            count_query = f"""
                SELECT COUNT(*) 
                FROM users u
                LEFT JOIN user_permission_types upt ON u.permission_code = upt.permission_code
                WHERE 1=1
                {where_sql}
            """
            cur.execute(count_query, params)
            total_count = cur.fetchone()[0]

            return {
                "items": [dict(row) for row in rows],
                "total_count": total_count,
                "total_pages": math.ceil(total_count / per_page)
            }

    except Exception as e:
        raise DatabaseError(f"[사용자 목록 조회 실패] {e}")


    
def insert_user(user: dict):
    try:
        password_hashed_key = password_hash_key(user["password"])
        with get_conn() as conn:
            # 1. 사용자 등록
            conn.execute("""
                INSERT INTO users (user_id, password, user_name, permission_code, use_yn, create_id, create_date, update_id, update_date)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), ?, datetime('now', 'localtime'))
            """, (
                user["user_id"], password_hashed_key, user["user_name"], user["permission_code"],
                user["use_yn"], user["login_id"], user["login_id"]
            ))

    except Exception as e:
        raise DatabaseError(f"[사용자 등록 실패] {e}")

def update_user_info(user: dict):
    try:
        with get_conn() as conn:
            cur = conn.execute("""
                UPDATE users
                SET user_name = ?, update_id = ?, update_date = CURRENT_TIMESTAMP, permission_code = ?, use_yn = ?
                WHERE user_id = ?
            """, (user["user_name"], user["login_id"], user["permission_code"], user["use_yn"], user["user_id"]))
            return cur.rowcount > 0
    except Exception as e:
        raise DatabaseError(f"[사용자 정보 수정 실패] {e}")

def update_user_password(user_id: str, new_password: str, updater_id: str) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.execute("""
                UPDATE users
                SET password = ?, update_id = ?, update_date = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (password_hash_key(new_password), updater_id, user_id))
            return cur.rowcount > 0
    except Exception as e:
        raise DatabaseError(f"[비밀번호 변경 실패] {e}")
    
def delete_user_overall_logic(user_id: str):
    try:
        with get_conn() as conn:
            # 유저 삭제
            cur1 = conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            if cur1.rowcount == 0:
                raise ValueError(f"삭제하신 유저ID({user_id})는 존재하지 않습니다.")

            # API Key 삭제
            conn.execute("DELETE FROM api_keys WHERE user_id = ?", (user_id,))

            # 권한 삭제
            conn.execute("DELETE FROM api_permissions WHERE user_id = ?", (user_id,))
            
    except Exception as e:
        raise DatabaseError(f"[유저, API-Key, API 권한 삭제 실패] {e}")    
    
def is_active_user_id(user_id: str) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.execute("SELECT 1 FROM users WHERE user_id = ? AND use_yn = 'Y' LIMIT 1", (user_id,))
            return cur.fetchone() is not None
    except Exception as e:
        raise DatabaseError(f"[유저 활성 상태 확인 실패] {e}")    

def is_existing_user_id(user_id) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            return cur.fetchone() is not None
    except Exception as e:
        raise DatabaseError(f"[사용자 존재 여부 확인 실패] {e}")    

def get_user_info(user_id: str) -> Optional[dict]:
    try:
        with get_conn() as conn:
            cur = conn.execute("""
                SELECT 
                    u.user_id, 
                    u.user_name, 
                    u.permission_code, 
                    u.use_yn, 
                    u.create_id, 
                    u.create_date, 
                    u.update_id, 
                    u.update_date,
                    CASE WHEN k.api_key IS NOT NULL THEN TRUE ELSE FALSE END AS has_api_key
                FROM users u
                LEFT JOIN api_keys k ON u.user_id = k.user_id
                WHERE u.user_id = ?
            """, (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        raise DatabaseError(f"[유저 정보 조회 실패] {e}")    