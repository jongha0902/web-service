import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    DB_PATH = os.getenv("DB_PATH", "C:/sqlite3/ets_api.db")
    API_SALT = os.getenv("API_SALT", "ets-ai-secret-api-salt")
    PASSWORD_SALT = os.getenv("PASSWORD_SALT", "ets-ai-secret-password-salt")
    JWT_SECRET = os.getenv("JWT_SECRET", "ets-ai-jwt-secret")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)
    TOKEN_REFRESH_THRESHOLD_SECONDS = os.getenv("TOKEN_REFRESH_THRESHOLD_SECONDS", 10 * 60)  # 10분