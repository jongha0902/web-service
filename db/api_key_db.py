from utils.db_config import get_conn, DatabaseError
from utils.common import api_hash_key
import math
import secrets
    
def is_api_key_existing_id(user_id) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.execute("SELECT 1 FROM api_keys WHERE user_id = ?", (user_id,))
            return cur.fetchone() is not None
    except Exception as e:
        raise DatabaseError(f"[API Key 존재 여부 확인 실패] {e}")    

# ✅ 유효한 API 키인지 확인하고 사용자 ID 반환
def is_valid_api_key(user_id, key) -> bool:
    try:
        hashed_key = api_hash_key(key)
        with get_conn() as conn:
            cur = conn.execute("SELECT 1 FROM api_keys WHERE user_id = ? AND api_key = ?", (user_id, hashed_key))
            return cur.fetchone() is not None
    except Exception as e:
        raise DatabaseError(f"[API Key 유효성 검사 실패] {e}")

def get_user_id_by_api_key(api_key: str) -> str | None:
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.user_id
                FROM api_keys k
                JOIN users u ON k.user_id = u.user_id
                WHERE k.api_key = ?
                  AND u.use_yn = 'Y'
                LIMIT 1
            """, (api_key,))
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        raise DatabaseError(f"[API Key → user_id 조회 실패] {e}")

# ✅ API 키 생성
def insert_api_key(user_id, key, comment, login_id):
    try:
        hashed_key = api_hash_key(key)
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO api_keys (user_id, api_key, comment, generate_date, generate_id, regenerate_date, regenerate_id)
                VALUES (?, ?, ?, datetime('now', 'localtime'), ?, datetime('now', 'localtime'), ? )
            """, (user_id, hashed_key, comment, login_id, login_id))
    except Exception as e:
        raise DatabaseError(f"[API Key 생성 실패] {e}")

# ✅ API 키 코멘트 수정
def update_api_key_comment(user_id, comment, login_id):
    try:
        with get_conn() as conn:
            cur = conn.execute("""
                UPDATE api_keys
                SET comment = ?, regenerate_date = datetime('now', 'localtime'), regenerate_id = ?
                WHERE user_id = ?
            """, (comment, login_id, user_id))
            if cur.rowcount == 0:
                raise ValueError("업데이트 실패: 해당 user_id 없음")
    except Exception as e:
        raise DatabaseError(f"[API Key 코멘트 수정 실패] {e}")

# ✅ API 키 재발급
def regenerate_api_key(user_id, login_id) -> tuple[str, str]:
    try:
        new_key = f"ets-{secrets.token_hex(16)}"
        hashed_key = api_hash_key(new_key)
        with get_conn() as conn:
            cur = conn.execute("SELECT comment FROM api_keys WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError("해당 ID가 존재하지 않습니다.")
            comment = row[0]
            conn.execute("""
                UPDATE api_keys
                SET api_key = ?, regenerate_date = CURRENT_TIMESTAMP, regenerate_id = ?
                WHERE user_id = ?
            """, (hashed_key, login_id, user_id))
        return new_key, comment
    except Exception as e:
        raise DatabaseError(f"[API Key 재발급 실패] {e}")

# ✅ API 키 삭제
def delete_api_key(user_id) -> bool:
    try:
        with get_conn() as conn:
            cur = conn.execute("DELETE FROM api_keys WHERE user_id = ?", (user_id,))
            return cur.rowcount > 0
    except Exception as e:
        raise DatabaseError(f"[API Key 삭제 실패] {e}")

# ✅ API 키 목록 조회
def get_api_key_list(page, per_page, user_id=None, comment=None):
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            query = """
                SELECT 
                    ak.user_id,
                    u.user_name,
                    ak.api_key,
                    ak.comment,
                    ak.generate_date,
                    ak.generate_id,
                    ak.regenerate_date,
                    ak.regenerate_id
                FROM api_keys ak
                INNER JOIN users u ON ak.user_id = u.user_id
                WHERE 1=1
                  AND u.use_yn = 'Y'
            """
            params = []
            if user_id:
                query += " AND ak.user_id LIKE ?"
                params.append(f"%{user_id}%")
            if comment:
                query += " AND ak.comment LIKE ?"
                params.append(f"%{comment}%")
            query += " ORDER BY ak.generate_date DESC LIMIT ? OFFSET ?"
            params.extend([per_page, (page - 1) * per_page])
            cur.execute(query, params)
            rows = cur.fetchall()

            count_query = """
                SELECT COUNT(*) FROM api_keys ak
                INNER JOIN users u ON ak.user_id = u.user_id
                WHERE 1=1
            """
            count_params = []
            if user_id:
                count_query += " AND ak.user_id LIKE ?"
                count_params.append(f"%{user_id}%")
            if comment:
                count_query += " AND ak.comment LIKE ?"
                count_params.append(f"%{comment}%")
            cur.execute(count_query, count_params)
            total_count = cur.fetchone()[0]
            total_pages = math.ceil(total_count / per_page)

            return {
                "items": [dict(row) for row in rows],
                "total_pages": total_pages,
                "total_count": total_count
            }
    except Exception as e:
        raise DatabaseError(f"[API Key 목록 조회 실패] {e}")
