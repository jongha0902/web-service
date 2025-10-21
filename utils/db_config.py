import sqlite3
from contextlib import contextmanager
from utils.config import Config

DB_PATH = Config.DB_PATH

class DatabaseError(Exception):
    pass

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise DatabaseError(f"[DB 오류] {e}")
    finally:
        conn.close()


async def init_db():
    try:
        with get_conn() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS api_list (
                    api_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    method TEXT NOT NULL,
                    use_yn TEXT NOT NULL DEFAULT 'Y',
                    description TEXT,
                    flow_data TEXT,
                    write_id TEXT,
                    write_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    update_id TEXT,
                    update_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS api_permissions (
                    api_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    create_id TEXT,
                    create_date TEXT DEFAULT (datetime('now')),
                    update_id TEXT,
                    update_date TEXT DEFAULT (datetime('now')),
                    CONSTRAINT API_PERMISSIONS_PK PRIMARY KEY (api_id,user_id)
                );

                CREATE TABLE IF NOT EXISTS api_permission_requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    api_id INTEGER NOT NULL,
                    status TEXT DEFAULT ('PENDING'),
                    memo TEXT CHECK (length(memo) <= 255),
                    request_date TEXT DEFAULT (datetime('now', 'localtime')),
                    response_date TEXT,
                    response_id TEXT
                );

                CREATE TABLE IF NOT EXISTS api_keys (
                    user_id TEXT PRIMARY KEY,
                    api_key TEXT UNIQUE NOT NULL,
                    comment TEXT,
                    generate_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    generate_id TEXT,
                    regenerate_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    regenerate_id TEXT
                );

                CREATE TABLE IF NOT EXISTS api_usage_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    path TEXT NOT NULL,
                    method TEXT NOT NULL,
                    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    request_data TEXT,
                    response_data TEXT,
                    status_code INTEGER
                );
                CREATE INDEX IF NOT EXISTS api_usage_log_path_IDX ON api_usage_log (path,user_id,method,request_time);

                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    permission_code TEXT DEFAULT 'user',
                    use_yn TEXT DEFAULT 'Y',
                    create_id TEXT,
                    create_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    update_id TEXT,
                    update_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    refresh_token TEXT
                );
                               
                CREATE TABLE IF NOT EXISTS screens (
                    screen_code TEXT PRIMARY KEY,
                    screen_name TEXT NOT NULL,
                    screen_path TEXT NOT NULL,
                    component_name TEXT NOT NULL,
                    use_yn TEXT(1) DEFAULT ('N') NOT NULL,
                    description TEXT,
                    create_id TEXT,
                    create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    update_id TEXT,
                    update_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    menu_order INTEGER DEFAULT NULL
                );
                               
                CREATE TABLE IF NOT EXISTS permission_screen_map (
                    permission_code TEXT,
                    screen_code TEXT,
                    create_id TEXT,
                    create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (permission_code, screen_code)
                );
                               
                CREATE TABLE IF NOT EXISTS user_permission_types (
                    permission_code VARCHAR(50) PRIMARY KEY,
                    permission_name VARCHAR(100) NOT NULL,
                    use_yn CHAR(1) DEFAULT 'Y' CHECK (use_yn IN ('Y', 'N')),
                    description TEXT,
                    create_id TEXT,
                    create_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    update_id TEXT,
                    update_date DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                               
                CREATE TABLE IF NOT EXISTS gateway_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,                -- 요청자 ID (API 키 인증 결과)
                    api_id TEXT,                 -- 호출된 API 코드 (ex. "RAG", "BID_INFO")
                    method TEXT NOT NULL,        -- HTTP 메서드 (GET, POST 등)
                    path TEXT NOT NULL,          -- 실제 호출된 경로 (ex. /rag, /bid-info)
                    query_param TEXT,            -- Query string (key=value&key2=value2 ...)
                    headers TEXT,                -- 요청 헤더 (JSON 직렬화)
                    body TEXT,                   -- 요청 바디 (JSON 또는 raw string)
                    status_code INTEGER,         -- 응답 상태 코드 (200, 403 등)
                    response TEXT,               -- 응답 내용 (JSON 직렬화 또는 에러 메시지)
                    requested_at TIMESTAMP NOT NULL,  -- 요청 시간 (ISO timestamp)
                    responded_at TIMESTAMP NOT NULL,  -- 응답 시간 (ISO timestamp)
                    latency_ms INTEGER,          -- 요청~응답 간 지연 시간(ms)
                    client_ip TEXT,              -- 클라이언트 IP
                    user_agent TEXT,             -- User-Agent 헤더
                    is_success TEXT NOT NULL,    -- 'Y' (성공), 'N' (실패)
                    error_message TEXT           -- 에러 메시지 (예외 발생 시)
                );

            ''')
    except Exception as e:
        raise DatabaseError(f"[DB 초기화 실패] {e}")        
